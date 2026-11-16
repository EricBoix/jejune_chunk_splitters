"""Split a markdown document into one JSON chunk per sentence.

Paragraph structure is resolved with markdown-it-py (same approach as the other
splitters). Sentence boundary detection uses nltk.sent_tokenize, replicating the
algorithm from pdf_to_markdown/MarkdownToDocument.py without importing that package.

Each sentence carries header hierarchy (h1/h2/h3), paragraph_number (reset on
any header change), and sentence_number (1-based within the paragraph).

A paragraph that belongs to a markdown blockquote ("> ...") is a paragraph like
the others, its sentences being flagged with is_blockquote. With
exclude_blockquotes it produces no chunk and does not consume a paragraph_number.
"""
import nltk
from markdown_it import MarkdownIt

from _splitter_common import blockquote_depth_change, run

_MODALITY = "Sentences"

for _resource in ("punkt", "punkt_tab"):
    try:
        nltk.data.find(f"tokenizers/{_resource}")
    except LookupError:
        nltk.download(_resource, quiet=True)


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
            for sent_number, sentence in enumerate(
                nltk.sent_tokenize(tokens[i + 1].content), 1
            ):
                meta = {**metadata_base, **{f"h{k}": v for k, v in headers.items()},
                        "paragraph_number": para_number,
                        "sentence_number": sent_number,
                        "is_blockquote": is_blockquote}
                chunks.append({"__document__": True, "metadata": meta,
                                "page_content": sentence})
            i += 3
        else:
            i += 1

    return chunks


if __name__ == "__main__":
    run(split, _MODALITY, "Split markdown by sentence into LangChain Document JSON.")
