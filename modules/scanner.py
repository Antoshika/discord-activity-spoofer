import json
import os
import re
import sys
from typing import Any

import requests

from modules.registry import _CoreRegistry
from modules.text import normalize_name

if sys.platform == "win32":
    import winreg
else:
    winreg: Any = None

_APPID_BRACE_RE = re.compile(r'"(\d{2,10})"\s*\{')
_APPID_QUOTED_RE = re.compile(r'"(\d{2,10})"\s*"\d+"')
_JSON_APPID_RE = re.compile(r"^(\d+)\.json$")
_PATH_SPLIT_RE = re.compile(r"[/\\]+")
_FORBIDDEN_CHARS = {":", "*", "?", "<", ">", "|"}


def sanitize_exe_rel_path(exe_rel: str) -> str:
    raw_parts = _PATH_SPLIT_RE.split(exe_rel.strip("/\\"))
    clean_parts = []
    for p in raw_parts:
        p_clean = p.strip().rstrip(".")
        if p_clean and p_clean not in (".", ".."):
            clean_parts.append(p_clean)
    if not clean_parts:
        clean_parts = ["game.exe"]
    if not clean_parts[-1].lower().endswith(".exe"):
        clean_parts[-1] += ".exe"
    return os.path.join(*clean_parts)


def find_local_steam_icon(steam_path: str | None, steam_ids: list | set) -> str | None:
    if not steam_path or not steam_ids:
        return None
    lib_cache = os.path.join(steam_path, "appcache", "librarycache")
    if not os.path.exists(lib_cache):
        return None

    for sid in steam_ids:
        for suffix in ("_icon.jpg", "_icon.png", "_header.jpg", "_library_600x900.jpg"):
            cand = os.path.join(lib_cache, f"{sid}{suffix}")
            if os.path.exists(cand):
                return cand

        sub_dir = os.path.join(lib_cache, str(sid))
        if os.path.isdir(sub_dir):
            try:
                files = os.listdir(sub_dir)
            except OSError:
                continue
            for f in files:
                f_low = f.lower()
                if "icon" in f_low and f_low.endswith((".jpg", ".png")):
                    return os.path.join(sub_dir, f)
            for f in files:
                if f.lower().endswith((".jpg", ".png")):
                    return os.path.join(sub_dir, f)
    return None


def parse_local_steam_appids() -> tuple[str | None, set[str]]:
    if winreg is None:
        return None, set()

    steam_path = None
    for root_key, subkey, val_name in [
        (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", "SteamPath"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam", "InstallPath"),
    ]:
        try:
            with winreg.OpenKey(root_key, subkey) as k:
                val, _ = winreg.QueryValueEx(k, val_name)
                if val and os.path.exists(val):
                    steam_path = os.path.normpath(val)
                    break
        except OSError:
            continue

    if not steam_path:
        return None, set()

    found_appids: set[str] = set()
    userdata_dir = os.path.join(steam_path, "userdata")
    if os.path.exists(userdata_dir):
        try:
            user_folders = os.listdir(userdata_dir)
        except OSError:
            user_folders = []

        for user_folder in user_folders:
            user_path = os.path.join(userdata_dir, user_folder)
            if not os.path.isdir(user_path):
                continue

            lib_cache = os.path.join(user_path, "config", "librarycache")
            if os.path.exists(lib_cache):
                try:
                    for fname in os.listdir(lib_cache):
                        m = _JSON_APPID_RE.match(fname)
                        if m:
                            found_appids.add(m.group(1))
                except OSError:
                    pass

            for vdf_rel in [
                os.path.join("config", "localconfig.vdf"),
                os.path.join("7", "remote", "sharedconfig.vdf"),
            ]:
                vdf_path = os.path.join(user_path, vdf_rel)
                if os.path.exists(vdf_path):
                    try:
                        with open(vdf_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        for appid in _APPID_BRACE_RE.findall(content):
                            found_appids.add(appid)
                    except OSError:
                        pass

    lib_vdf = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
    if os.path.exists(lib_vdf):
        try:
            with open(lib_vdf, "r", encoding="utf-8", errors="ignore") as f:
                for appid in _APPID_QUOTED_RE.findall(f.read()):
                    found_appids.add(appid)
        except OSError:
            pass

    return steam_path, found_appids


def load_discord_detectable_games() -> tuple[list[dict], dict[str, dict]]:
    cache_path = _CoreRegistry.cache_filepath()
    data = None
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            data = None

    if not data:
        resp = requests.get(_CoreRegistry.detectable_endpoint(), timeout=20)
        resp.raise_for_status()
        data = resp.json()
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except OSError:
            pass

    parsed = []
    games_by_id = {}
    seen_ids = set()
    for app in data:
        if not isinstance(app, dict):
            continue
        app_id = str(app.get("id", "0"))
        if app_id in seen_ids:
            continue
        name = app.get("name")
        executables = app.get("executables", [])
        if not name or not executables:
            continue

        win_exes = [
            ex["name"].lstrip("/\\")
            for ex in executables
            if ex.get("os") == "win32" and ex.get("name") and not ex.get("is_launcher", False)
        ]
        if not win_exes:
            win_exes = [
                ex["name"].lstrip("/\\")
                for ex in executables
                if ex.get("os") == "win32" and ex.get("name")
            ]

        valid_exes = [
            e for e in win_exes if e and not any(c in e for c in _FORBIDDEN_CHARS)
        ]
        if not valid_exes:
            continue

        exe_rel_path = valid_exes[0]
        steam_ids = {
            str(sku["id"])
            for sku in (app.get("third_party_skus") or [])
            if isinstance(sku, dict) and sku.get("distributor") == "steam" and sku.get("id")
        }

        norm_names = {normalize_name(name)}
        for alias in app.get("aliases", []):
            if alias:
                norm_names.add(normalize_name(alias))

        seen_ids.add(app_id)
        game_obj = {
            "id": app_id,
            "name": name,
            "name_lower": name.lower(),
            "exe_lower": exe_rel_path.lower(),
            "icon": app.get("icon") or app.get("cover_image"),
            "norm_names": norm_names,
            "steam_ids": steam_ids,
            "exe": exe_rel_path,
            "all_exes": valid_exes[:2],
        }
        parsed.append(game_obj)
        games_by_id[app_id] = game_obj

    sorted_games = sorted(parsed, key=lambda x: x["name_lower"])
    return sorted_games, games_by_id
