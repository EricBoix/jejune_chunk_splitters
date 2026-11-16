"""Shared utilities for the split_by_*.py splitter scripts."""
import argparse
import json
import sys
from pathlib import Path

import yaml


def load_manifest(manifest_path: str) -> tuple[dict, Path]:
    path = Path(manifest_path)
    with open(path, encoding="utf-8") as f:
        manifest = yaml.safe_load(f)
    return manifest, path.parent


def blockquote_depth_change(token_type: str) -> int:
    """Change of the blockquote nesting depth brought by a markdown-it token.

    The paragraphs of a blockquote are 'paragraph_open' tokens (like the other
    paragraphs) enclosed between a 'blockquote_open' and a 'blockquote_close'
    token: tracking the depth tells whether a paragraph is within a blockquote.
    """
    if token_type == "blockquote_open":
        return 1
    if token_type == "blockquote_close":
        return -1
    return 0


def add_common_arguments(parser: argparse.ArgumentParser, modality: str) -> None:
    """Add --catalog, --output_dir, --output, --exclude-blockquotes to an ArgumentParser."""
    parser.add_argument(
        "--exclude-blockquotes",
        action="store_true",
        help=(
            "Leave the markdown blockquotes (e.g. the pull quotes of a book) out "
            "of the chunks. They do not consume a paragraph_number. "
            "By default blockquotes are kept."
        ),
    )
    parser.add_argument(
        "--catalog",
        action="append",
        metavar="CATALOG_YAML",
        required=True,
        help="Path to a jejune_doc_* catalog.yaml (repeatable).",
    )
    parser.add_argument(
        "--output_dir",
        default=None,
        metavar="DIR",
        help="Directory for the output file.",
    )
    parser.add_argument(
        "--output",
        default=None,
        metavar="OUTPUT_JSON",
        help=(
            f"Output filename relative to --output_dir; '-' writes to stdout. "
            f"Defaults to <markdown_stem>_-_{modality}_as_LangChain_document.json "
            f"placed in the markdown file's directory (single --catalog only)."
        ),
    )


def resolve_output_path(args: argparse.Namespace, modality: str) -> Path | None:
    """Return the resolved output Path, or None for stdout."""
    if args.output == "-":
        return None
    if args.output is None and len(args.catalog) > 1:
        sys.exit(
            "ERROR: --output is required when multiple --catalog arguments are provided."
        )
    if args.output is not None:
        base = Path(args.output_dir) if args.output_dir else Path(".")
        return base / args.output
    manifest, doc_dir = load_manifest(args.catalog[0])
    md_file = doc_dir / manifest["markdown_file"]
    filename = f"{md_file.stem}_-_{modality}_as_LangChain_document.json"
    out_dir = Path(args.output_dir) if args.output_dir else md_file.parent
    return out_dir / filename


def process_manifest(
    manifest_path: str, split_fn, exclude_blockquotes: bool = False
) -> list[dict]:
    """Load one manifest and run split_fn on its markdown file."""
    manifest, doc_dir = load_manifest(manifest_path)
    markdown_file = doc_dir / manifest["markdown_file"]
    metadata_base = {
        "jejune_source_name": markdown_file.name,
        "jejune_source_slug": manifest["slug"],
    }
    return split_fn(
        markdown_file.read_text(encoding="utf-8"), metadata_base, exclude_blockquotes
    )


def write_output(chunks: list[dict], output_path: Path | None) -> None:
    text = json.dumps(chunks, indent=4, ensure_ascii=False)
    if output_path is None:
        print(text)
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")


def run(split_fn, modality: str, description: str) -> None:
    """Parse arguments, run split_fn over all catalogs, write output."""
    parser = argparse.ArgumentParser(description=description)
    add_common_arguments(parser, modality)
    args = parser.parse_args()
    output_path = resolve_output_path(args, modality)
    chunks = []
    for manifest_path in args.catalog:
        chunks.extend(
            process_manifest(manifest_path, split_fn, args.exclude_blockquotes)
        )
    write_output(chunks, output_path)
