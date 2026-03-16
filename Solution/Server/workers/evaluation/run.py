import sys
import os
import time
import gc # Added for memory management
from datetime import datetime, timedelta, timezone
from filelock import FileLock, Timeout

current_dir = os.path.dirname(os.path.abspath(__file__))
server_dir = os.path.abspath(os.path.join(current_dir, '../../'))
sys.path.append(server_dir)

from api import create_app
from api.extensions import db
from api.models import MarkingSession 

# The Shared Baton (Must be the EXACT same path as the conversion script)
LOCK_PATH = os.path.join(server_dir, "worker_processing.lock")
lock = FileLock(LOCK_PATH, timeout=0)

def run_worker():
    print("Initializing Evaluation Worker...")
    app = create_app()

    with app.app_context():
        print("Worker successfully connected to the database. Starting polling loop...")
        
        while True:
            try:
                # Zombie Sweeper (Crash Recovery)
                timeout_threshold = datetime.now(timezone.utc) - timedelta(minutes=30)
                
                # Find any sessions that have been stuck in "Evaluation Processing"
                stale_sessions = MarkingSession.query.filter(
                    MarkingSession.stage == "Evaluation Processing",
                    MarkingSession.updated_at < timeout_threshold
                ).all()

                if stale_sessions:
                    print(f"\nFound {len(stale_sessions)} crashed sessions. Reverting to Pending...")
                    for session in stale_sessions:
                        session.stage = "Evaluation Pending"
                    db.session.commit()

                # Database Check (Fast-Fail)
                if MarkingSession.query.filter_by(stage="Conversion Processing").first():
                    print("Conversion in progress (DB check). Pausing Evaluation...", end="\n")
                    time.sleep(5)
                    continue

                # Atomic File Lock (Race Condition Prevention)
                with lock:
                    # Fetch the exact same top 3 oldest unfinished sessions
                    top_sessions = MarkingSession.query \
                        .filter(MarkingSession.stage != "Evaluated") \
                        .order_by(MarkingSession.created_at.asc()) \
                        .limit(3) \
                        .all()

                    # Filter out ONLY the sessions this specific worker needs to handle
                    sessions_to_process = [s for s in top_sessions if s.stage == "Evaluation Pending"]

                    if sessions_to_process:
                        print(f"\nFound {len(sessions_to_process)} sessions in this batch.")
                        
                        # STEP 1: LOAD THE LLM
                        print(">>> LOADING EVALUATION LLM INTO MEMORY... <<<")
                        # e.g., eval_model = AutoModelForCausalLM.from_pretrained(...)
                        
                        for session in sessions_to_process:
                            print(f"\n -> Evaluating Session ID: {session.id}")
                            
                            session.stage = "Evaluation Processing"
                            db.session.commit()
                            
                            # ===================================================
                            # STEP 2: PROCESS WITH LLM
                            # ===================================================
                            print(f"....BEEP BOOP (Evaluating Session {session.id} with LLM)....")
                            # e.g., grade = eval_model.generate(student_text)
                            
                            # Mark as completely finished
                            # session.stage = "Evaluated"
                            # db.session.commit()

                        # STEP 3: UNLOAD THE LLM AND PURGE MEMORY
                        print("\n>>> BATCH FINISHED. UNLOADING EVALUATION LLM FROM MEMORY... <<<")
                        # del eval_model
                        gc.collect()
                        # torch.cuda.empty_cache()
                        print(">>> MEMORY PURGED. <<<")

                    else:
                        print("No Evaluation Pending sessions in top 3. Passing the baton...", end="\n")

                # Force SQLAlchemy to fetch fresh data next loop
                db.session.commit()

                # Wait for lock until checking again
                time.sleep(5)

            except Timeout:
                # This catches the millisecond race condition if the DB check missed it
                print("Conversion grabbed the lock first. Waiting my turn...", end="\n")
                time.sleep(5)
                
            except Exception as e:
                print(f"\nAn error occurred while polling: {e}")
                db.session.rollback()
                time.sleep(5)

if __name__ == "__main__":
    run_worker()