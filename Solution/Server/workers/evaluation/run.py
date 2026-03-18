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
from api.models import MarkingSession, StudentSubmission, MarkingFeedbackItem, MarkingFeedback, User, UserUpdate
from sqlalchemy.orm import selectinload

import logging
from evaluate import Evaluator 

# The Shared Baton (Must be the EXACT same path as the conversion script)
LOCK_PATH = os.path.join(server_dir, "worker_processing.lock")
lock = FileLock(LOCK_PATH, timeout=0)

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] [%(asctime)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

def recover_stale_sessions():
    timeout_threshold = datetime.now(timezone.utc) - timedelta(minutes=45) # Evaluation takes longer, give it 45 mins
    stale_sessions = MarkingSession.query.filter(
        MarkingSession.stage == "Evaluation Processing",
        MarkingSession.status.in_(["processing", "error"]),
        MarkingSession.updated_at < timeout_threshold
    ).all()

    if stale_sessions:
        logger.info(f"Found {len(stale_sessions)} crashed sessions. Reverting to Pending...")
        for session in stale_sessions:
            session.stage = "Evaluation Pending"
            session.status = "processing"
        db.session.commit()

def fetch_pending_sessions():
    top_sessions = MarkingSession.query \
        .options(
            selectinload(MarkingSession.user),
            selectinload(MarkingSession.markschemes),
            selectinload(MarkingSession.student_submissions).selectinload(StudentSubmission.feedback)
        ) \
        .filter(MarkingSession.stage == "Evaluation Pending", MarkingSession.status == "processing") \
        .order_by(MarkingSession.created_at.asc()) \
        .limit(3) \
        .all()
    return top_sessions

def compile_markschemes(session) -> str:
    """Stitches all markscheme texts into a single string."""
    texts = [ms.contents for ms in session.markschemes if ms.contents]
    return "\n\n---\n\n".join(texts)

def process_evaluations(session, evaluator):
    """Processes all students in a session and creates DB records."""
    markscheme_text = compile_markschemes(session)
    
    required_outputs = getattr(session, 'required_outputs', []) 
    if not required_outputs:
        required_outputs = ["Give Feedback", "Score Work"]

    if session.user and getattr(session.user, 'writing_style', None):
        writing_styles = session.user.writing_style
    else:
        writing_styles = ["Balanced"]

    all_students_evaluated = True

    for student in session.student_submissions:
        # TWEAK 1: Check the length of the list just in case it's an empty list object
        if student.feedback and len(student.feedback) > 0:
            logger.info(f"Skipping Student {student.student_no} (Already evaluated)")
            continue

        if not student.contents:
            logger.warning(f"Student {student.student_no} has no text! Skipping.")
            all_students_evaluated = False
            continue

        logger.info(f"Evaluating Student {student.student_no}...")
        
        # Call the Orchestrator
        feedback_variations = evaluator.evaluate(
            student_text=student.contents, 
            markscheme_text=markscheme_text, 
            required_outputs=required_outputs,
            writing_styles=writing_styles
        )

        if not isinstance(feedback_variations, list) or len(feedback_variations) == 0:
            logger.error(f"Failed to generate valid feedback for Student {student.student_no}.")
            all_students_evaluated = False
            continue

        # Map the JSON to the Database Models
        for var_data in feedback_variations:
            new_feedback = MarkingFeedback(
                submission_id=student.id,
                student_no=student.student_no,
                description=var_data.get("description", "AI Evaluation"),
                confidence=float(var_data.get("confidence", 0.8)), # Default to 0.8 just in case
                teacher_comments=""
            )
            db.session.add(new_feedback)
            db.session.flush()

            items_list = var_data.get("items", [])
            for item_obj in items_list:
                # TWEAK 2: Ensure item_obj is actually a dictionary before calling .get()
                if isinstance(item_obj, dict):
                    output_type = item_obj.get("type")
                    content_text = item_obj.get("content")

                    if output_type and content_text:
                        new_item = MarkingFeedbackItem(
                            feedback_id=new_feedback.id,
                            type=output_type,
                            contents=str(content_text)
                        )
                        db.session.add(new_item)

        # Commit per student so work isn't lost if the next one fails
        try:
            db.session.commit()
            logger.info(f"Successfully saved variations for Student {student.student_no}.")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Database error saving student {student.student_no}: {e}")
            all_students_evaluated = False

    return all_students_evaluated

def run_worker():
    logger.info("Initializing Evaluation Worker...")
    app = create_app()
    evaluator = Evaluator()

    with app.app_context():
        logger.info("Worker successfully connected to the database. Starting polling loop...")
        is_waiting_logged = False

        while True:
            try:
                recover_stale_sessions()

                if MarkingSession.query.filter_by(stage="Conversion Processing").first():
                    logger.info("Conversion in progress. Pausing Evaluation...")
                    time.sleep(5)
                    continue

                with lock:
                    sessions_to_process = fetch_pending_sessions()

                    if sessions_to_process:
                        is_waiting_logged = False
                        logger.info(f"Found {len(sessions_to_process)} Evaluation Pending sessions.")
                        
                        evaluator.load_models()

                        for session in sessions_to_process:
                            logger.info(f"Processing Session: {session.id} ---")
                            session.stage = "Evaluation Processing"
                            db.session.commit()

                            success = process_evaluations(session, evaluator)

                            if success:
                                logger.info(f"Session {session.id} fully evaluated. Stage -> Evaluated.")
                                session.stage = "Evaluated"
                                session.status = "completed"

                                completion_notification = UserUpdate(
                                    user_id=session.user_id,
                                    type="MarkingSessionUpdate",
                                    title="Evaluation Complete!",
                                    message="Your session has been successfully evaluated! All marking and feedback generation is 100% complete and ready for your review.",
                                    related_id=str(session.id),
                                )
                                db.session.add(completion_notification)
                            else:
                                logger.info(f"Session {session.id} partially failed. Remaining in Processing.")
                                session.status = "error"
                                
                            db.session.commit()

                        evaluator.unload_models()

                    else:
                        if not is_waiting_logged:
                            logger.info("No Evaluation Pending sessions. Passing baton...")
                            is_waiting_logged = True

                db.session.commit()
                time.sleep(5)

            except Timeout:
                logger.info("Conversion grabbed the lock first. Waiting my turn...")
                time.sleep(5)
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                db.session.rollback()
                time.sleep(5)

if __name__ == "__main__":
    run_worker()