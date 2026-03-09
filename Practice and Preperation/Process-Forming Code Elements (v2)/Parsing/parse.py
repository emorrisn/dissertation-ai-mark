from __future__ import annotations

from typing import Iterable
from scripts.utils import (
	DATA_DIR,
	ensure_dir,
)
from scripts.markschemes import MarkschemeProcessor
from scripts.images import process_images


def main(argv: Iterable[str] | None = None) -> int:
	ensure_dir(DATA_DIR)
	processor = MarkschemeProcessor()

	while True:
		if not any(DATA_DIR.iterdir()):
			print("No files found. Exiting.")
			break

		print("Files found. Processing aggregated mark schemes...")
		processor.process()

		print("Processing image files...")
		image_counts = process_images()
		markscheme_count = image_counts.get("markschemes", 0)
		student_count = image_counts.get("students", 0)
		if markscheme_count or student_count:
			print(
				f"Converted {markscheme_count} mark scheme image(s) and {student_count} student page image(s)."
			)
		else:
			print("No images to convert this pass.")
		print("Cycle complete. Re-checking for remaining files...\n")
	return 0	

		


if __name__ == "__main__":
	raise SystemExit(main())

