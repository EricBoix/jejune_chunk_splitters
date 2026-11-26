# jejune\_chunk\_splitters<!-- omit in toc -->

## Table of contents<!-- omit in toc -->

- [Introduction](#introduction)
- [Installation as a jejune-cli plugin](#installation-as-a-jejune-cli-plugin)
- [Usage via jejune CLI](#usage-via-jejune-cli)
- [Running with Docker](#running-with-docker)
- [Running standalone](#running-standalone)
- [Splitting strategies](#splitting-strategies)

## Introduction

This repository is a [`jejune-cli`](https://github.com/EricBoix/jejune_cli)
plugin that extends the **doc-steward role** with chunk-splitting commands.

It provides three markdown-to-JSON splitter scripts used to prepare
`jejune_doc_*` documents for knowledge-graph extraction.  Each splitter reads
document metadata from a `manifest.yaml` file (located at the root of a
`jejune_doc_*` repository) and writes a JSON file of
[LangChain Documents](https://reference.langchain.com/python/langchain-core/documents)
that can be inspected before feeding them into the graph extractor.

The three available splitting strategies are:

| Script | Granularity |
|--------|-------------|
| `split_by_headers.py` | one chunk per header section (all paragraphs merged) |
| `split_by_paragraphs.py` | one chunk per paragraph |
| `split_by_sentences.py` | one chunk per sentence (`nltk.sent_tokenize`) |

## Installation as a jejune-cli plugin

Install `jejune-cli` first, then install this plugin from the repository:

```bash
uv pip install git+https://github.com/EricBoix/jejune_chunk_splitters.git
```

Or in a doc-steward workspace, let `jejune-cli` manage it:

```bash
jejune plugin-packages install
```

Verify the plugin is wired:

```bash
jejune doctor          # chunk-splitters row should appear
jejune chunk-splitters --help
```

## Usage via jejune CLI

Build the chunk-splitters Docker image once:

```bash
jejune chunk-splitters build
```

General form (the `manifest.yaml` is resolved automatically):

```bash
jejune chunk-splitters split <DIR> --splitter [headers|paragraphs|sentences]
```

`<DIR>` defaults to the current working directory, so from inside a
`jejune_doc_<name>` repository these short forms are equivalent:

```bash
jejune chunk-splitters split --splitter headers
jejune chunk-splitters split --splitter paragraphs
jejune chunk-splitters split --splitter sentences
```

`--splitter` itself defaults to `headers`, so the minimal invocation is just:

```bash
jejune chunk-splitters split
```

With an explicit path:

```bash
jejune chunk-splitters split /path/to/jejune_doc_<name> --splitter paragraphs
```

To write the output to a specific file (path relative to `/data` inside the
container):

```bash
jejune chunk-splitters split /path/to/jejune_doc_<name> \
  --splitter headers --output my_chunks.json
```

The output JSON is written beside the markdown file with an auto-generated name
of the form `<markdown_stem>_-_<Modality>_as_LangChain_document.json`.

## Running with Docker

Build the image directly:

```bash
docker build -t jejune:chunk_splitters \
  https://github.com/EricBoix/jejune_chunk_splitters.git#:DockerContext
```

Run a splitter (document directory mounted as `/data`):

```bash
# Headers — auto-named output beside the markdown file
docker run --rm \
  -v /path/to/jejune_doc_<name>:/data \
  jejune:chunk_splitters \
  split_by_headers.py --catalog /data/manifest.yaml

# Sentences — output to a specific file
docker run --rm \
  -v /path/to/jejune_doc_<name>:/data \
  jejune:chunk_splitters \
  split_by_sentences.py \
  --catalog /data/manifest.yaml \
  --output_dir /data \
  --output chunks_sentences.json
```

## Running standalone

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

```bash
git clone https://github.com/EricBoix/jejune_doc_Four_Noble_Truths.git

python split_by_headers.py \
  --catalog jejune_doc_Four_Noble_Truths/manifest.yaml

python split_by_sentences.py \
  --catalog jejune_doc_Four_Noble_Truths/manifest.yaml \
  --output_dir result_data
```

## Splitting strategies

All splitters share these output flags:

| Flag | Meaning |
|------|---------|
| _(none)_ | auto-generate `<markdown_stem>_-_<Modality>_as_LangChain_document.json` beside the markdown file |
| `--output_dir DIR` | place the auto-generated (or named) file in `DIR` instead |
| `--output FILE` | use `FILE` as the filename; relative to `--output_dir` if given |
| `--output -` | write to stdout |

`--catalog` is repeatable to blend multiple documents; `--output` is then
required.

### Markdown blockquotes

A markdown blockquote (`> ...`, e.g. the pull quotes of a book) is split like
any other paragraph. By default blockquotes are kept, and the chunks of the
paragraphs and sentences splitters carry an `is_blockquote` boolean in their
metadata (`true` within a blockquote) so that the consumer can tell them apart.

| Flag | Meaning |
|------|---------|
| `--exclude-blockquotes` | leave the blockquotes out of the chunks. They then do not consume a `paragraph_number` (the numbering counts the remaining paragraphs only). |

Through the jejune CLI the flag is forwarded to the splitter as an extra
argument:

```bash
jejune chunk-splitters split --splitter paragraphs -- --exclude-blockquotes
```

### Page markers

The markdown that `pdf-to-markdown` writes from a PDF can carry page markers,
html comments that stand where a page starts:

```markdown
<!-- page reader=iv pdf=4 -->
```

`reader` is the number printed on the page (an integer, or e.g. `Cover` or a
roman numeral), `pdf` is the page as a PDF viewer numbers it (the first page is
1). Between two blocks the marker is a block of its own; within a paragraph it
stands on a line of its own (a newline before and after, no blank line), or is
glued after the last sentence of the previous page. A sentence belongs to the
page where it starts. The splitters join a marker on its own line back first, so
a paragraph that such a marker interrupts stays one paragraph (same chunks, same
paragraph and sentence numbers as with the glued marker).

When the markdown holds markers every chunk carries the page where it starts:

| Metadata | Meaning |
| --- | --- |
| `page` | the printed page number (an integer when it is one, otherwise the text) |
| `pdf_page` | the page of the PDF, the first page being 1 |

A section chunk (headers splitter) carries the page of its header, a paragraph
chunk the page where the paragraph starts, a sentence chunk its own page. A
markdown without markers gives chunks without these two keys.

The markers are not part of `page_content`: a sentence chunk stays a literal
part of the markdown (which the "Open in Markdown" function of the markdown
browser relies on). A paragraph or a section that goes over a page break is not
a literal part of the markdown anymore, since the marker standing inside it is
removed from its text.

The html comments of a header (e.g. the markdownlint comment that
`pdf-to-markdown` appends to a title ending with a punctuation) are removed from
the `h1`/`h2`/`h3` values.

### Split by header sections

One chunk per markdown section (all paragraphs under a heading merged).
Header hierarchy (`h1`, `h2`, `h3`) is captured in metadata.

```bash
python split_by_headers.py \
  --catalog jejune_doc_Four_Noble_Truths/manifest.yaml
```

### Split by paragraphs

One chunk per paragraph. Metadata includes the enclosing header hierarchy and
a `paragraph_number` (reset at each heading boundary).

```bash
python split_by_paragraphs.py \
  --catalog jejune_doc_Four_Noble_Truths/manifest.yaml \
  --output_dir result_data
```

### Split by sentences

One chunk per sentence using `nltk.sent_tokenize`. Metadata includes header
hierarchy, `paragraph_number`, and `sentence_number` within the paragraph.

```bash
python split_by_sentences.py \
  --catalog jejune_doc_Four_Noble_Truths/manifest.yaml \
  --output_dir result_data
```

### Blending multiple documents

Pass `--catalog` multiple times (requires `--output`):

```bash
python split_by_sentences.py \
  --catalog jejune_doc_Four_Noble_Truths/manifest.yaml \
  --catalog jejune_doc_Rob_Burbea/manifest.yaml \
  --output_dir result_data \
  --output blended_-_Sentences_as_LangChain_document.json
```
