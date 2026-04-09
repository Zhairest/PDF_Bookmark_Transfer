#!/usr/bin/env python3
"""Copy PDF outline/bookmarks from one PDF onto another PDF's pages."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader, PdfWriter
from pypdf.generic import Destination, Fit, NameObject, create_string_object


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Copy the outline/bookmarks from one PDF onto another PDF without "
            "changing the destination PDF's page contents."
        )
    )
    parser.add_argument(
        "--content",
        required=True,
        type=Path,
        help="PDF whose page content should be kept, e.g. the high-resolution typeA file.",
    )
    parser.add_argument(
        "--bookmarks",
        required=True,
        type=Path,
        help="PDF whose outline/bookmarks should be copied, e.g. the typeB file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output PDF path. Defaults to '<content>_with_bookmarks.pdf'.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the output file if it already exists.",
    )
    return parser.parse_args()


def page_size(page) -> tuple[float, float]:
    box = page.mediabox
    return float(box.width), float(box.height)


def scale_horizontal(value: float | None, source_page, target_page) -> float | None:
    if value is None:
        return None
    source_width, _ = page_size(source_page)
    target_width, _ = page_size(target_page)
    if source_width == 0:
        return value
    return value * target_width / source_width


def scale_vertical(value: float | None, source_page, target_page) -> float | None:
    if value is None:
        return None
    _, source_height = page_size(source_page)
    _, target_height = page_size(target_page)
    if source_height == 0:
        return value
    return value * target_height / source_height


def destination_to_fit(destination: Destination, source_page, target_page) -> Fit:
    destination_type = str(destination.get("/Type", "/Fit"))

    if destination_type == "/XYZ":
        return Fit.xyz(
            left=scale_horizontal(destination.get("/Left"), source_page, target_page),
            top=scale_vertical(destination.get("/Top"), source_page, target_page),
            zoom=destination.get("/Zoom"),
        )
    if destination_type == "/Fit":
        return Fit.fit()
    if destination_type == "/FitB":
        return Fit.fit_box()
    if destination_type == "/FitH":
        return Fit.fit_horizontally(
            top=scale_vertical(destination.get("/Top"), source_page, target_page)
        )
    if destination_type == "/FitBH":
        return Fit.fit_box_horizontally(
            top=scale_vertical(destination.get("/Top"), source_page, target_page)
        )
    if destination_type == "/FitV":
        return Fit.fit_vertically(
            left=scale_horizontal(destination.get("/Left"), source_page, target_page)
        )
    if destination_type == "/FitBV":
        return Fit.fit_box_vertically(
            left=scale_horizontal(destination.get("/Left"), source_page, target_page)
        )
    if destination_type == "/FitR":
        return Fit.fit_rectangle(
            left=scale_horizontal(destination.get("/Left"), source_page, target_page),
            bottom=scale_vertical(destination.get("/Bottom"), source_page, target_page),
            right=scale_horizontal(destination.get("/Right"), source_page, target_page),
            top=scale_vertical(destination.get("/Top"), source_page, target_page),
        )

    raise ValueError(f"Unsupported outline destination type: {destination_type}")


def is_outline_open(destination: Destination) -> bool:
    count = destination.get("/Count")
    return count is None or count >= 0


def font_flags(destination: Destination) -> tuple[bool, bool]:
    flags = int(destination.get("/F", 0) or 0)
    italic = bool(flags & 1)
    bold = bool(flags & 2)
    return bold, italic


def normalize_color(destination: Destination) -> tuple[float, float, float] | None:
    color = destination.get("/C")
    if not color:
        return None
    return tuple(float(component) for component in color[:3])


def copy_outline_tree(
    writer: PdfWriter,
    outline_items: Iterable[Destination | list],
    bookmarks_reader: PdfReader,
    content_reader: PdfReader,
    parent=None,
) -> int:
    copied_count = 0
    last_added = None

    for item in outline_items:
        if isinstance(item, list):
            if last_added is None:
                raise ValueError("Encountered child outline items without a parent item.")
            copied_count += copy_outline_tree(
                writer=writer,
                outline_items=item,
                bookmarks_reader=bookmarks_reader,
                content_reader=content_reader,
                parent=last_added,
            )
            continue

        page_index = bookmarks_reader.get_destination_page_number(item)
        if page_index < 0:
            raise ValueError(f"Could not resolve page number for outline item: {item.title}")
        if page_index >= len(content_reader.pages):
            raise ValueError(
                f"Outline item '{item.title}' points to page {page_index + 1}, "
                f"but the content PDF only has {len(content_reader.pages)} pages."
            )

        bold, italic = font_flags(item)
        fit = destination_to_fit(
            destination=item,
            source_page=bookmarks_reader.pages[page_index],
            target_page=content_reader.pages[page_index],
        )
        last_added = writer.add_outline_item(
            title=str(item.title),
            page_number=page_index,
            parent=parent,
            color=normalize_color(item),
            bold=bold,
            italic=italic,
            fit=fit,
            is_open=is_outline_open(item),
        )
        last_added.get_object()[NameObject("/Title")] = create_string_object(
            str(item.title).encode("utf-16")
        )
        copied_count += 1

    return copied_count


def filtered_metadata(reader: PdfReader) -> dict[str, str]:
    metadata = {}
    for key, value in (reader.metadata or {}).items():
        if isinstance(key, str) and isinstance(value, str):
            metadata[key] = value
    return metadata


def merge_bookmarks(content_path: Path, bookmarks_path: Path, output_path: Path) -> int:
    logging.getLogger("pypdf").setLevel(logging.ERROR)

    content_reader = PdfReader(str(content_path))
    bookmarks_reader = PdfReader(str(bookmarks_path))

    outline = bookmarks_reader.outline
    if not outline:
        raise ValueError(f"No outline/bookmarks were found in {bookmarks_path}.")

    writer = PdfWriter()
    writer.append(content_reader, import_outline=False)

    metadata = filtered_metadata(content_reader)
    if metadata:
        writer.add_metadata(metadata)

    try:
        if content_reader.page_layout:
            writer.page_layout = content_reader.page_layout
    except Exception:
        pass
    writer.page_mode = "/UseOutlines"

    copied_count = copy_outline_tree(
        writer=writer,
        outline_items=outline,
        bookmarks_reader=bookmarks_reader,
        content_reader=content_reader,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as output_file:
        writer.write(output_file)

    return copied_count


def main() -> int:
    args = parse_args()
    content_path = args.content.expanduser().resolve()
    bookmarks_path = args.bookmarks.expanduser().resolve()
    output_path = (
        args.output.expanduser().resolve()
        if args.output
        else content_path.with_name(f"{content_path.stem}_with_bookmarks.pdf")
    )

    if not content_path.exists():
        raise SystemExit(f"Content PDF not found: {content_path}")
    if not bookmarks_path.exists():
        raise SystemExit(f"Bookmarks PDF not found: {bookmarks_path}")
    if output_path == content_path or output_path == bookmarks_path:
        raise SystemExit(
            "Output path must be different from both input PDFs to avoid overwriting them."
        )
    if output_path.exists() and not args.force:
        raise SystemExit(
            f"Output file already exists: {output_path}\n"
            "Pass --force to overwrite it."
        )

    copied_count = merge_bookmarks(content_path, bookmarks_path, output_path)
    print(f"Created: {output_path}")
    print(f"Copied outline items: {copied_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
