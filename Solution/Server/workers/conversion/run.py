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

# The Shared Baton
LOCK_PATH = os.path.join(server_dir, "worker_processing.lock")
lock = FileLock(LOCK_PATH, timeout=0)

def run_worker():
    print("Initializing Conversion Worker...")
    app = create_app()
    converter = Converter(server_dir)

    with app.app_context():
        print("Worker successfully connected to the database. Starting polling loop...")
        
        while True:
            try:
                # Zombie Sweeper (Crash Recovery)
                timeout_threshold = datetime.now(timezone.utc) - timedelta(minutes=30)
                
                stale_sessions = MarkingSession.query.filter(
                    MarkingSession.stage == "Conversion Processing",
                    MarkingSession.updated_at < timeout_threshold
                ).all()

                if stale_sessions:
                    print(f"\nFound {len(stale_sessions)} crashed sessions. Reverting to Pending...")
                    for session in stale_sessions:
                        session.stage = "Conversion Pending"
                    db.session.commit()

                # Database Check (Fast-Fail)
                if MarkingSession.query.filter_by(stage="Evaluation Processing").first():
                    print("Evaluation in progress (DB check). Pausing Conversion...", end="\n")
                    time.sleep(5)
                    continue

                # Atomic File Lock (Race Condition Prevention)
                with lock:    
                    top_sessions = MarkingSession.query \
                        .options(
                            selectinload(MarkingSession.markschemes).selectinload(MarkScheme.file),
                            selectinload(MarkingSession.student_submissions)
                            .selectinload(StudentSubmission.pages)
                            .selectinload(SubmissionPage.file)
                        ) \
                        .filter(MarkingSession.stage != "Evaluated") \
                        .order_by(MarkingSession.created_at.asc()) \
                        .limit(3) \
                        .all()

                    # Filter out ONLY the sessions this specific worker needs to handle
                    sessions_to_process = [s for s in top_sessions if s.stage == "Conversion Pending"]

                    if sessions_to_process:
                        print(f"\nFound {len(sessions_to_process)} sessions in this batch.")
                        
                        # LOAD THE LLM
                        print("LOADING LLM INTO MEMORY...")
                        converter.load_models()
                        
                        for session in sessions_to_process:
                            print(f"\n-> Converting Session ID: {session.id}")
                            
                            session.stage = "Conversion Processing"
                            db.session.commit()

                            all_items_converted = True
                            
                            # PROCESS MARKSCHEMES
                            for ms in session.markschemes:
                                if ms.contents and ms.contents.strip():
                                    print(f"-> Skipping Markscheme {ms.id} (already has contents)")
                                    continue

                                if ms.file and getattr(ms.file, 'storage_url', None):
                                    print(f"-> Converting Markscheme: {ms.id}")
                                    text = converter.convert(ms.file.storage_url)

                                    if text:
                                        ms.contents = text
                                        db.session.commit()
                                    else:
                                        all_items_converted = False
                                else:
                                    all_items_converted = False

                            # PROCESS STUDENT SUBMISSIONS (Stitch pages)
                            for submission in session.student_submissions:
                                if submission.contents and submission.contents.strip():
                                    print(f"-> Skipping Student {submission.student_no} (already has contents)")
                                    continue

                                print(f"-> Processing Student No: {submission.student_no}")
                                
                                submission_texts = []
                                sorted_pages = sorted(submission.pages, key=lambda p: getattr(p, 'page_no', 0))
                                
                                current_submission_success = True
                                for page in sorted_pages:
                                    if page.file and getattr(page.file, 'storage_url', None):
                                        print(f"-> Converting Page {getattr(page, 'page_no', '?')}")
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
                                    db.session.commit() # Commit each student as they are done
                                else:
                                    all_items_converted = False

                            #MOVE TO NEXT STAGE
                            if all_items_converted:
                                print(f"-> All items for session {session.id} converted. Moving to Evaluation Pending.")
                                session.stage = "Evaluation Pending"
                                db.session.commit()
                            else:
                                print(f"-> Session {session.id} still has pending items. Remaining in Conversion Processing.")

                        # UNLOAD THE LLM AND PURGE MEMORY
                        converter.unload_models()
                    else:
                        print("No Conversion Pending sessions in top 3. Passing the baton...", end="\n")

                # Force SQLAlchemy to fetch fresh data next loop
                db.session.commit()
                
                # Wait for lock until checking again
                time.sleep(5)

            except Timeout:
                # This catches the millisecond race condition if the DB check missed it
                print("Evaluation grabbed the lock first. Waiting my turn...", end="\n")
                time.sleep(5)
                
            except Exception as e:
                print(f"\nAn error occurred while polling: {e}")
                db.session.rollback()
                time.sleep(5)

if __name__ == "__main__":
    run_worker()