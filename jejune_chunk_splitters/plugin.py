"""jejune plugin entry point for chunk-splitters."""

from jejune_cli.plugin_description import PluginDescription

from .component import CompChunkSplitters
from .commands import chunk_splitters_group

_component = CompChunkSplitters()


def _check_availability() -> tuple[bool, str]:
    built = _component.is_built()
    return built, "" if built else "image not built"


plugin = PluginDescription(
    name="chunk-splitters",
    group=chunk_splitters_group,
    check_availability=_check_availability,
    target_role="doc-steward",
    component=_component,
)
