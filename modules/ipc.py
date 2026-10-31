import ctypes
import json
import struct
import threading
import time
import uuid
from ctypes import wintypes


class DiscordIPCInjector:
    GENERIC_READ = 0x80000000
    GENERIC_WRITE = 0x40000000
    OPEN_EXISTING = 3
    INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

    def __init__(self):
        self._stop_event: threading.Event | None = None
        self._lock = threading.Lock()
        self.k32 = ctypes.windll.kernel32 if hasattr(ctypes, "windll") else None
        self.u32 = ctypes.windll.user32 if hasattr(ctypes, "windll") else None

    def start(self, app_id: str, pid: int, game_name: str):
        self.stop()
        stop_ev = threading.Event()
        with self._lock:
            self._stop_event = stop_ev
        threading.Thread(
            target=self._ipc_worker,
            args=(str(app_id), int(pid), game_name, stop_ev),
            daemon=True,
        ).start()

    def stop(self):
        with self._lock:
            if self._stop_event is not None:
                self._stop_event.set()
                self._stop_event = None

    def _open_pipe(self):
        if self.k32 is None:
            return None
        for i in range(10):
            pipe_name = rf"\\.\pipe\discord-ipc-{i}"
            h = self.k32.CreateFileW(
                pipe_name,
                self.GENERIC_READ | self.GENERIC_WRITE,
                0,
                None,
                self.OPEN_EXISTING,
                0,
                None,
            )
            if h not in (self.INVALID_HANDLE_VALUE, -1, 0):
                return h
            if self.k32.GetLastError() == 231:
                self.k32.WaitNamedPipeW(pipe_name, 1000)
                h = self.k32.CreateFileW(
                    pipe_name,
                    self.GENERIC_READ | self.GENERIC_WRITE,
                    0,
                    None,
                    self.OPEN_EXISTING,
                    0,
                    None,
                )
                if h not in (self.INVALID_HANDLE_VALUE, -1, 0):
                    return h
        return None

    def _write_packet(self, h_pipe, op: int, payload: dict) -> bool:
        if self.k32 is None:
            return False
        raw = json.dumps(payload).encode("utf-8")
        packet = struct.pack("<II", op, len(raw)) + raw
        written = wintypes.DWORD(0)
        ok = self.k32.WriteFile(h_pipe, packet, len(packet), ctypes.byref(written), None)
        return bool(ok and written.value == len(packet))

    def _drain_pipe(self, h_pipe, wait_ms: int = 200) -> bool:
        if self.k32 is None:
            return False
        loops = max(1, wait_ms // 25)
        for _ in range(loops):
            avail = wintypes.DWORD(0)
            ok = self.k32.PeekNamedPipe(h_pipe, None, 0, None, ctypes.byref(avail), None)
            if not ok:
                return False
            if avail.value >= 8:
                buf = ctypes.create_string_buffer(min(avail.value, 16384))
                read_bytes = wintypes.DWORD(0)
                self.k32.ReadFile(h_pipe, buf, len(buf), ctypes.byref(read_bytes), None)
                return True
            time.sleep(0.025)
        return True

    def _ipc_worker(self, app_id: str, pid: int, game_name: str, stop_ev: threading.Event):
        start_ts = int(time.time())
        while not stop_ev.is_set():
            h_pipe = self._open_pipe()
            if not h_pipe:
                if stop_ev.wait(2.0):
                    break
                continue

            try:
                if not self._write_packet(h_pipe, 0, {"v": 1, "client_id": app_id}):
                    continue
                self._drain_pipe(h_pipe, 400)

                while not stop_ev.is_set():
                    activity_payload = {
                        "cmd": "SET_ACTIVITY",
                        "args": {
                            "pid": pid,
                            "activity": {
                                "details": game_name,
                                "state": "In Game",
                                "timestamps": {"start": start_ts},
                                "instance": True,
                            },
                        },
                        "nonce": str(uuid.uuid4()),
                    }
                    if not self._write_packet(h_pipe, 1, activity_payload):
                        break
                    self._drain_pipe(h_pipe, 150)

                    if stop_ev.wait(2.0):
                        break
            except (OSError, struct.error, ValueError):
                pass
            finally:
                try:
                    clear_payload = {
                        "cmd": "SET_ACTIVITY",
                        "args": {"pid": pid, "activity": None},
                        "nonce": str(uuid.uuid4()),
                    }
                    self._write_packet(h_pipe, 1, clear_payload)
                except (OSError, struct.error, ValueError):
                    pass
                if self.k32 is not None:
                    try:
                        self.k32.CloseHandle(h_pipe)
                    except (OSError, ValueError):
                        pass
