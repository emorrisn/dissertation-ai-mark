import logging
import re
import os

logger = logging.getLogger(__name__)

class FeedbackEvaluator:
    def __init__(self, model_caller):
        self.model_caller = model_caller
        self.summary_tokens = int(os.getenv("EVALUATION_WORKER_SUMMARY_TOKENS", "250"))
        self.confidence_tokens = int(os.getenv("EVALUATION_WORKER_CONFIDENCE_TOKENS", "10"))

    def generate_summaries(self, student_text, markscheme, writing_styles, style_definitions):
        summaries = {}

        for style in writing_styles:
            style_description = style_definitions.get(style, f"Adopt a highly professional {style} persona.")
            
            # STAGE 1: Generate the Description (Raw Text)
            desc_system_prompt = (
                "ROLE: Expert automated examiner.\n"
                f"TASK: Evaluate the student against the mark scheme using a {style} persona.\n"
                f"PERSONA GUIDANCE: {style_description}\n"
                "INSTRUCTION:\n"
                "Write a summary of the student's performance. Cite specific Geography concepts.\n"
                "STRICT LIMIT: MAXIMUM 3 SENTENCES. DO NOT waffle.\n"
                "Do NOT use JSON. Do NOT use markdown. Just write the raw text.\n"
                "CRITICAL: NO PREAMBLE. NO INTRODUCTORY TEXT. DO NOT say 'Here is the feedback'. Start immediately with the first word of the actual feedback."
            )
            
            desc_user_prompt = f"# MARKSCHEME:\n{markscheme}\n\n# STUDENT SUBMISSION:\n{student_text}\n\nSummary:"
            
            # Request 250 tokens for the description
            raw_desc = self.model_caller(desc_system_prompt, desc_user_prompt, max_tokens=self.summary_tokens).strip()
            
            # Clean up stray quotes
            clean_desc = raw_desc.replace('"', '').replace('```', '').strip()
            if not clean_desc:
                clean_desc = f"AI failed to generate a {style} summary."

            # STAGE 2: Generate the Confidence Score
            conf_system_prompt = (
                "ROLE: AI Quality Assurance.\n"
                "TASK: Rate how accurately the generated feedback evaluates the student's submission against the mark scheme.\n"
                "INSTRUCTION:\n"
                "Provide a single float number between 0.00 and 1.00 representing your confidence.\n"
                "Output ONLY the number. No text, no explanation."
            )
            
            conf_user_prompt = (
                f"# MARKSCHEME:\n{markscheme}\n\n"
                f"# STUDENT SUBMISSION:\n{student_text}\n\n"
                f"# GENERATED FEEDBACK:\n{clean_desc}\n\n"
                "Confidence Score (0.00-1.00):"
            )

            logger.info(f"[Style: {style}] Generating Summary...")
            
            # We only need 10 tokens for a number! Lightning fast.
            raw_conf = self.model_caller(conf_system_prompt, conf_user_prompt, max_tokens=self.confidence_tokens).strip()
            
            # Robustly extract just the number (in case it says "Score: 0.85")
            try:
                # Extract only digits and decimal points
                num_str = re.sub(r'[^\d.]', '', raw_conf)
                confidence = float(num_str) if num_str else 0.85
                # Clamp it between 0 and 1 just to be safe
                confidence = max(0.0, min(1.0, confidence))
            except Exception as e:
                logger.warning(f"Failed to parse confidence score for {style}. Defaulting to 0.85. Raw: {raw_conf}")
                confidence = 0.85

            # Python safely packages the data
            summaries[style] = {
                "description": clean_desc,
                "confidence": confidence
            }
        
        return summaries