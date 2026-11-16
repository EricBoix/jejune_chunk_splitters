"""Split a markdown document into one JSON chunk per paragraph.

Each paragraph inherits the enclosing header hierarchy (h1/h2/h3) as metadata,
along with a paragraph_number that is reset to 1 each time any header changes.

A paragraph that belongs to a markdown blockquote ("> ...") is a paragraph like
the others, flagged with is_blockquote. With exclude_blockquotes it produces no
chunk and does not consume a paragraph_number.
"""
from markdown_it import MarkdownIt

from _splitter_common import blockquote_depth_change, run

_MODALITY = "Paragraphs"


def split(markdown_text: str, metadata_base: dict,
          exclude_blockquotes: bool = False) -> list[dict]:
    tokens = MarkdownIt().parse(markdown_text)
    chunks = []
    headers: dict[int, str] = {}
    para_number = 0
    blockquote_depth = 0

    i = 0
    while i < len(tokens):
        tok = tokens[i]
        blockquote_depth += blockquote_depth_change(tok.type)
        if tok.type == "heading_open":
            level = int(tok.tag[1])
            headers[level] = tokens[i + 1].content
            for deeper in [k for k in headers if k > level]:
                del headers[deeper]
            para_number = 0
            i += 3
        elif tok.type == "paragraph_open":
            is_blockquote = blockquote_depth > 0
            if is_blockquote and exclude_blockquotes:
                i += 3
                continue
            para_number += 1
            meta = {**metadata_base, **{f"h{k}": v for k, v in headers.items()},
                    "paragraph_number": para_number,
                    "is_blockquote": is_blockquote}
            chunks.append({"__document__": True, "metadata": meta,
                            "page_content": tokens[i + 1].content})
            i += 3
        else:
            i += 1

    return chunks


if __name__ == "__main__":
    run(split, _MODALITY, "Split markdown by paragraph into LangChain Document JSON.")
