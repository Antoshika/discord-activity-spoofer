import os
import shutil
import subprocess
import threading

from modules.registry import _CoreRegistry
from modules.scanner import sanitize_exe_rel_path


def compile_dummy_exe(dummy_exe_path: str, base_temp_dir: str, compile_lock: threading.Lock):
    with compile_lock:
        os.makedirs(base_temp_dir, exist_ok=True)
        try:
            _CoreRegistry.write_dummy_exe(dummy_exe_path)
        except OSError:
            pass


def kill_processes(processes: list[subprocess.Popen]):
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    for proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=1.0)
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
            if os.name == "nt":
                try:
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=flags,
                        check=False,
                    )
                except (subprocess.SubprocessError, OSError):
                    pass


def spawn_game_processes(
    game_obj: dict,
    runtime_dir: str,
    dummy_exe_path: str,
    priority_on: bool,
) -> list[subprocess.Popen]:
    game_dir = os.path.join(runtime_dir, f"APP_{game_obj['id']}")
    exe_candidates = game_obj.get("all_exes") or [game_obj["exe"]]
    my_pid_str = str(os.getpid())

    spawned = []
    for idx, exe_rel in enumerate(exe_candidates):
        safe_rel = sanitize_exe_rel_path(exe_rel)
        target_exe_path = os.path.join(game_dir, safe_rel)
        target_dir = os.path.dirname(target_exe_path)
        os.makedirs(target_dir, exist_ok=True)

        try:
            _CoreRegistry.write_dummy_exe(target_exe_path)
        except OSError:
            if not os.path.exists(target_exe_path) and os.path.exists(dummy_exe_path):
                try:
                    shutil.copy2(dummy_exe_path, target_exe_path)
                except OSError:
                    pass

        sup_flag = "1" if (priority_on and idx == 0) else "0"
        try:
            proc = subprocess.Popen(
                [target_exe_path, game_obj["name"], my_pid_str, sup_flag],
                cwd=target_dir,
            )
            spawned.append(proc)
        except Exception:
            pass
    return spawned
