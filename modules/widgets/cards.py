import tkinter as tk

from modules.renderer import SmoothRenderer
from modules.theme import M3Blue


class M3SurfaceCard(tk.Canvas):
    def __init__(
        self,
        parent,
        bg_parent: str = M3Blue.SURFACE,
        fill_color: str = M3Blue.SURFACE_CONTAINER,
        outline_color: str | None = M3Blue.OUTLINE,
        radius: int = 20,
        padx: int = 16,
        pady: int = 12,
        expand_v: bool = False,
        fixed_height: int | None = None,
    ):
        init_h = fixed_height if fixed_height else 48
        super().__init__(parent, bg=bg_parent, height=init_h, highlightthickness=0, bd=0)
        self.fill_color = fill_color
        self.outline_color = outline_color
        self.radius = radius
        self.padx = padx
        self.pady = pady
        self.expand_v = expand_v
        self.fixed_height = fixed_height
        self._last_size = (0, 0)

        self.inner = tk.Frame(self, bg=fill_color)
        self.win_id = self.create_window(padx, pady, window=self.inner, anchor="nw")

        self.inner.bind("<Configure>", self._on_inner_configure)
        self.bind("<Configure>", self._on_canvas_configure)

    def _on_inner_configure(self, _=None):
        if not self.expand_v:
            target_h = self.fixed_height if self.fixed_height else (self.inner.winfo_reqheight() + self.pady * 2)
            if abs(self.winfo_height() - target_h) > 2:
                self.configure(height=target_h)

    def _on_canvas_configure(self, event):
        w = event.width
        if not self.expand_v:
            h = self.fixed_height if self.fixed_height else (self.inner.winfo_reqheight() + self.pady * 2)
            if abs(event.height - h) > 2:
                self.configure(height=h)
        else:
            h = event.height

        if w < 16 or h < 16 or (w, h) == self._last_size:
            return
        self._last_size = (w, h)

        self.itemconfigure(
            self.win_id,
            width=max(1, w - self.padx * 2),
            height=max(1, h - self.pady * 2),
        )
        self._draw_9slice(w, h)

    def _draw_9slice(self, w: int, h: int):
        self.delete("card_bg")
        r = min(self.radius, w // 2, h // 2)
        nw, ne, sw, se = SmoothRenderer.get_9slice_corners(r, self.fill_color, self.outline_color, 1)

        self.create_rectangle(r, 0, w - r, h, fill=self.fill_color, outline="", tags="card_bg")
        self.create_rectangle(0, r, r, h - r, fill=self.fill_color, outline="", tags="card_bg")
        self.create_rectangle(w - r, r, w, h - r, fill=self.fill_color, outline="", tags="card_bg")

        self.create_image(0, 0, image=nw, anchor="nw", tags="card_bg")
        self.create_image(w - r, 0, image=ne, anchor="nw", tags="card_bg")
        self.create_image(0, h - r, image=sw, anchor="nw", tags="card_bg")
        self.create_image(w - r, h - r, image=se, anchor="nw", tags="card_bg")

        if self.outline_color:
            self.create_line(r, 0, w - r, 0, fill=self.outline_color, width=1, tags="card_bg")
            self.create_line(r, h - 1, w - r, h - 1, fill=self.outline_color, width=1, tags="card_bg")
            self.create_line(0, r, 0, h - r, fill=self.outline_color, width=1, tags="card_bg")
            self.create_line(w - 1, r, w - 1, h - r, fill=self.outline_color, width=1, tags="card_bg")

        self.tag_lower("card_bg")
