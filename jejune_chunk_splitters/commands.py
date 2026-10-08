"""Click command group for the chunk-splitters plugin."""

import click

from .component import CompChunkSplitters


@click.group("chunk-splitters", short_help="Split documents into JSON chunks")
@click.pass_context
def chunk_splitters_group(ctx):
    """Split a jejune_doc_<name> catalog into JSON chunks for knowledge-graph extraction."""
    from jejune_cli.app_context import AppContext
    ctx.obj = ctx.find_object(AppContext).component_registry.get("chunk-splitters")


@chunk_splitters_group.command("build")
@click.option(
    "--no-cache",
    is_flag=True,
    default=False,
    help="Do not use Docker layer cache when building.",
)
@click.pass_obj
def chunk_splitters_build(comp, no_cache: bool):
    """Build the chunk-splitters Docker image."""
    comp.build(no_cache=no_cache)


@chunk_splitters_group.command("split", context_settings={"ignore_unknown_options": True})
@click.argument("doc_dir", default=".", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--splitter",
    type=click.Choice(list(CompChunkSplitters.SPLITTERS)),
    default="headers",
    show_default=True,
    help="Splitting strategy.",
)
@click.option(
    "--output",
    default=None,
    help="Output JSON path inside the container. Defaults to the splitter's own naming scheme.",
)
@click.option(
    "--no-cache",
    is_flag=True,
    default=False,
    help="Do not use Docker layer cache when building.",
)
@click.argument("extra_args", nargs=-1, type=click.UNPROCESSED)
@click.pass_obj
def split(comp, doc_dir, splitter, output, no_cache, extra_args):
    """Split DOC_DIR's catalog into JSON chunks.

    Builds the chunk-splitters Docker image and runs the chosen splitter script
    against /data/manifest.yaml. Without --output the splitter writes a file
    named after the markdown source and the splitting modality.

    EXTRA_ARGS are forwarded verbatim to the splitter (e.g. --output_dir /data).
    """
    comp.run_split(doc_dir, splitter, output, no_cache, extra_args)


@chunk_splitters_group.command("check-availability")
@click.pass_obj
def check_availability(comp):
    """Show chunk-splitters image build status."""
    built = comp.is_built()
    status = click.style("built", fg="green") if built else click.style("not built", fg="yellow")
    click.echo(f"  image   {comp.image_name}")
    click.echo(f"  status  {status}")


@chunk_splitters_group.command("status-availability")
@click.pass_obj
def status_availability(comp):
    """Show chunk-splitters availability status."""
    built = comp.is_built()
    if built:
        click.echo(f"chunk-splitters: {click.style('ok', fg='green')}")
    else:
        click.echo(f"chunk-splitters: {click.style('warn', fg='yellow')}")


@chunk_splitters_group.command("hint-availability")
@click.pass_obj
def hint_availability(comp):
    """Show how to prepare the chunk-splitters image if it is not built."""
    if comp.is_built():
        click.echo(click.style("chunk-splitters image is built", fg="green"))
    else:
        click.echo("run `jejune chunk-splitters build`")
