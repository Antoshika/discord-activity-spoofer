import json
import os
import re
import threading
from io import BytesIO
from urllib.parse import quote

import requests
from PIL import Image

from modules.scanner import find_local_steam_icon
from modules.text import normalize_name

_PAREN_STRIP_RE = re.compile(r"\s*\(.*?\)")


def fetch_external_non_steam_icon(game_name: str, session: requests.Session) -> Image.Image | None:
    norm_target = normalize_name(game_name)

    try:
        lutris_url = f"https://lutris.net/api/games?search={quote(game_name)}"
        lr = session.get(lutris_url, timeout=3.5)
        if lr.status_code == 200:
            results = lr.json().get("results", [])
            matched = next((item for item in results if normalize_name(item.get("name", "")) == norm_target), None)
            if not matched and results:
                matched = next((item for item in results if norm_target in normalize_name(item.get("name", ""))), None)
            if matched:
                slug = matched.get("slug")
                candidates = []
                if slug:
                    candidates.append(f"https://lutris.net/games/icon/{slug}.png")
                if matched.get("coverart"):
                    candidates.append(matched["coverart"])
                if matched.get("banner_url"):
                    candidates.append(matched["banner_url"])
                for img_url in candidates:
                    try:
                        ir = session.get(img_url, timeout=3)
                        if ir.status_code == 200 and len(ir.content) > 150:
                            return Image.open(BytesIO(ir.content))
                    except (requests.RequestException, OSError):
                        continue
    except (requests.RequestException, json.JSONDecodeError, OSError):
        pass

    try:
        wiki_url = (
            "https://en.wikipedia.org/w/api.php?action=query&generator=search"
            f"&gsrsearch={quote(game_name + ' video game')}&gsrlimit=3"
            "&prop=pageimages&pithumbsize=120&format=json"
        )
        wr = session.get(wiki_url, timeout=3.5)
        if wr.status_code == 200:
            pages = wr.json().get("query", {}).get("pages", {})
            for page in pages.values():
                title_norm = normalize_name(_PAREN_STRIP_RE.sub("", page.get("title", "")))
                if title_norm == norm_target or norm_target in title_norm:
                    thumb = page.get("thumbnail", {}).get("source")
                    if thumb:
                        tr = session.get(thumb, timeout=3)
                        if tr.status_code == 200 and len(tr.content) > 150:
                            return Image.open(BytesIO(tr.content))
    except (requests.RequestException, json.JSONDecodeError, OSError):
        pass

    try:
        itunes_url = f"https://itunes.apple.com/search?term={quote(game_name)}&entity=software&limit=5"
        ar = session.get(itunes_url, timeout=3.5)
        if ar.status_code == 200:
            for item in ar.json().get("results", []):
                track_norm = normalize_name(item.get("trackName", ""))
                if track_norm == norm_target or track_norm.startswith(norm_target):
                    art_url = item.get("artworkUrl100")
                    if art_url:
                        ir = session.get(art_url, timeout=3)
                        if ir.status_code == 200 and len(ir.content) > 150:
                            return Image.open(BytesIO(ir.content))
    except (requests.RequestException, json.JSONDecodeError, OSError):
        pass

    return None


