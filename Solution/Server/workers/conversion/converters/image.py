import io
import gc
import os
import logging
import torch
from PIL import Image
from transformers import AutoModelForImageTextToText, AutoProcessor, BitsAndBytesConfig
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)
class ImageConverter:
    def __init__(self):
        """Initialize the converter settings without loading the massive model into RAM."""

        # Base
        self.model_path = os.getenv("CONVERTER_WORKER_MODEL_PATH", "nanonets/Nanonets-OCR2-3B")
        self.max_new_tokens = int(os.getenv("CONVERTER_WORKER_MAX_NEW_TOKENS", "1024"))
        self.max_image_size = int(os.getenv("CONVERTER_WORKER_MAX_IMAGE_SIZE", "1024"))

        # Model Setup
        self.device_map = os.getenv("CONVERTER_WORKER_DEVICE_MAP", "auto")
        self.attn_impl = os.getenv("CONVERTER_WORKER_ATTN_IMPLEMENTATION", "sdpa")
        self.trust_remote = os.getenv("CONVERTER_WORKER_TRUST_REMOTE_CODE", "True").lower() in ("true", "1", "t")
        self.low_cpu_mem = os.getenv("CONVERTER_WORKER_LOW_CPU_MEM_USAGE", "True").lower() in ("true", "1", "t")
        self.load_in_4bit = os.getenv("CONVERTER_WORKER_LOAD_IN_4BIT", "True").lower() in ("true", "1", "t")

        # Dtype
        dtype_str = os.getenv("CONVERTER_WORKER_DTYPE", "float16").lower()
        if dtype_str == "float16":
            self.torch_dtype = torch.float16
        elif dtype_str == "bfloat16":
            self.torch_dtype = torch.bfloat16
        else:
            self.torch_dtype = "auto"

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.processor = None
        
        self.prompt = (
            "Extract all handwritten text from the provided image. as if you were reading it naturally."
            "You are an OCR assistant. Transcribe ONLY handwritten content (letters, numbers, math, annotations). "
            "Additionally, if there is a drawn diagram, printed element circled, or visual annotations (arrows, underlines, crosses), describe exactly what has been drawn and what has been circled. "
            "Ignore printed / typed text such as headers, instructions, watermarks, logos, page numbers, or form labels. "
            "Do NOT invent text. Do NOT output placeholder lines like '_' or '____'. Skip empty/blank lines. "
            "Preserve the natural order of the handwriting. If a line is illegible, omit it rather than guessing."
            "If there is absolutely no handwriting in the image, output exactly: NO_HANDWRITING_DETECTED"
        )

    def load(self):
        """Loads the model and processor into RAM/VRAM."""
        if self.model is not None and self.processor is not None:
            return # Already loaded
            
        logging.info(f"Loading {self.model_path} onto {self.device.upper()}...")

        quant_config = None
        if self.load_in_4bit and self.device == "cuda":
            logging.info("Applying 4-bit quantization to fit into VRAM...")
            quant_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=self.torch_dtype,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            )
        
        self.model = AutoModelForImageTextToText.from_pretrained(
            self.model_path,
            torch_dtype=self.torch_dtype,
            device_map=self.device_map,
            attn_implementation=self.attn_impl,
            trust_remote_code=self.trust_remote,
            low_cpu_mem_usage=self.low_cpu_mem,
            quantization_config=quant_config
        )
        self.model.eval()

        self.processor = AutoProcessor.from_pretrained(self.model_path, trust_remote_code=self.trust_remote)
        logging.info("Model loaded successfully!")

    def unload(self):
        """Destroys the model and forces the OS to reclaim the memory."""
        logging.info("Unloading model and purging memory...")
        
        # Delete references
        self.model = None
        self.processor = None
        
        # Force garbage collection
        gc.collect()
        
        # Empty GPU cache if applicable
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        logging.info("Memory purged successfully.")

    def convert(self, image_source) -> str:
        """
        Processes a single image and extracts text.
        Accepts either a file path (str/Path) or raw file bytes (bytes).
        """
        if self.model is None or self.processor is None:
            raise RuntimeError("Model is not loaded! Call .load() before .convert()")

        # Handle both file paths and raw database blobs
        if isinstance(image_source, bytes):
            image = Image.open(io.BytesIO(image_source))
        else:
            image = Image.open(image_source)

        # Convert to RGB to avoid issues with transparent PNGs or Grayscale
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Resize logic
        if max(image.size) > self.max_image_size:
            ratio = self.max_image_size / max(image.size)
            new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)

        # Formatting inputs
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": [
                {"type": "image", "image": image}, 
                {"type": "text", "text": self.prompt},
            ]},
        ]

        text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.processor(text=[text], images=[image], padding=True, return_tensors="pt")
        inputs = inputs.to(self.device)

        # Generate text
        with torch.inference_mode():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
                temperature=None,
                top_p=None,
                num_beams=1,
                repetition_penalty=1.15,
            )
        
        input_len = inputs["input_ids"].shape[1]
        generated_ids = output_ids[0][input_len:]

        # Decode output
        output_text = self.processor.decode(generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=True)

        # Clean up local variables immediately
        del inputs, output_ids, generated_ids, image

        if "NO_HANDWRITING_DETECTED" in output_text:
            return ""
        
        return output_text