import os
import threading
import tkinter as tk

import requests
from PIL import Image, ImageDraw, ImageSequence, ImageTk

from modules.registry import _CoreRegistry
from modules.renderer import SmoothRenderer
from modules.theme import M3Blue


class M3AuthorGifBadge(tk.Canvas):
    def __init__(self, parent, cache_dir: str, bg_parent: str = M3Blue.TITLEBAR, width: int = 112, height: int = 28):
        super().__init__(parent, bg=bg_parent, width=width, height=height, highlightthickness=0, bd=0)
        self.gif_url = _CoreRegistry.badge_asset_endpoint()
        self.cache_path = os.path.join(cache_dir, "badge_anim.gif")
        self.frames: list[ImageTk.PhotoImage] = []
        self.delays: list[int] = []
        self.frame_idx = 0

        self._pill_img = SmoothRenderer.rounded_box(width, height, height // 2, M3Blue.PRIMARY_CONTAINER, M3Blue.PRIMARY, 1)
        self.create_image(0, 0, image=self._pill_img, anchor="nw")
        self.gif_item = self.create_image(16, height // 2, anchor="center")
        self.create_text(29, height // 2, text="by antoshika", anchor="w", fill=M3Blue.PRIMARY, font=("Segoe UI Semibold", 8))

        threading.Thread(target=self._fetch_gif, daemon=True).start()

    def _fetch_gif(self):
        try:
            if not os.path.exists(self.cache_path):
                r = requests.get(self.gif_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                if r.status_code == 200 and len(r.content) > 100:
                    with open(self.cache_path, "wb") as f:
                        f.write(r.content)

            if os.path.exists(self.cache_path):
                pil_gif = Image.open(self.cache_path)
                size = 20
                scale = 4
                mask = Image.new("L", (size * scale, size * scale), 0)
                ImageDraw.Draw(mask).ellipse([0, 0, size * scale - 1, size * scale - 1], fill=255)
                mask = mask.resize((size, size), Image.Resampling.LANCZOS)

                raw_frames = []
                delays = []
                for frame in ImageSequence.Iterator(pil_gif):
                    dur = frame.info.get("duration", 70)
                    delays.append(max(30, int(dur)))
                    rgba = frame.convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)
                    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
                    out.paste(rgba, (0, 0), mask)
                    raw_frames.append(out)
                    if len(raw_frames) >= 60:
                        break

                if raw_frames:
                    self.after(0, self._init_tk_frames, raw_frames, delays)
        except (requests.RequestException, OSError, ValueError, Image.DecompressionBombError):
            pass

    def _init_tk_frames(self, raw_frames, delays):
        self.frames = [ImageTk.PhotoImage(f) for f in raw_frames]
        self.delays = delays
        self._animate()

    def _animate(self):
        if not self.frames:
            return
        self.itemconfigure(self.gif_item, image=self.frames[self.frame_idx])
        delay = self.delays[self.frame_idx]
        self.frame_idx = (self.frame_idx + 1) % len(self.frames)
        self.after(delay, self._animate)


class M3ProgressBar(tk.Canvas):
    def __init__(
        self,
        parent,
        bg_parent: str = M3Blue.PRIMARY_CONTAINER,
        track_color: str = M3Blue.SURFACE_CONTAINER_LOW,
        bar_color: str = M3Blue.PRIMARY,
        height: int = 8,
    ):
        super().__init__(parent, bg=bg_parent, height=height, highlightthickness=0, bd=0)
        self.track_color = track_color
        self.bar_color = bar_color
        self.progress = 0.0
        self.bind("<Configure>", lambda e: self._redraw())

    def set_progress(self, value: float):
        self.progress = max(0.0, min(100.0, float(value)))
        self._redraw()

    def _redraw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 12 or h < 4:
            return
        r = h // 2
        self.create_line(r, r, w - r, r, fill=self.track_color, width=h, capstyle=tk.ROUND)
        if self.progress > 0:
            fill_w = max(h, int(w * (self.progress / 100.0)))
            self.create_line(r, r, fill_w - r, r, fill=self.bar_color, width=h, capstyle=tk.ROUND)


class M3StatusPill(tk.Canvas):
    def __init__(
        self,
        parent,
        text: str,
        bg_parent: str = M3Blue.SURFACE,
        fill_color: str = M3Blue.SURFACE_CONTAINER,
        fg_color: str = M3Blue.ON_SURFACE_VARIANT,
        width: int = 265,
        height: int = 34,
    ):
        super().__init__(parent, bg=bg_parent, width=width, height=height, highlightthickness=0, bd=0)
        self.text = text
        self.fill_color = fill_color
        self.fg_color = fg_color
        self._img = None
        self.bind("<Configure>", lambda e: self._redraw())

    def set_state(self, text: str, fg_color: str, fill_color: str | None = None):
        self.text = text
        self.fg_color = fg_color
        if fill_color:
            self.fill_color = fill_color
        self._redraw()

    def _redraw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 10 or h < 10:
            return
        self._img = SmoothRenderer.rounded_box(w, h, h // 2, self.fill_color, M3Blue.OUTLINE, 1, "dot", self.fg_color, 18)
        self.create_image(0, 0, image=self._img, anchor="nw")
        self.create_text(w // 2 + 8, h // 2, text=self.text, fill=self.fg_color, font=("Segoe UI Semibold", 9))