def fetch_single_icon(
    g: dict, session: requests.Session, icons_dir: str, steam_path: str | None, on_icon_loaded
):
    app_id = g["id"]
    game_name = g["name"]
    steam_ids = list(g.get("steam_ids", []))
    icon_hash = g.get("icon")
    cached_png = os.path.join(icons_dir, f"{app_id}.png")

    raw_img: Image.Image | None = None
    try:
        if os.path.exists(cached_png):
            raw_img = Image.open(cached_png)

        if raw_img is None:
            local_file = find_local_steam_icon(steam_path, steam_ids)
            if local_file:
                raw_img = Image.open(local_file)

        if raw_img is None and not icon_hash:
            try:
                rpc_r = session.get(f"https://discord.com/api/v9/applications/{app_id}/rpc", timeout=2.5)
                if rpc_r.status_code == 200:
                    rpc_data = rpc_r.json()
                    icon_hash = rpc_data.get("icon") or rpc_data.get("cover_image")
            except (requests.RequestException, json.JSONDecodeError, OSError):
                pass

        if raw_img is None and icon_hash:
            for disc_url in (
                f"https://i0.wp.com/cdn.discordapp.com/app-icons/{app_id}/{icon_hash}.png?w=64",
                f"https://wsrv.nl/?url=https://cdn.discordapp.com/app-icons/{app_id}/{icon_hash}.png&w=64&h=64&output=png",
                f"https://cdn.discordapp.com/app-icons/{app_id}/{icon_hash}.png?size=64",
            ):
                try:
                    r = session.get(disc_url, timeout=3)
                    if r.status_code == 200 and len(r.content) > 100:
                        raw_img = Image.open(BytesIO(r.content))
                        break
                except (requests.RequestException, OSError):
                    continue

        if raw_img is None and steam_ids:
            for sid in steam_ids:
                for cdn_url in (
                    f"https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/{sid}/capsule_sm_120.jpg",
                    f"https://cdn.cloudflare.steamstatic.com/steam/apps/{sid}/capsule_sm_120.jpg",
                ):
                    try:
                        r = session.get(cdn_url, timeout=3)
                        if r.status_code == 200 and len(r.content) > 200:
                            raw_img = Image.open(BytesIO(r.content))
                            break
                    except (requests.RequestException, OSError):
                        continue
                if raw_img is not None:
                    break

        if raw_img is None and not steam_ids:
            try:
                search_url = f"https://store.steampowered.com/api/storesearch/?term={quote(game_name)}&l=english&cc=US"
                sr = session.get(search_url, timeout=3)
                if sr.status_code == 200:
                    items = sr.json().get("items", [])
                    norm_target = normalize_name(game_name)
                    for it in items:
                        if normalize_name(it.get("name", "")) == norm_target:
                            tiny_img_url = it.get("tiny_image")
                            if tiny_img_url:
                                tr = session.get(tiny_img_url, timeout=3)
                                if tr.status_code == 200 and len(tr.content) > 200:
                                    raw_img = Image.open(BytesIO(tr.content))
                            break
            except (requests.RequestException, json.JSONDecodeError, OSError):
                pass

        if raw_img is None:
            raw_img = fetch_external_non_steam_icon(game_name, session)

        if raw_img is not None:
            raw_img.load()
            if not os.path.exists(cached_png):
                try:
                    raw_img.save(cached_png, "PNG")
                except OSError:
                    pass
            on_icon_loaded(app_id, raw_img)
    except (requests.RequestException, OSError, ValueError, KeyError):
        pass


class IconWorkerPool:
    def __init__(self, icons_dir: str, get_steam_path, on_icon_loaded, num_workers: int = 4):
        self.icons_dir = icons_dir
        self.get_steam_path = get_steam_path
        self.on_icon_loaded = on_icon_loaded
        self.icon_stack: list[dict] = []
        self.icon_stack_lock = threading.Lock()
        self.icon_event = threading.Event()
        self.icons_loading: set[str] = set()
        self.cached_ids: set[str] = set()

        for _ in range(num_workers):
            threading.Thread(target=self._worker_loop, daemon=True).start()

    def schedule_games(self, games: list[dict]):
        with self.icon_stack_lock:
            self.icon_stack.clear()
            for g in reversed(games):
                cid = g["id"]
                if cid not in self.cached_ids and cid not in self.icons_loading:
                    self.icon_stack.append(g)
            if self.icon_stack:
                self.icon_event.set()

    def _worker_loop(self):
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        while True:
            self.icon_event.wait()
            g = None
            with self.icon_stack_lock:
                while self.icon_stack:
                    cand = self.icon_stack.pop()
                    cid = cand["id"]
                    if cid not in self.cached_ids and cid not in self.icons_loading:
                        self.icons_loading.add(cid)
                        g = cand
                        break
                if not self.icon_stack:
                    self.icon_event.clear()

            if g is None:
                continue

            try:
                fetch_single_icon(
                    g,
                    session,
                    self.icons_dir,
                    self.get_steam_path(),
                    self._on_loaded_wrapper,
                )
            finally:
                self.icons_loading.discard(g["id"])

    def _on_loaded_wrapper(self, app_id: str, raw_img: Image.Image):
        self.cached_ids.add(app_id)
        self.on_icon_loaded(app_id, raw_img)
