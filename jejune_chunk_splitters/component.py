"""chunk-splitters containerized component (plugin)."""

from pathlib import Path

import click

from jejune_cli.component_containerized import ContComp


class CompChunkSplitters(ContComp):
    SPLITTERS = {
        "headers": "split_by_headers.py",
        "paragraphs": "split_by_paragraphs.py",
        "sentences": "split_by_sentences.py",
    }

    def __init__(self) -> None:
        super().__init__(
            name="chunk-splitters",
            image_name="jejune:chunk_splitters",
            hint="run `jejune chunk-splitters build`",
        )
        # cli_name intentionally not set: help display is via target_role in PluginDescription

    def check(self) -> tuple[str, str]:
        return ("ok", "") if self.is_built() else ("warn", "image not built")

    def build(self, no_cache: bool = False) -> None:
        if not self.build_context:
            self.build_context = self._context.git_server.remote_git_url(
                "jejune_chunk_splitters", ":DockerContext"
            )
        super().build(no_cache)

    @staticmethod
    def _repo_name(doc_dir: Path) -> str:
        return doc_dir.name.removeprefix("jejune_doc_")

    def run_split(
        self,
        doc_dir: str | Path,
        splitter: str,
        output: str | None,
        no_cache: bool,
        extra_args: tuple,
    ) -> None:
        doc_dir = Path(doc_dir).resolve()
        repo_name = self._repo_name(doc_dir)
        self.build(no_cache)
        output_args = ("--output", output) if output is not None else ()
        click.echo(f"Splitting with {self.SPLITTERS[splitter]} ...")
        self._context.docker.run_foreground(
            f"jejune_split_{repo_name}",
            self.image_name,
            f"{doc_dir}:/data",
            self.SPLITTERS[splitter],
            "--catalog",
            "/data/manifest.yaml",
            *output_args,
            *extra_args,
        )
