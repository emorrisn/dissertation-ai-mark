from __future__ import annotations

import logging
import os
import threading
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image
import torch
from transformers import AutoModelForImageTextToText, AutoProcessor, TextIteratorStreamer

from .utils import (
	DATA_DIR,
	EVAL_DIR,
	ensure_dir,
	is_image,
	move_safely,
	parse_markscheme_name,
	parse_student_img_name,
)


logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(asctime)s: %(message)s')
os.environ['TRANSFORMERS_VERBOSITY'] = 'info'

# Fix GPU memory fragmentation (optional)
# os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'

_MODEL_CACHE: Dict[str, object] = {"processor": None, "model": None, "device": None}


def setup_model() -> Tuple[AutoProcessor, AutoModelForImageTextToText, str]:
	"""Load (or reuse) the Nanonets OCR model and processor."""
	if _MODEL_CACHE["processor"] and _MODEL_CACHE["model"]:
		return (
			_MODEL_CACHE["processor"],
			_MODEL_CACHE["model"],
			_MODEL_CACHE["device"] or ("cuda" if torch.cuda.is_available() else "cpu"),
		)

	logging.info("Starting Nanonets-OCR2-3B model setup...")
	model_path = "nanonets/Nanonets-OCR2-3B"
	device = "cuda" if torch.cuda.is_available() else "cpu"
	logging.info(f"Device selected: {device}")

	model = AutoModelForImageTextToText.from_pretrained(
		model_path,
		dtype="auto",
		device_map="auto",
		attn_implementation="sdpa",
		trust_remote_code=True,
		low_cpu_mem_usage=True,
	)

	model.eval()

	processor = AutoProcessor.from_pretrained(model_path, trust_remote_code=True)

	logging.info("Model loaded successfully!")

	if device == "cuda":
		mem_allocated = torch.cuda.memory_allocated() / 1024**3
		mem_reserved = torch.cuda.memory_reserved() / 1024**3
		logging.info(f"Using GPU: {torch.cuda.get_device_name(0)}")
		logging.info(f"Total GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
		logging.info(f"GPU Memory Allocated: {mem_allocated:.2f} GB")
		logging.info(f"GPU Memory Reserved: {mem_reserved:.2f} GB")

	_MODEL_CACHE["processor"] = processor
	_MODEL_CACHE["model"] = model
	_MODEL_CACHE["device"] = device

	return processor, model, device


def process_image(image_path: str, processor: AutoProcessor, model: AutoModelForImageTextToText, max_new_tokens: int = 1024) -> str:
	"""Process a single image and extract text using Nanonets OCR (unchanged)."""
	logging.info(f"Processing image: {image_path}")

	prompt = (
		"Extract all handwritten text from the provided image. as if you were reading it naturally."
		"You are an OCR assistant. Transcribe ONLY handwritten content (letters, numbers, math, annotations). "
		"Ignore printed / typed text such as headers, instructions, watermarks, logos, page numbers, or form labels. "
		"Do NOT invent text. Do NOT output placeholder lines like '_' or '____'. Skip empty/blank lines. "
		"Preserve the natural order of the handwriting. If a line is illegible, omit it rather than guessing."
	)

	logging.info("Loading image...")
	image = Image.open(image_path)
	original_size = image.size
	logging.info(f"Original image size: {original_size}")

	max_image_size = 1536
	if max(image.size) > max_image_size:
		ratio = max_image_size / max(image.size)
		new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
		image = image.resize(new_size, Image.Resampling.LANCZOS)
		logging.info(f"Resized image to: {image.size}")
	else:
		logging.info(f"Image size: {image.size}")

	logging.info("Creating message format...")
	messages = [
		{"role": "system", "content": "You are a helpful assistant."},
		{"role": "user", "content": [
			{"type": "image", "image": f"file://{image_path}"},
			{"type": "text", "text": prompt},
		]},
	]

	logging.info("Applying chat template...")
	text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

	logging.info("Processing image and text inputs...")
	inputs = processor(text=[text], images=[image], padding=True, return_tensors="pt")
	inputs = inputs.to(model.device)

	if torch.cuda.is_available():
		mem_after_input = torch.cuda.memory_allocated() / 1024**3
		logging.info(f"GPU memory after input preparation: {mem_after_input:.2f} GB")

	logging.info(f"Starting text generation (max {max_new_tokens} tokens)...")
	logging.info("Streaming tokens to console...")

	tokenizer = getattr(processor, "tokenizer", None)

	if tokenizer is None:
		raise RuntimeError("Processor has no tokenizer; load a tokenizer or use a processor that bundles one.")

	streamer = TextIteratorStreamer(
		tokenizer,
		skip_prompt=True,
		skip_special_tokens=True,
		decode_kwargs={"clean_up_tokenization_spaces": True},
	)
	chunks: List[str] = []

	def _consume() -> None:
		for piece in streamer:
			chunks.append(piece)
			print(piece, end="", flush=True)

	t = threading.Thread(target=_consume)
	t.start()

	with torch.inference_mode():
		output_ids = model.generate(
			**inputs,
			max_new_tokens=max_new_tokens,
			do_sample=False,
			num_beams=1,
			streamer=streamer,
		)
	t.join()
	logging.info("Generation finished.")
	output_text = ''.join(chunks)

	del inputs, output_ids, image
	if torch.cuda.is_available():
		torch.cuda.empty_cache()
		mem_after = torch.cuda.memory_allocated() / 1024**3
		logging.info(f"GPU memory after cleanup: {mem_after:.2f} GB")

	logging.info("Processing complete!")
	return output_text


def save_output(text: str, output_path: Path) -> None:
	p = Path(output_path)
	p.parent.mkdir(parents=True, exist_ok=True)
	p.write_text(text, encoding='utf-8')
	logging.info(f"Saved output to: {p.resolve()}")


def append_output(text: str, output_path: Path) -> None:
	p = Path(output_path)
	p.parent.mkdir(parents=True, exist_ok=True)
	with p.open('a', encoding='utf-8') as f:
		if p.exists() and p.stat().st_size > 0:
			f.write("\n\n")
		f.write(text)
	logging.info(f"Appended output to: {p.resolve()}")


def process_images(
	*,
	data_dir: Path | None = None,
	eval_output_dir: Path | None = None,
	max_new_tokens: int = 1024,
) -> dict[str, int]:
	"""Process all mark scheme and student images in data_dir.

	Mark scheme OCR results stay inside data_dir as mX_Ay.txt so the mark scheme processor can ingest
	them later. Student OCR results go to Evaluation/data (one file per student).
	"""

	data_dir = Path(data_dir) if data_dir else DATA_DIR
	eval_output_dir = Path(eval_output_dir) if eval_output_dir else EVAL_DIR
	ensure_dir(data_dir)
	ensure_dir(eval_output_dir)

	image_files = [p for p in data_dir.iterdir() if p.is_file() and is_image(p)]
	if not image_files:
		return {"markschemes": 0, "students": 0}

	processor, model, _device = setup_model()

	markscheme_images: List[Tuple[tuple, Path, str, str]] = []
	student_images: List[Tuple[tuple, Path, str, str, str]] = []

	for image_file in image_files:
		parsed_ms = parse_markscheme_name(image_file)
		if parsed_ms:
			session_id, artifact_id, _ext = parsed_ms
			sort_key = (int(session_id), int(artifact_id), image_file.name.lower())
			markscheme_images.append((sort_key, image_file, session_id, artifact_id))
			continue

		parsed_student = parse_student_img_name(image_file)
		if parsed_student:
			session_id, student_id, page_id = parsed_student
			sort_key = (int(session_id), int(student_id), int(page_id))
			student_images.append((sort_key, image_file, session_id, student_id, page_id))
			continue

		logging.warning(
			"Filename '%s' did not match mark-scheme 'm{x}_A{y}' nor student 'm{x}_s{y}_p{z}'. Skipping...",
			image_file.name,
		)

	markscheme_images.sort(key=lambda item: item[0])
	student_images.sort(key=lambda item: item[0])

	results = {"markschemes": 0, "students": 0}

	for idx, (_key, image_file, session_id, artifact_id) in enumerate(markscheme_images, 1):
		logging.info(f"[MarkScheme] Processing image {idx}/{len(markscheme_images)}: {image_file.name}")
		if not image_file.exists():
			logging.warning("File not found: %s, skipping...", image_file)
			continue
		try:
			text = process_image(str(image_file.absolute()), processor, model, max_new_tokens=max_new_tokens)
		except Exception as exc:
			logging.error("Error processing %s: %s", image_file, exc, exc_info=True)
			continue

		artifact_txt = data_dir / f"m{session_id}_A{artifact_id}.txt"
		if artifact_txt.exists():
			append_output(text, artifact_txt)
		else:
			save_output(text, artifact_txt)

		try:
			image_file.unlink()
			logging.info("Deleted processed image: %s", image_file.name)
		except Exception as delete_error:
			logging.warning("Could not delete %s: %s", image_file.name, delete_error)

		results["markschemes"] += 1

	current_student: Tuple[str, str] | None = None
	processed_count = 0

	def finalize_student(student_key: Tuple[str, str]) -> None:
		if not student_key:
			return
		session_id, student_id = student_key
		aggregate_path = data_dir / f"m{session_id}_s{student_id}.txt"
		if not aggregate_path.exists():
			return
		pending = False
		for candidate in data_dir.iterdir():
			if not candidate.is_file() or not is_image(candidate):
				continue
			parsed = parse_student_img_name(candidate)
			if parsed and parsed[0] == session_id and parsed[1] == student_id:
				pending = True
				break
		if pending:
			logging.info("Student m%s_s%s still has pages pending; keeping aggregate in data directory.", session_id, student_id)
			return
		try:
			moved_path = move_safely(aggregate_path, eval_output_dir)
			logging.info("Moved student aggregate %s -> %s", aggregate_path.name, moved_path.name)
		except Exception as exc:
			logging.warning("Could not move %s to evaluation: %s", aggregate_path.name, exc)

	for idx, (_key, image_file, session_id, student_id, page_id) in enumerate(student_images, 1):
		student_key = (session_id, student_id)
		if current_student and student_key != current_student:
			finalize_student(current_student)
			current_student = student_key
		elif not current_student:
			current_student = student_key

		logging.info(f"[Student] Processing image {idx}/{len(student_images)}: {image_file.name}")
		if not image_file.exists():
			logging.warning("File not found: %s, skipping...", image_file)
			continue
		try:
			text = process_image(str(image_file.absolute()), processor, model, max_new_tokens=max_new_tokens)
		except Exception as exc:
			logging.error("Error processing %s: %s", image_file, exc, exc_info=True)
			continue

		student_file_data = data_dir / f"m{session_id}_s{student_id}.txt"
		student_file_eval = eval_output_dir / student_file_data.name
		if not student_file_data.exists() and student_file_eval.exists():
			logging.info(
				"Student aggregate %s already in evaluation; moving back to data to append new pages.",
				student_file_eval.name,
			)
			ensure_dir(student_file_data.parent)
			student_file_eval.replace(student_file_data)

		if student_file_data.exists():
			append_output(text, student_file_data)
		else:
			save_output(text, student_file_data)

		try:
			image_file.unlink()
			logging.info("Deleted processed image: %s", image_file.name)
		except Exception as delete_error:
			logging.warning("Could not delete %s: %s", image_file.name, delete_error)

		processed_count += 1

	if current_student:
		finalize_student(current_student)

	results["students"] += processed_count

	return results


def process_mark_scheme_images(data_dir: Path | None = None, max_new_tokens: int = 1024) -> int:
	"""Backwards-compatible wrapper returning only mark scheme counts."""
	results = process_images(data_dir=data_dir, max_new_tokens=max_new_tokens)
	return results.get("markschemes", 0)


def process_student_images(*_args, **_kwargs) -> int:
	"""Process only student images (wrapper for compatibility)."""
	results = process_images()
	return results.get("students", 0)


__all__ = [
	"setup_model",
	"process_image",
	"save_output",
	"append_output",
	"process_images",
	"process_mark_scheme_images",
	"process_student_images",
]
