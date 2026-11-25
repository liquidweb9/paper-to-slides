#!/usr/bin/env python3
"""Render a PDF page or rectangular figure crop to PNG for source verification."""

import argparse
import json
from math import isfinite
from pathlib import Path


def render(args):
    try:
        import pymupdf
    except ImportError as error:
        raise ValueError("PDF rendering requires PyMuPDF (python -m pip install pymupdf).") from error

    if args.output.suffix.lower() != ".png":
        raise ValueError("Output filename must end in .png.")
    if args.page < 1 or args.dpi < 1:
        raise ValueError("Page and DPI must be positive.")
    with pymupdf.open(args.pdf) as document:
        if not document.is_pdf or document.needs_pass:
            raise ValueError("Expected a readable PDF.")
        if args.page > document.page_count:
            raise ValueError(f"PDF page {args.page} is out of range (1–{document.page_count}).")
        page = document[args.page - 1]
        clip = None
        if args.crop:
            if not all(isfinite(coordinate) for coordinate in args.crop):
                raise ValueError("Crop coordinates must be finite numbers.")
            clip = pymupdf.Rect(args.crop)
            if not clip.is_valid or clip.is_empty or not page.rect.contains(clip):
                raise ValueError(f"Crop must have positive area within the displayed page bounds {tuple(page.rect)}.")
        pixmap = page.get_pixmap(dpi=args.dpi, clip=clip)
        png = pixmap.tobytes("png")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write(png)
    return {
        "pdf": str(args.pdf), "pdf_page": args.page, "crop_points": args.crop,
        "dpi": args.dpi, "output": str(args.output),
        "width_pixels": pixmap.width, "height_pixels": pixmap.height,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, help="Local original or archived PDF")
    parser.add_argument("--page", required=True, type=int, help="1-based PDF page position")
    parser.add_argument("--output", required=True, type=Path, help="New output PNG")
    parser.add_argument("--dpi", type=int, default=200)
    parser.add_argument("--crop", nargs=4, type=float, metavar=("X0", "Y0", "X1", "Y1"),
                        help="Crop in PDF points from the top-left of the displayed page")
    try:
        print(json.dumps(render(parser.parse_args())))
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f"PDF rendering failed: {error}\n")


if __name__ == "__main__":
    main()
