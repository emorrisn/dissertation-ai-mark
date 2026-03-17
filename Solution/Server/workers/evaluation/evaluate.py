import logging
import gc
import torch
import os
import re
from threading import Thread
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TextIteratorStreamer
from dotenv import load_dotenv

from evaluators.feedback import FeedbackEvaluator
from evaluators.feedbackItem import FeedbackItemEvaluator

load_dotenv()
logger = logging.getLogger(__name__)

class Evaluator:
    def __init__(self):
        # Base Settings
        self.model_path = os.getenv("EVALUATION_WORKER_MODEL_PATH", "meta-llama/Meta-Llama-3-8B-Instruct")
        self.debug = os.getenv("EVALUATION_WORKER_DEBUG", "False").lower() in ("true", "1", "t")

        if self.debug:
            logger.setLevel(logging.DEBUG)
        
        self.device_map = os.getenv("EVALUATION_WORKER_DEVICE_MAP", "auto")
        self.attn_impl = os.getenv("EVALUATION_WORKER_ATTN_IMPLEMENTATION", "sdpa")
        self.trust_remote = os.getenv("EVALUATION_WORKER_TRUST_REMOTE_CODE", "True").lower() in ("true", "1", "t")
        self.low_cpu_mem = os.getenv("EVALUATION_WORKER_LOW_CPU_MEM_USAGE", "True").lower() in ("true", "1", "t")
        self.load_in_4bit = os.getenv("EVALUATION_WORKER_LOAD_IN_4BIT", "True").lower() in ("true", "1", "t")
        
        dtype_str = os.getenv("EVALUATION_WORKER_DTYPE", "bfloat16").lower()
        self.torch_dtype = torch.float16 if dtype_str == "float16" else torch.bfloat16
            
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.tokenizer = None

        # Store definitions to pass to the Item Evaluator
        self.output_definitions = {
            "Give Feedback": "Write a personalized 'Strength and Target' (WWW/EBI) summary. Highlight successful mark scheme applications and exact conceptual gaps.",
            "Score Work": "Provide a granular mark breakdown. Justify the score by citing specific requirements fully met, partially met, or absent.",
            "Section by Section": "Perform a chronological audit of the submission, explaining how each part contributes to the grade.",
            "What to Write": "Generate a 'Teacher Feedback Script'. Include a model answer explaining how to rephrase to meet 'Full Marks' criteria.",
            "Identify Misconceptions": "Diagnose errors to identify patterns of misunderstanding. Suggest the core concept to revisit.",
            "Next Steps Challenge": "Provide a 'Stretch and Challenge' task. Ask a probing question for correct answers, or a scaffolding hint for incorrect ones."
        }

        # Store definitions for styles
        self.style_definitions = {
            "Strict": "Focus heavily on exact keyword matches, highlight minor errors, and maintain a highly academic, formal, and uncompromising tone.",
            "Balanced": "Acknowledge strengths while clearly identifying areas for improvement. Maintain a supportive, objective, and constructive tone.",
            "Encouraging": "Focus heavily on the positive aspects of the student's work, use motivational language, and gently guide them toward corrections.",
            "Technical": "Focus intensely on geographical terminology, data accuracy, and logical flow. Maintain a dry, highly professional, and analytical tone."
        }

        # Initialize the specialists
        self.feedback_gen = FeedbackEvaluator(self._generate)
        self.item_gen = FeedbackItemEvaluator(self._generate)

    def load_models(self):
        if self.model is not None: return
        logger.info(f"Loading {self.model_path} onto {self.device.upper()}...")
        
        try:
            quant_config = None
            if self.load_in_4bit and self.device == "cuda":
                quant_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=self.torch_dtype,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path, trust_remote_code=self.trust_remote)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                torch_dtype=self.torch_dtype,
                device_map=self.device_map,
                attn_implementation=self.attn_impl,
                trust_remote_code=self.trust_remote,
                low_cpu_mem_usage=self.low_cpu_mem,
                quantization_config=quant_config
            )
            self.model.eval()
            logger.info("Evaluation Model loaded successfully!")
            
        except torch.cuda.OutOfMemoryError as e:
            logger.critical("CUDA OOM during model load! GPU might be tied up by another process.", exc_info=True)
            self.unload_models() # Sweep any half-loaded tensors out of VRAM
            raise e # Re-raise so the polling loop catches it and rolls back the database

        except Exception as e:
            logger.critical(f"Failed to load model {self.model_path}. Is the HuggingFace cache corrupted or disk full?", exc_info=True)
            self.unload_models() 
            raise e

    def unload_models(self):
        logger.info("Unloading LLM and purging memory...")
        self.model = None
        self.tokenizer = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def evaluate(self, student_text: str, markscheme_text: str, required_outputs: list, writing_styles: list) -> list:
        """The main orchestration loop called by run.py"""
        try: 
            if not self.model: self.load_models()

            # 1. Clean the text once to save VRAM
            clean_text = student_text.replace("Extra Space", "").replace('"', "'")
            clean_text = re.sub(r'\n\s*\n', '\n', clean_text).strip()

            # Strip underscores and whitespace to see if any actual words exist
            meaningful_text = re.sub(r'[_ \n\t]', '', clean_text)
            if len(meaningful_text) < 10:  # If less than 10 actual characters...
                logger.warning("Submission is practically blank. Short-circuiting AI.")
                return self._generate_blank_feedback(required_outputs, writing_styles)

            # 2. Stage 1: Get the 3 Personas (Now decoupled text & score)
            summaries = self.feedback_gen.generate_summaries(clean_text, markscheme_text, writing_styles, self.style_definitions)

            # 3. Stage 2: Get the Granular Items
            final_results = []
            for style, summary_data in summaries.items():
                summary_desc = summary_data.get("description", "Evaluation generated by AI.")
                confidence = summary_data.get("confidence", 0.8)
                style_description = self.style_definitions.get(style, f"Adopt a highly professional {style} persona.")

                variation_items = []
                for out_type in required_outputs:
                    definition = self.output_definitions.get(out_type, "Provide relevant feedback.")
                    
                    content = self.item_gen.generate_item(
                        clean_text, markscheme_text, style, style_description, summary_desc, out_type, definition
                    )
                    variation_items.append({"type": out_type, "content": content})
                
                final_results.append({
                    "description": summary_desc,
                    "confidence": confidence,
                    "items": variation_items
                })
            
            return final_results
        except Exception as e:
            # Added exc_info=True so you get line numbers!
            logger.error(f"Critical failure in evaluation orchestration: {e}", exc_info=True)
            return []
    
    def _generate_blank_feedback(self, required_outputs: list, writing_styles: list) -> list:
        """Instantly returns 0-mark feedback for blank submissions to save GPU time."""
        results = []
        for style in writing_styles:
            items = []
            for out_type in required_outputs:
                items.append({
                    "type": out_type, 
                    "content": "The student did not provide enough readable text to evaluate this section. 0 marks."
                })
            results.append({
                "description": "The submission was blank or contained only OCR artifacts. 0 marks awarded.",
                "confidence": 1.0, # We are 100% confident it's blank!
                "items": items
            })
        return results

    def _generate(self, system_prompt: str, user_prompt: str, max_tokens: int, retried: bool = False) -> str:
        """Helper that handles the GPU inference and optional streaming."""
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = self.tokenizer(text, return_tensors="pt").to(self.device)

            gen_kwargs = dict(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=0.3, # Bumped slightly to 0.3 for more natural text generation
                do_sample=True,
                use_cache=True,
                eos_token_id=self.tokenizer.eos_token_id,
                pad_token_id=self.tokenizer.pad_token_id
            )

            with torch.inference_mode():
                output_ids = self.model.generate(**gen_kwargs)
                output = ""
                output += self.tokenizer.decode(output_ids[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)

                if self.debug:
                    print("\n\n# Debug output:\n")
                    print(output)

                return output
        except torch.cuda.OutOfMemoryError as e:
            if not retried:
                logger.warning("CUDA Out of Memory! Clearing cache and attempting one retry...")
                
                # Sweep memory
                import gc
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                
                # Call itself again
                return self._generate(system_prompt, user_prompt, max_tokens, retried=True)
            else:
                logger.error("CUDA Out of Memory on retry! The student text is likely too massive for the context window.", exc_info=True)
                return "AI Generation failed: Submission exceeded available memory."
        except Exception as e:
            logger.error(f"Inference failure during _generate: {e}", exc_info=True)
            return "AI Generation failed due to an internal processing error."