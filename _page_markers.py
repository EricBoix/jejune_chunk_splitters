"""Page markers of the markdown that pdf-to-markdown writes.

A page marker is an html comment, e.g.

    <!-- page reader=iv pdf=4 -->

that stands before the first text of a page (see PageMarker in the
pdf-to-markdown package, that writes it):

- reader is the number printed on the page (percent encoded): an integer, or
  whatever the book prints ("Cover", a roman numeral...);
- pdf is the page as a PDF viewer numbers it: the first page is 1.

Between two blocks (paragraphs, tables, headings, headers) the marker is a block
of its own (an 'html_block' token of markdown-it). Within a paragraph it stands
inline, glued by a single space to the end of the previous sentence: removing
" <marker>" gives back the text of the paragraph without markers. A sentence
belongs to the page where it starts.

pdf-to-markdown can instead write the marker within a paragraph on a line of its
own (a single newline on both sides, in a blockquote or a list item after the
prefix or indentation of the line): join_own_line turns it back into the inline
form before the markdown is parsed, so that the paragraph is not cut in two.

The chunks carry the page as the "page" (reader) and "pdf_page" metadata. A
markdown without markers gives chunks without them.
"""
import re
from dataclasses import dataclass, field
from urllib.parse import unquote


class PageMarkers:
    """Reading the page markers of a markdown text."""

    PATTERN = re.compile(r"<!-- page reader=(?P<reader>\S+) pdf=(?P<pdf>\d+) -->")
    # Inline, the marker is glued to the previous sentence by a single space
    INLINE = re.compile(r" ?" + PATTERN.pattern)
    HTML_COMMENT = re.compile(r"\s*<!--.*?-->")
    # A marker alone on a line, with text on the line before and the line after
    # (their blockquote prefix or list indentation is dropped with the newlines)
    OWN_LINE = re.compile(
        r"(?<=\S)[ \t]*\n[ >\t]*(" + PATTERN.pattern + r")[ \t]*\n[ >\t]*(?=\S)"
    )

    @classmethod
    def join_own_line(cls, markdown_text: str) -> str:
        """The markdown with the markers that stand on a line of their own
        within a paragraph written inline (as between two sentences)."""
        return cls.OWN_LINE.sub(r" \1 ", markdown_text)

    @classmethod
    def metadata_of(cls, match: re.Match) -> dict:
        reader = unquote(match.group("reader"))
        return {
            "page": int(reader) if reader.isdigit() else reader,
            "pdf_page": int(match.group("pdf")),
        }

    @classmethod
    def parse_block(cls, text: str) -> dict | None:
        """The page of a block that is a marker, None for any other text."""
        match = cls.PATTERN.fullmatch(text.strip())
        return cls.metadata_of(match) if match else None

    @classmethod
    def strip_inline(cls, text: str) -> tuple[str, list[tuple[int, dict]]]:
        """The text without its inline markers, and for each marker the offset
        (in the text without markers) from which its page is the one."""
        parts = []
        markers = []
        position = 0
        length = 0
        for match in cls.INLINE.finditer(text):
            parts.append(text[position : match.start()])
            length += match.start() - position
            markers.append((length, cls.metadata_of(match)))
            position = match.end()
        parts.append(text[position:])
        return "".join(parts), markers

    @classmethod
    def strip_comments(cls, text: str) -> str:
        """The text without any html comment (e.g. in the title of a header the
        markdownlint comment that pdf-to-markdown may append)."""
        return cls.HTML_COMMENT.sub("", text)


@dataclass
class ParagraphPages:
    """A paragraph without its markers, and the pages that its text goes over."""

    text: str
    start_page: dict
    markers: list[tuple[int, dict]] = field(default_factory=list)

    def page_at(self, offset: int) -> dict:
        """The page of the text that starts at the given offset of the text."""
        page = self.start_page
        for marker_offset, marker_page in self.markers:
            if marker_offset > offset:
                break
            page = marker_page
        return page


class PageTracker:
    """The page of the text read last, while the tokens of a markdown go by."""

    def __init__(self) -> None:
        self.page: dict = {}

    def observe(self, token) -> None:
        """A markdown-it token: a block that is a marker changes the page."""
        if token.type != "html_block":
            return
        page = PageMarkers.parse_block(token.content)
        if page is not None:
            self.page = page

    def read_paragraph(self, content: str) -> ParagraphPages:
        """A paragraph (the content of its inline token), read from the page
        that the previous text left off."""
        text, markers = PageMarkers.strip_inline(content)
        paragraph = ParagraphPages(text, dict(self.page), markers)
        if markers:
            self.page = markers[-1][1]
        return paragraph
