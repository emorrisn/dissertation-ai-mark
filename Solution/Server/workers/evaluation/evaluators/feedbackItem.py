import logging
import os

logger = logging.getLogger(__name__)

class FeedbackItemEvaluator:
    def __init__(self, model_caller):
        self.model_caller = model_caller
        self.item_tokens = int(os.getenv("EVALUATION_WORKER_ITEM_TOKENS", "250"))

    def generate_item(self, student_text, markscheme, style, style_description, summary_desc, output_type, definition):
        system_prompt = (
            "ROLE: Expert automated examiner.\n"
            f"TASK: Generate the '{output_type}' feedback section for a student.\n"
            f"PERSONA: {style}. {style_description}\n"
            f"OVERALL CONTEXT (Use this to align your tone and facts): {summary_desc}\n\n"
            "SPECIFIC REQUIREMENT FOR THIS SECTION:\n"
            f"{definition}\n\n"
            "INSTRUCTION:\n"
            "Output a highly specific response citing geography keywords from the mark scheme where relevant.\n"
            "STRICT LIMIT: MAXIMUM 3 SENTENCES. DO NOT EXCEED 3 SENTENCES.\n"
            "Do NOT use JSON. Do NOT use markdown. Just write the raw text.\n"
            "CRITICAL: NO PREAMBLE. NO INTRODUCTORY TEXT. DO NOT say 'Here is the feedback'. Start immediately with the first word of the actual feedback."
        )
        
        user_prompt = f"# MARKSCHEME:\n{markscheme}\n\n# STUDENT SUBMISSION:\n{student_text}\n\nFeedback:"

        logger.info(f"[Style: {style}] [Output_type: {output_type}] Generating...")
        
        raw_res = self.model_caller(system_prompt, user_prompt, max_tokens=self.item_tokens)
        
        # Strip away any markdown code blocks or stray quotes the AI might add
        clean_text = raw_res.replace('"', '').replace('```', '').strip()
        
        if not clean_text:
            logger.warning(f"Failed to generate item '{output_type}' for {style}: output was empty.")
            return "Content generation failed or was empty."
            
        return clean_text