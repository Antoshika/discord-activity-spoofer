import threading
import time
from tkinter import messagebox

from modules.spawner import kill_processes, spawn_game_processes
from modules.theme import M3Blue


class SessionController:
    def __init__(self, app):
        self.app = app

    def update_toggle_button_ui(self):
        is_running = bool(self.app.active_processes) or self.app.auto_farming
        if is_running:
            self.app.btn_toggle_run.configure_state("Stop Game", "stop", "error")
        else:
            self.app.btn_toggle_run.configure_state("Launch Game", "play", "filled")

    def toggle_run_stop(self):
        if self.app.active_processes or self.app.auto_farming:
            self.app.stop_all()
        else:
            self.app.run_selected_game()

    def spawn_spoofed_game(self, game_obj: dict):
        self.kill_active_process(keep_queue=True)
        self.app._compile_dummy_exe()

        priority_on = self.app.ipc_lock_var.get()
        try:
            spawned = spawn_game_processes(
                game_obj, self.app.runtime_dir, self.app.dummy_exe_path, priority_on
            )
        except Exception as e:
            self.app.set_status(f"Error launching game: {e}")
            return

        if not spawned:
            self.app.set_status(f"Failed to launch game process for {game_obj['name']}.")
            return

        self.app.active_processes = spawned
        self.app.active_game_obj = game_obj
        self.app.session_start_time = time.time()

        primary_pid = spawned[0].pid
        self.app.ipc_injector.start(game_obj["id"], primary_pid, game_obj["name"])

        self.app.root.after(
            0,
            lambda: self.app.priority_pill.set_state(
                f"GLOBAL PRIORITY: LOCKED ({primary_pid})" if priority_on else f"PROCESS ACTIVE ({primary_pid})",
                M3Blue.PRIMARY,
                M3Blue.SECONDARY_CONTAINER if priority_on else M3Blue.SURFACE_HIGH,
            ),
        )

        self.app.root.after(0, lambda: self.app.active_game_lbl.config(text=game_obj["name"]))
        self.app.root.after(0, self.update_toggle_button_ui)
        self.app.set_status(f"Running game: {game_obj['name']}  [{game_obj['exe']}]")

    def run_selected_game(self):
        self.app.auto_farming = False
        self.app.auto_farm_queue_names = []
        self.app.queue_info_lbl.config(text="Queue: Idle")
        sel = self.app.tree.selection()
        if not sel and self.app.select_all_var.get() and self.app.filtered_games:
            game_obj = self.app.filtered_games[0]
        elif sel:
            game_obj = self.app.games_by_id.get(sel[0])
        elif self.app.filtered_games:
            game_obj = self.app.filtered_games[0]
            self.app.tree.selection_set(game_obj["id"])
        else:
            messagebox.showinfo("Select Game", "Please select a game from the list first.")
            return

        if game_obj:
            self.app.progress_bar.set_progress(100)
            self.spawn_spoofed_game(game_obj)

    def start_autofarm(self):
        if self.app.select_all_var.get() and self.app.filtered_games:
            queue = list(self.app.filtered_games)
        else:
            sel = self.app.tree.selection()
            if not sel:
                messagebox.showinfo("Auto-Farm", "Select games in the list or enable 'Select All' first.")
                return
            queue = [self.app.games_by_id[iid] for iid in sel if iid in self.app.games_by_id]

        if not queue:
            return

        try:
            interval = max(30, int(self.app.interval_input.get().strip()))
        except ValueError:
            interval = 300

        self.app.auto_farming = True
        self.app.auto_farm_queue_names = [g["name"] for g in queue]
        self.update_toggle_button_ui()
        threading.Thread(target=self._autofarm_worker, args=(queue, interval), daemon=True).start()

    def _autofarm_worker(self, queue: list, interval: int):
        total = len(queue)
        for idx, game_obj in enumerate(queue, start=1):
            if not self.app.auto_farming:
                break
            q_text = f"Queue [{idx}/{total}]: " + " -> ".join([g["name"] for g in queue[idx - 1:]])
            if len(q_text) > 115:
                q_text = q_text[:112] + "..."
            self.app.root.after(0, lambda t=q_text: self.app.queue_info_lbl.config(text=t))
            self.spawn_spoofed_game(game_obj)

            for elapsed in range(interval):
                if not self.app.auto_farming:
                    break
                remaining = interval - elapsed
                pct = ((elapsed + 1) / interval) * 100
                self.app.root.after(0, lambda p=pct: self.app.progress_bar.set_progress(p))
                self.app.set_status(f"Auto-Farm [{idx}/{total}]: {game_obj['name']} - switching in {remaining}s...")
                time.sleep(1)

        if self.app.auto_farming:
            self.app.auto_farming = False
            self.app.auto_farm_queue_names = []
            self.app.root.after(0, lambda: self.app.queue_info_lbl.config(text="Queue: Completed"))
            self.kill_active_process()
            self.app.root.after(0, lambda: self.app.progress_bar.set_progress(0))
            self.app.set_status("Auto-Farm queue completed successfully.")

    def kill_active_process(self, keep_queue: bool = False):
        self.app.ipc_injector.stop()
        kill_processes(self.app.active_processes)
        self.app.active_processes = []
        self.app.active_game_obj = None
        self.app.session_start_time = None
        self.app.root.after(0, lambda: self.app.active_game_lbl.config(text="Waiting for game launch..."))
        if not keep_queue:
            self.app.root.after(0, lambda: self.app.queue_info_lbl.config(text="Queue: Idle"))
        self.app.root.after(
            0,
            lambda: self.app.priority_pill.set_state(
                "GLOBAL PRIORITY: STANDBY",
                M3Blue.ON_SURFACE_VARIANT,
                M3Blue.SURFACE_CONTAINER,
            ),
        )
        self.app.root.after(0, self.update_toggle_button_ui)

    def stop_all(self):
        self.app.auto_farming = False
        self.app.auto_farm_queue_names = []
        self.kill_active_process(keep_queue=False)
        self.app.progress_bar.set_progress(0)
        self.app.set_status("All processes stopped.")
