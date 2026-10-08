# jejune\_chunk\_splitters<!-- omit in toc -->

## Table of contents<!-- omit in toc -->

- [Introduction](#introduction)
- [Running with jejune CLI](#running-with-jejune-cli)
- [Running with Docker](#running-with-docker)
- [Running standalone](#running-standalone)
- [Splitting strategies](#splitting-strategies)
- [Next step: knowledge-graph extraction](#next-step-knowledge-graph-extraction)

## Introduction

This repository provides three markdown-to-JSON splitter scripts used to
prepare `jejune_doc_*` documents for knowledge-graph extraction.

Each splitter reads document metadata from a `manifest.yaml` file (located at
the root of a `jejune_doc_*` repository) and writes a JSON file of
[LangChain Documents](https://reference.langchain.com/python/langchain-core/documents)
that can be inspected before feeding them into the graph extractor.

The three available splitting strategies are:

| Script | Granularity |
|--------|-------------|
| `split_by_headers.py` | one chunk per header section (all paragraphs merged) |
| `split_by_paragraphs.py` | one chunk per paragraph |
| `split_by_sentences.py` | one chunk per sentence (`nltk.sent_tokenize`) |

## Running with jejune CLI

Install and configure [`jejune_cli`](https://github.com/EricBoix/jejune_cli),
then build the chunk-splitters Docker image once:

```bash
jejune chunk-splitters build
```

Split a document (the `manifest.yaml` is resolved automatically):

```bash
# Default splitter: headers
jejune chunk-splitters split /path/to/jejune_doc_<name>

# Choose a different strategy
jejune chunk-splitters split /path/to/jejune_doc_<name> --splitter paragraphs
jejune chunk-splitters split /path/to/jejune_doc_<name> --splitter sentences

# Write output to a specific file (path relative to /data inside the container)
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

## Next step: knowledge-graph extraction

Feed the JSON output into
[`jejune_extract_knowledge_graph`](https://github.com/EricBoix/jejune_extract_knowledge_graph)
to build a Neo4j knowledge graph:

```bash
jejune graph extract /path/to/jejune_doc_<name>
```

Requires a running Neo4j instance and a configured LLM — see
[`jejune_cli`](https://github.com/EricBoix/jejune_cli) for setup instructions.
