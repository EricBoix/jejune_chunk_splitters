"""The splitters read the page markers that pdf-to-markdown writes."""

import sys
import types
from pathlib import Path

import pytest

# The splitter scripts live next to the tests' directory, not in a package
sys.path.insert(0, str(Path(__file__).parent.parent))
# yaml is only needed to read a manifest (not by the split functions)
sys.modules.setdefault("yaml", types.ModuleType("yaml"))

import split_by_headers
import split_by_paragraphs
import split_by_sentences
from _page_markers import PageMarkers

MARKDOWN = """\
<!-- page reader=iv pdf=4 -->

## Chapter

First paragraph. <!-- page reader=v pdf=5 --> Second sentence.

<!-- page reader=6 pdf=6 -->

> A quote.
"""

BASE = {"jejune_source_name": "book.md"}


def _pages(chunks):
    return [
        (chunk["page_content"], chunk["metadata"].get("page"), chunk["metadata"].get("pdf_page"))
        for chunk in chunks
    ]


class TestPageMarkers:
    def test_block_that_is_a_marker(self):
        assert PageMarkers.parse_block("<!-- page reader=iv pdf=4 -->\n") == {
            "page": "iv",
            "pdf_page": 4,
        }

    def test_numeric_printed_page_is_an_integer(self):
        assert PageMarkers.parse_block("<!-- page reader=12 pdf=13 -->")["page"] == 12

    def test_percent_encoded_printed_page_is_decoded(self):
        assert PageMarkers.parse_block("<!-- page reader=a%20b pdf=1 -->")["page"] == "a b"

    def test_other_comments_are_not_markers(self):
        assert PageMarkers.parse_block("<!-- Converter note: picture removed -->") is None

    def test_inline_markers_are_stripped_with_the_space_that_glues_them(self):
        text, markers = PageMarkers.strip_inline(
            "One. <!-- page reader=v pdf=5 --> Two. <!-- page reader=6 pdf=6 --> Three."
        )
        assert text == "One. Two. Three."
        assert markers == [
            (4, {"page": "v", "pdf_page": 5}),
            (9, {"page": 6, "pdf_page": 6}),
        ]

    def test_html_comments_are_stripped_from_a_header_title(self):
        title = "Reflect.<!-- markdownlint-disable-line MD026 -->"
        assert PageMarkers.strip_comments(title) == "Reflect."


class TestSplitters:
    def test_sentences_carry_the_page_where_they_start(self):
        assert _pages(split_by_sentences.split(MARKDOWN, BASE)) == [
            ("First paragraph.", "iv", 4),
            ("Second sentence.", "v", 5),
            ("A quote.", 6, 6),
        ]

    def test_paragraphs_carry_the_page_where_they_start_without_markers(self):
        assert _pages(split_by_paragraphs.split(MARKDOWN, BASE)) == [
            ("First paragraph. Second sentence.", "iv", 4),
            ("A quote.", 6, 6),
        ]

    def test_section_carries_the_page_of_its_header(self):
        assert _pages(split_by_headers.split(MARKDOWN, BASE)) == [
            ("First paragraph. Second sentence.\n\nA quote.", "iv", 4),
        ]

    def test_markdown_without_markers_gives_chunks_without_pages(self):
        for splitter in (split_by_sentences, split_by_paragraphs, split_by_headers):
            for chunk in splitter.split("## Title\n\nOne. Two.\n", BASE):
                assert "page" not in chunk["metadata"]
                assert "pdf_page" not in chunk["metadata"]

    def test_marker_inside_an_excluded_blockquote_still_changes_the_page(self):
        markdown = (
            "<!-- page reader=iv pdf=4 -->\n\n"
            "Before.\n\n"
            "> Quote. <!-- page reader=v pdf=5 --> More quote.\n\n"
            "After.\n"
        )
        chunks = split_by_paragraphs.split(markdown, BASE, exclude_blockquotes=True)
        assert _pages(chunks) == [("Before.", "iv", 4), ("After.", "v", 5)]

    def test_marker_inside_a_numbered_list_is_seen(self):
        markdown = (
            "<!-- page reader=iv pdf=4 -->\n\n"
            "1. First item.\n\n"
            "   <!-- page reader=v pdf=5 -->\n\n"
            "2. Second item.\n"
        )
        chunks = split_by_paragraphs.split(markdown, BASE)
        assert _pages(chunks) == [("First item.", "iv", 4), ("Second item.", "v", 5)]

    def test_title_of_a_header_loses_its_html_comments(self):
        chunks = split_by_paragraphs.split(
            "## Reflect.<!-- markdownlint-disable-line MD026 -->\n\nText.\n", BASE
        )
        assert chunks[0]["metadata"]["h2"] == "Reflect."

    def test_page_markers_never_reach_the_text_of_a_chunk(self):
        for splitter in (split_by_sentences, split_by_paragraphs, split_by_headers):
            for chunk in splitter.split(MARKDOWN, BASE):
                assert "<!--" not in chunk["page_content"]


INLINE_TEXT = (
    "<!-- page reader=iv pdf=4 -->\n\n"
    "First sentence. <!-- page reader=v pdf=5 --> Second sentence.\n"
)
OWN_LINE_TEXT = (
    "<!-- page reader=iv pdf=4 -->\n\n"
    "First sentence.\n<!-- page reader=v pdf=5 -->\nSecond sentence.\n"
)


@pytest.mark.parametrize("module", [split_by_paragraphs, split_by_sentences])
def test_a_marker_on_its_own_line_gives_the_chunks_of_the_inline_marker(module):
    assert module.split(OWN_LINE_TEXT, {}) == module.split(INLINE_TEXT, {})


def test_own_line_marker_in_a_blockquote_and_a_list_item_is_joined():
    quote = "> One.\n> <!-- page reader=2 pdf=3 -->\n> Two.\n"
    item = "1. One.\n   <!-- page reader=2 pdf=3 -->\n   Two.\n"
    assert PageMarkers.join_own_line(quote) == "> One. <!-- page reader=2 pdf=3 --> Two.\n"
    assert PageMarkers.join_own_line(item) == "1. One. <!-- page reader=2 pdf=3 --> Two.\n"


def test_a_marker_between_blocks_is_left_alone():
    text = "One.\n\n<!-- page reader=2 pdf=3 -->\n\nTwo.\n"
    assert PageMarkers.join_own_line(text) == text
