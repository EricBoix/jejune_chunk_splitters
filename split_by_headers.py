"""Split a markdown document into one JSON chunk per header section.

Each chunk's page_content is the concatenated text of all paragraphs inside
one header section. Header hierarchy (h1/h2/h3) is tracked in metadata and
reset when a heading of equal or higher level is encountered.
Headers inside fenced code blocks are ignored (they appear as 'fence' tokens,
not 'heading_open' tokens in the markdown-it token stream).

The paragraphs of a markdown blockquote ("> ...") are paragraphs like the others
(a section chunk does not tell them apart). With exclude_blockquotes they are
left out of the section text.

When the markdown holds page markers (see _page_markers.py) each section also
carries the page where it starts (the one of its header), as the page and
pdf_page metadata. The page markers are not part of page_content.
"""
from markdown_it import MarkdownIt

from _page_markers import PageMarkers, PageTracker
from _splitter_common import blockquote_depth_change, run

_MODALITY = "Headers"


def split(markdown_text: str, metadata_base: dict,
          exclude_blockquotes: bool = False) -> list[dict]:
    tokens = MarkdownIt().parse(PageMarkers.join_own_line(markdown_text))
    chunks = []
    headers: dict[int, str] = {}
    paragraphs: list[str] = []
    blockquote_depth = 0
    pages = PageTracker()
    # The page where the section starts: the one of its header (or, for the
    # text standing before the first header, the one of its first paragraph)
    section_page: dict | None = None

    def flush() -> None:
        nonlocal section_page
        if not paragraphs:
            return
        meta = {**metadata_base, **{f"h{k}": v for k, v in headers.items()},
                **(section_page or {})}
        chunks.append({"__document__": True, "metadata": meta,
                        "page_content": "\n\n".join(paragraphs)})
        paragraphs.clear()
        section_page = None

    i = 0
    while i < len(tokens):
        tok = tokens[i]
        blockquote_depth += blockquote_depth_change(tok.type)
        if tok.type == "html_block":
            pages.observe(tok)
            i += 1
        elif tok.type == "heading_open":
            flush()
            level = int(tok.tag[1])
            headers[level] = PageMarkers.strip_comments(tokens[i + 1].content)
            for deeper in [k for k in headers if k > level]:
                del headers[deeper]
            section_page = dict(pages.page)
            i += 3
        elif tok.type == "paragraph_open":
            # The markers of an excluded blockquote still change the page
            paragraph = pages.read_paragraph(tokens[i + 1].content)
            if section_page is None:
                section_page = paragraph.start_page
            if not (exclude_blockquotes and blockquote_depth > 0):
                paragraphs.append(paragraph.text)
            i += 3
        else:
            i += 1

    flush()
    return chunks


if __name__ == "__main__":
    run(split, _MODALITY, "Split markdown by header sections into LangChain Document JSON.")
