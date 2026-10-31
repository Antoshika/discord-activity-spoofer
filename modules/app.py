import json
import os
import tempfile
import threading
import time
import tkinter as tk
from tkinter import ttk

import requests
from PIL import Image

from modules.game_list import GameListController
from modules.icon_fetcher import IconWorkerPool
from modules.ipc import DiscordIPCInjector
from modules.renderer import SmoothRenderer
from modules.scanner import (
    load_discord_detectable_games,
    parse_local_steam_appids,
)
from modules.session import SessionController
from modules.spawner import compile_dummy_exe
from modules.theme import M3Blue
from modules.ui_builder import build_app_ui, setup_treeview_styles
from modules.window_frame import WindowFrameController


class DiscordSteamSpooferM3BlueApp:
    PAGE_SIZE = 80

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Discord Activity Spoofer by antoshika")
        self.root.geometry("960x720")
        self.root.minsize(840, 580)
        self.root.configure(bg=M3Blue.SURFACE)

        self.steam_path: str | None = None
        self.discord_games: list[dict] = []
        self.games_by_id: dict[str, dict] = {}
        self.user_steam_appids: set[str] = set()
        self.filtered_games: list[dict] = []
        self.rendered_count = 0
        self._search_after_id = None
        self._scroll_after_id = None

        self.custom_icons_cache: dict[str, object] = {}
        self._compile_lock = threading.Lock()

        self.active_processes: list = []
        self.active_game_obj: dict | None = None
        self.session_start_time: float | None = None
        self.auto_farming = False
        self.auto_farm_queue_names: list[str] = []
        self.ipc_injector = DiscordIPCInjector()

        real_user_root = os.path.join(tempfile.gettempdir(), "DISCORD_GAME_SPOOFER")
        self.runtime_dir = real_user_root
        self.base_temp_dir = os.path.join(real_user_root, "assets")
        self.icons_dir = os.path.join(self.base_temp_dir, "icons")
        os.makedirs(self.icons_dir, exist_ok=True)
        os.makedirs(self.runtime_dir, exist_ok=True)
        self.dummy_exe_path = os.path.join(self.base_temp_dir, "host_service.exe")

        self.tree: ttk.Treeview
        self.status_var: tk.StringVar

        self.frame_ctrl = WindowFrameController(self)
        self.game_list_ctrl = GameListController(self)
        self.session_ctrl = SessionController(self)

        setup_treeview_styles()
        build_app_ui(self)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.frame_ctrl.setup_custom_frame()

        self.icon_pool = IconWorkerPool(
            self.icons_dir,
            lambda: self.steam_path,
            self._apply_loaded_icon,
        )

        threading.Thread(target=self._init_background, daemon=True).start()
        self._tick_timer()

    def _minimize_window(self):
        self.frame_ctrl.minimize_window()

    def _on_restore_from_taskbar(self, event=None):
        self.frame_ctrl.on_restore_from_taskbar(event)

    def _toggle_maximize(self, event=None):
        self.frame_ctrl.toggle_maximize(event)

    def _start_window_drag(self, event):
        self.frame_ctrl.start_drag(event)

    def _do_window_drag(self, event):
        self.frame_ctrl.do_drag(event)

    def _resize_right(self, event):
        self.frame_ctrl.resize_right(event)

    def _resize_bottom(self, event):
        self.frame_ctrl.resize_bottom(event)

    def _on_select_all_toggled(self):
        self.game_list_ctrl.on_select_all_toggled()

    def _on_ctrl_a(self, _=None):
        return self.game_list_ctrl.on_ctrl_a(_)

    def _on_tree_click_release(self, _=None):
        self.game_list_ctrl.on_tree_click_release(_)

    def _on_tree_selection_changed(self, _=None):
        self.game_list_ctrl.on_tree_selection_changed(_)

    def _on_search_typed(self, *_):
        self.game_list_ctrl.on_search_typed(*_)

    def _sync_tree_columns(self, event):
        self.game_list_ctrl.sync_tree_columns(event)

    def _on_tree_scroll(self, first, last):
        self.game_list_ctrl.on_tree_scroll(first, last)

    def _apply_loaded_icon(self, app_id: str, pil_img: Image.Image):
        try:
            tk_icon = SmoothRenderer.process_game_icon(pil_img, size=30)
            self.custom_icons_cache[app_id] = tk_icon
            if self.tree.exists(app_id):
                self.tree.item(app_id, image=tk_icon)
        except (tk.TclError, OSError):
            pass

    def _tick_timer(self):
        if self.active_processes and self.session_start_time:
            elapsed = int(time.time() - self.session_start_time)
            hrs, rem = divmod(elapsed, 3600)
            mins, secs = divmod(rem, 60)
            self.timer_lbl.config(text=f"{hrs:02d}:{mins:02d}:{secs:02d}", fg=M3Blue.PRIMARY)
        else:
            self.timer_lbl.config(text="00:00:00", fg=M3Blue.ON_PRIMARY_CONTAINER)
        self.root.after(1000, self._tick_timer)

    def _init_background(self):
        self.set_status("Initializing game environment...")
        self._compile_dummy_exe()

        self.set_status("Loading Discord detectable games cache...")
        self._load_discord_detectable()

        self.set_status("Syncing with local Steam library...")
        self.parse_local_steam()

        self.root.after(0, self.update_game_list)

    def _compile_dummy_exe(self):
        compile_dummy_exe(self.dummy_exe_path, self.base_temp_dir, self._compile_lock)

    def _load_discord_detectable(self):
        try:
            self.discord_games, self.games_by_id = load_discord_detectable_games()
        except (requests.RequestException, json.JSONDecodeError, OSError) as e:
            self.set_status(f"Error loading Discord database: {e}")

    def parse_local_steam(self):
        steam_path, found_appids = parse_local_steam_appids()
        self.steam_path = steam_path
        if not steam_path:
            self.set_status(f"Loaded {len(self.discord_games)} games from Discord database.")
            return

        if found_appids:
            self.user_steam_appids = found_appids
            self.root.after(0, lambda: self.only_steam_var.set(True))
            self.set_status(f"Synced with local Steam library ({len(found_appids)} AppIDs). Double-click any game to launch.")
        else:
            self.set_status(f"Ready. {len(self.discord_games)} games available.")

    def update_game_list(self):
        self.game_list_ctrl.update_game_list()

    def toggle_run_stop(self):
        self.session_ctrl.toggle_run_stop()

    def run_selected_game(self):
        self.session_ctrl.run_selected_game()

    def start_autofarm(self):
        self.session_ctrl.start_autofarm()

    def stop_all(self):
        self.session_ctrl.stop_all()

    def _spawn_spoofed_game(self, game_obj: dict):
        self.session_ctrl.spawn_spoofed_game(game_obj)

    def _update_toggle_button_ui(self):
        self.session_ctrl.update_toggle_button_ui()

    def _kill_active_process(self, keep_queue: bool = False):
        self.session_ctrl.kill_active_process(keep_queue=keep_queue)

    def set_status(self, text: str):
        self.root.after(0, lambda: self.status_var.set(text))

    def on_close(self):
        self.stop_all()
        self.root.destroy()
