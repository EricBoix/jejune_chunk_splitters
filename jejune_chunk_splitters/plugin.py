"""jejune plugin entry point for chunk-splitters."""

from jejune_cli.plugin_description import PluginDescription

from .component_cont_chunk_splitters import CompChunkSplitters
from .commands import chunk_splitters_group


def _check_availability(component: CompChunkSplitters) -> tuple[bool, str]:
    built = component.is_built()
    return built, "" if built else "image not built"


plugin = PluginDescription(
    name="chunk-splitters",
    group=chunk_splitters_group,
    check_availability=_check_availability,
    target_role="doc-steward",
    component_factory=CompChunkSplitters,
)
