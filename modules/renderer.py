from typing import ClassVar

from PIL import Image, ImageDraw, ImageTk

from modules.theme import M3Blue


class SmoothRenderer:
    _box_cache: ClassVar[dict] = {}
    _corner_cache: ClassVar[dict] = {}
    _default_icon: ImageTk.PhotoImage | None = None

    @classmethod
    def get_9slice_corners(
        cls, radius: int, fill: str, outline: str | None = None, outline_w: int = 1
    ) -> tuple[ImageTk.PhotoImage, ImageTk.PhotoImage, ImageTk.PhotoImage, ImageTk.PhotoImage]:
        r = max(4, int(radius))
        key = (r, fill, outline, outline_w)
        if key in cls._corner_cache:
            return cls._corner_cache[key]

        scale = 4
        sr = r * scale
        size = sr * 2
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        ow = outline_w * scale if outline else 0
        draw.rounded_rectangle(
            [ow, ow, size - 1 - ow, size - 1 - ow],
            radius=sr,
            fill=fill,
            outline=outline if outline else None,
            width=ow,
        )
        smooth = img.resize((r * 2, r * 2), Image.Resampling.LANCZOS)

        nw = ImageTk.PhotoImage(smooth.crop((0, 0, r, r)))
        ne = ImageTk.PhotoImage(smooth.crop((r, 0, r * 2, r)))
        sw = ImageTk.PhotoImage(smooth.crop((0, r, r, r * 2)))
        se = ImageTk.PhotoImage(smooth.crop((r, r, r * 2, r * 2)))

        corners = (nw, ne, sw, se)
        cls._corner_cache[key] = corners
        return corners

    @classmethod
    def rounded_box(
        cls,
        w: int,
        h: int,
        radius: int,
        fill: str,
        outline: str | None = None,
        outline_w: int = 1,
        icon_type: str | None = None,
        icon_color: str | None = None,
        icon_x: int = 24,
    ) -> ImageTk.PhotoImage:
        w, h = max(4, int(w)), max(4, int(h))
        key = (w, h, radius, fill, outline, outline_w, icon_type, icon_color, icon_x)
        if key in cls._box_cache:
            return cls._box_cache[key]

        scale = 4
        sw, sh = w * scale, h * scale
        sr = max(0, min(radius * scale, sw // 2, sh // 2))

        img = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img, "RGBA")

        ow = outline_w * scale if outline else 0
        draw.rounded_rectangle(
            [ow, ow, sw - 1 - ow, sh - 1 - ow],
            radius=sr,
            fill=fill,
            outline=outline if outline else None,
            width=ow,
        )

        if icon_type and icon_color:
            cx, cy = icon_x * scale, sh // 2
            match icon_type:
                case "play":
                    draw.polygon([(cx - 14, cy - 22), (cx - 14, cy + 22), (cx + 22, cy)], fill=icon_color)
                case "stop":
                    draw.rounded_rectangle([cx - 18, cy - 18, cx + 18, cy + 18], radius=6, fill=icon_color)
                case "queue":
                    draw.polygon([(cx - 22, cy - 18), (cx - 22, cy + 18), (cx + 2, cy)], fill=icon_color)
                    draw.polygon([(cx + 4, cy - 18), (cx + 4, cy + 18), (cx + 28, cy)], fill=icon_color)
                case "check":
                    draw.line(
                        [(cx - 16, cy + 2), (cx - 4, cy + 14), (cx + 18, cy - 12)],
                        fill=icon_color,
                        width=8,
                        joint="curve",
                    )
                case "search":
                    draw.ellipse([cx - 20, cy - 20, cx + 8, cy + 8], outline=icon_color, width=7)
                    draw.line([(cx + 5, cy + 5), (cx + 22, cy + 22)], fill=icon_color, width=7)
                case "dot":
                    draw.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], fill=icon_color)

        smooth = img.resize((w, h), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(smooth)
        if len(cls._box_cache) > 400:
            cls._box_cache.clear()
        cls._box_cache[key] = photo
        return photo

    @classmethod
    def get_default_game_icon(cls, size: int = 30) -> ImageTk.PhotoImage:
        if cls._default_icon is not None:
            return cls._default_icon

        scale = 4
        s = size * scale
        img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img, "RGBA")
        draw.rounded_rectangle(
            [0, 0, s - 1, s - 1], radius=8 * scale, fill="#0E3B5E", outline=M3Blue.OUTLINE, width=3
        )

        cx, cy = s // 2, s // 2
        draw.rounded_rectangle([cx - 28, cy - 16, cx + 28, cy + 16], radius=12, fill=M3Blue.PRIMARY)
        draw.line([(cx - 14, cy), (cx - 4, cy)], fill="#0E3B5E", width=6)
        draw.line([(cx - 9, cy - 5), (cx - 9, cy + 5)], fill="#0E3B5E", width=6)
        draw.ellipse([cx + 5, cy - 6, cx + 11, cy], fill="#0E3B5E")
        draw.ellipse([cx + 13, cy + 1, cx + 19, cy + 7], fill="#0E3B5E")

        cls._default_icon = ImageTk.PhotoImage(img.resize((size, size), Image.Resampling.LANCZOS))
        return cls._default_icon

    @staticmethod
    def process_game_icon(raw_img: Image.Image, size: int = 30) -> ImageTk.PhotoImage:
        raw_img = raw_img.convert("RGBA")
        w, h = raw_img.size
        side = min(w, h)
        left = (w - side) // 2
        top = (h - side) // 2
        cropped = raw_img.crop((left, top, left + side, top + side)).resize(
            (size, size), Image.Resampling.LANCZOS
        )

        scale = 4
        mask = Image.new("L", (size * scale, size * scale), 0)
        mdraw = ImageDraw.Draw(mask)
        mdraw.rounded_rectangle([0, 0, size * scale - 1, size * scale - 1], radius=8 * scale, fill=255)
        mask = mask.resize((size, size), Image.Resampling.LANCZOS)

        out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        out.paste(cropped, (0, 0), mask)
        return ImageTk.PhotoImage(out)
