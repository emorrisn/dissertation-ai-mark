import sys
import os
import time
from datetime import datetime, timedelta, timezone
from filelock import FileLock, Timeout

current_dir = os.path.dirname(os.path.abspath(__file__))
server_dir = os.path.abspath(os.path.join(current_dir, '../../'))
sys.path.append(server_dir)

from api import create_app
from api.extensions import db
from sqlalchemy.orm import selectinload
from api.models import MarkingSession, MarkScheme, StudentSubmission, SubmissionPage 

from convert import Converter
import logging

# The Shared Baton
LOCK_PATH = os.path.join(server_dir, "worker_processing.lock")
lock = FileLock(LOCK_PATH, timeout=0)
logging.basicConfig(
    level=logging.INFO, 
    format='[%(levelname)s] [%(asctime)s] %(message)s', 
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


def recover_stale_sessions():
    """Finds sessions that crashed mid-conversion and resets them."""
    timeout_threshold = datetime.now(timezone.utc) - timedelta(minutes=30)
    stale_sessions = MarkingSession.query.filter(
        MarkingSession.stage == "Conversion Processing",
        MarkingSession.status.in_(["processing", "error"]),
        MarkingSession.updated_at < timeout_threshold
    ).all()

    if stale_sessions:
        logger.info(f"Found {len(stale_sessions)} crashed sessions. Reverting to Pending...")
        for session in stale_sessions:
            session.stage = "Conversion Pending"
            session.status = "pending"
        db.session.commit()

def fetch_pending_sessions():
    """Fetches and locks the top 3 sessions that are ready for conversion."""
    top_sessions = MarkingSession.query \
        .options(
            selectinload(MarkingSession.markschemes).selectinload(MarkScheme.file),
            selectinload(MarkingSession.student_submissions)
            .selectinload(StudentSubmission.pages)
            .selectinload(SubmissionPage.file)
        ) \
        .filter(
            MarkingSession.stage != "Evaluated",
            MarkingSession.status == "pending"
        ) \
        .order_by(MarkingSession.created_at.asc()) \
        .limit(3) \
        .all()
        
    return [s for s in top_sessions if s.stage == "Conversion Pending"]


def process_markschemes(session, converter):
    """Converts markschemes to text"""
    all_converted = True
    for ms in session.markschemes:
        if ms.contents and ms.contents.strip():
            logger.info(f"Skipping Markscheme {ms.id}")
            continue

        if ms.file and getattr(ms.file, 'storage_url', None):
            logger.info(f"Converting Markscheme: {ms.id}")
            text = converter.convert(ms.file.storage_url)

            if text:
                ms.contents = text
                db.session.commit()
            else:
                all_converted = False
        else:
            all_converted = False
            
    return all_converted

def process_student_submissions(session, converter):
    """Converts and stitches student submission pages."""
    all_converted = True
    for submission in session.student_submissions:
        if submission.contents and submission.contents.strip():
            logger.info(f"Skipping Student {submission.student_no}")
            continue

        logger.info(f"Processing Student No: {submission.student_no}")
        
        submission_texts = []
        sorted_pages = sorted(submission.pages, key=lambda p: getattr(p, 'page_no', 0))
        
        current_submission_success = True
        for page in sorted_pages:
            if page.file and getattr(page.file, 'storage_url', None):
                logger.info(f"Converting Page {getattr(page, 'page_no', '?')}")
                page_text = converter.convert(page.file.storage_url)
                
                if page_text:
                    submission_texts.append(page_text)
                else:
                    current_submission_success = False
            else:
                current_submission_success = False
        
        # Stitch all pages together with a double newline
        if current_submission_success and submission_texts:
            submission.contents = "\n\n".join(submission_texts)
            db.session.commit()
        else:
            all_converted = False
            
    return all_converted

def run_worker():
    logger.info("Initializing Conversion Worker...")
    app = create_app()
    converter = Converter(server_dir)

    with app.app_context():
        logger.info("Worker successfully connected to the database. Starting polling loop...")

        is_waiting_logged = False
        while True:
            try:
                recover_stale_sessions()

                # Database Check (Fast-Fail)
                if MarkingSession.query.filter_by(stage="Evaluation Processing").first():
                    logger.info("Evaluation in progress (DB check). Pausing Conversion...")
                    time.sleep(5)
                    continue

                # Atomic File Lock (Race Condition Prevention)
                with lock:    
                    sessions_to_process = fetch_pending_sessions()

                    if sessions_to_process:
                        is_waiting_logged = False
                        logger.info(f"Found {len(sessions_to_process)} sessions in this batch.")
                        
                        # LOAD THE LLM
                        converter.load_models()
                        
                        for session in sessions_to_process:
                            logger.info(f"Converting Session ID: {session.id}")
                            
                            session.stage = "Conversion Processing"
                            session.status = "processing"
                            db.session.commit()
                            
                            # PROCESS MARKSCHEMES
                            ms_success = process_markschemes(session, converter)
                            sub_success = process_student_submissions(session, converter)

                            #MOVE TO NEXT STAGE
                            if ms_success and sub_success:
                                logger.info(f"All items for session {session.id} converted. Moving to Evaluation Pending.")
                                session.stage = "Evaluation Pending"
                            else:
                                logger.info(f"Session {session.id} still has pending items. Remaining in Conversion Processing.")
                                session.status = "error"
                        
                            db.session.commit()

                        converter.unload_models()
                    else:
                        if not is_waiting_logged:
                            logger.info("No Conversion Pending sessions in top 3. Passing the baton...")
                            # Toggle the flag so we don't print it again on the next 5-second loop
                            is_waiting_logged = True

                # Force SQLAlchemy to fetch fresh data next loop
                db.session.commit()
                
                # Wait for lock until checking again
                time.sleep(5)

            # This catches the millisecond race condition if the DB check missed it
            except Timeout:
                logger.info("Evaluation grabbed the lock first. Waiting my turn...")
                time.sleep(5)
                
            except Exception as e:
                logger.info(f"An error occurred while polling: {e}")
                db.session.rollback()
                time.sleep(5)

if __name__ == "__main__":
    run_worker()