from __future__ import annotations

import sys
from collections import defaultdict
from dataclasses import dataclass
import logging
from typing import TYPE_CHECKING, Mapping, Sequence

from rich._ratio import ratio_resolve

from ..geometry import Region, Point
from ..layout import Layout, MapRegion
from .._types import Lines

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


if TYPE_CHECKING:
    from ..widget import Widget

log = logging.getLogger("rich")


DockEdge = Literal["top", "right", "bottom", "left"]


@dataclass
class DockOptions:
    size: int | None = None
    fraction: int = 1
    minimum_size: int = 1

    @property
    def ratio(self) -> int:
        return self.fraction


@dataclass
class Dock:
    edge: DockEdge
    widgets: Sequence[Widget]
    z: int = 0


class DockLayout(Layout):
    def __init__(self, docks: list[Dock] = None) -> None:
        self.docks: list[Dock] = docks or []
        super().__init__()

    def generate_map(
        self, width: int, height: int, offset: Point = Point(0, 0)
    ) -> dict[Widget, MapRegion]:
        from ..view import View

        map: dict[Widget, MapRegion] = {}

        layout_region = Region(0, 0, width, height)
        layers: dict[int, Region] = defaultdict(lambda: layout_region)

        def add_widget(widget: Widget, region: Region, order: tuple[int, int]):
            region = region + offset + widget.layout_offset
            map[widget] = MapRegion(region, order)
            if isinstance(widget, View):
                sub_map = widget.layout.generate_map(
                    region.width, region.height, offset=region.origin
                )
                map.update(sub_map)

        for index, dock in enumerate(self.docks):
            dock_options = [
                DockOptions(
                    widget.layout_size,
                    widget.layout_fraction,
                    widget.layout_minimim_size,
                )
                for widget in dock.widgets
            ]
            region = layers[dock.z]
            if not region:
                # No space left
                continue

            order = (dock.z, index)
            x, y, width, height = region

            if dock.edge == "top":
                sizes = ratio_resolve(height, dock_options)
                render_y = y
                remaining = region.height
                total = 0
                for widget, size in zip(dock.widgets, sizes):
                    if not widget.visible:
                        continue
                    size = min(remaining, size)
                    if not size:
                        break
                    total += size
                    add_widget(widget, Region(x, render_y, width, size), order)
                    render_y += size
                    remaining = max(0, remaining - size)
                region = Region(x, y + total, width, height - total)

            elif dock.edge == "bottom":
                sizes = ratio_resolve(height, dock_options)
                render_y = y + height
                remaining = region.height
                total = 0
                for widget, size in zip(dock.widgets, sizes):
                    if not widget.visible:
                        continue
                    size = min(remaining, size)
                    if not size:
                        break
                    total += size
                    add_widget(widget, Region(x, render_y - size, width, size), order)
                    render_y -= size
                    remaining = max(0, remaining - size)
                region = Region(x, y, width, height - total)

            elif dock.edge == "left":
                sizes = ratio_resolve(width, dock_options)
                render_x = x
                remaining = region.width
                total = 0
                for widget, size in zip(dock.widgets, sizes):
                    if not widget.visible:
                        continue
                    size = min(remaining, size)
                    if not size:
                        break
                    total += size
                    add_widget(widget, Region(render_x, y, size, height), order)
                    render_x += size
                    remaining = max(0, remaining - size)
                region = Region(x + total, y, width - total, height)

            elif dock.edge == "right":
                sizes = ratio_resolve(width, dock_options)
                render_x = x + width
                remaining = region.width
                total = 0
                for widget, size in zip(dock.widgets, sizes):
                    if not widget.visible:
                        continue
                    size = min(remaining, size)
                    if not size:
                        break
                    total += size
                    add_widget(widget, Region(render_x - size, y, size, height), order)
                    render_x -= size
                    remaining = max(0, remaining - size)
                region = Region(x, y, width - total, height)

            layers[dock.z] = region

        return map
