from datetime import datetime
from logging import getLogger

from rich.console import Console, ConsoleOptions, RenderableType
from rich.panel import Panel
from rich.repr import rich_repr, RichReprResult
from rich.style import StyleType
from rich.table import Table
from rich.text import TextType

from .. import events
from ..widget import Widget

log = getLogger("rich")


class Header(Widget):
    def __init__(
        self,
        title: TextType,
        *,
        panel: bool = True,
        style: StyleType = "white on blue",
        clock: bool = True
    ) -> None:
        self.title = title
        self.panel = panel
        self.style = style
        self.clock = clock

        super().__init__()
        self.layout_size = 3

    def __rich_repr__(self) -> RichReprResult:
        yield self.title

    def get_clock(self) -> str:
        return datetime.now().time().strftime("%X")

    def render(self) -> RenderableType:

        header_table = Table.grid(padding=(0, 1), expand=True)
        header_table.style = self.style
        header_table.add_column(justify="left", ratio=0)
        header_table.add_column("title", justify="center", ratio=1)
        if self.clock:
            header_table.add_column("clock", justify="right")
            header_table.add_row("🐞", self.title, self.get_clock())
        else:
            header_table.add_row("🐞", self.title)
        header: RenderableType
        if self.panel:
            header = Panel(header_table, style=self.style)
        else:
            header = header_table
        return header

    async def on_mount(self, event: events.Mount) -> None:
        self.set_interval(1.0, callback=self.refresh)
