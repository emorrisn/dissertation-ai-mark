import io
import gc
import logging
import torch
from PIL import Image
from transformers import AutoModelForImageTextToText, AutoProcessor

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

class ImageConverter:
    def __init__(self, model_path="nanonets/Nanonets-OCR2-3B", max_new_tokens=1024):
        """Initialize the converter settings without loading the massive model into RAM."""
        self.model_path = model_path
        self.max_new_tokens = max_new_tokens
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.processor = None
        
        self.prompt = (
            "Extract all handwritten text from the provided image. as if you were reading it naturally."
            "You are an OCR assistant. Transcribe ONLY handwritten content (letters, numbers, math, annotations). "
            "Ignore printed / typed text such as headers, instructions, watermarks, logos, page numbers, or form labels. "
            "Do NOT invent text. Do NOT output placeholder lines like '_' or '____'. Skip empty/blank lines. "
            "Preserve the natural order of the handwriting. If a line is illegible, omit it rather than guessing."
        )

    def load(self):
        """Loads the model and processor into RAM/VRAM."""
        if self.model is not None and self.processor is not None:
            return # Already loaded
            
        logging.info(f"Loading {self.model_path} onto {self.device.upper()}...")
        
        self.model = AutoModelForImageTextToText.from_pretrained(
            self.model_path,
            dtype="auto",
            device_map="auto",
            attn_implementation="sdpa",
            trust_remote_code=True,
            low_cpu_mem_usage=True,
        )
        self.model.eval()

        self.processor = AutoProcessor.from_pretrained(self.model_path, trust_remote_code=True)
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

        # Resize logic from your original script
        max_image_size = 1536
        if max(image.size) > max_image_size:
            ratio = max_image_size / max(image.size)
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
                num_beams=1,
            )

        # Decode output
        output_text = self.processor.batch_decode(output_ids, skip_special_tokens=True, clean_up_tokenization_spaces=True)[0]

        # Clean up local variables immediately
        del inputs, output_ids, image
        
        return output_text