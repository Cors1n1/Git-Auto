"""
main.py  —  Ponto de entrada do Git Auto.
Garante instância única, inicializa o app e abre a janela.
"""
import ctypes
import os
import sys

# ── Single-instance guard ──────────────────────────────────────────────────────
kernel32 = ctypes.windll.kernel32
user32   = ctypes.windll.user32

mutex      = kernel32.CreateMutexW(None, False, "GitAutoSingleInstanceMutex")
last_error = kernel32.GetLastError()

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
pid_file = os.path.join(DATA_DIR, "pid.txt")

if last_error == 183:   # ERROR_ALREADY_EXISTS
    try:
        with open(pid_file, "r") as f:
            target_pid = int(f.read().strip())

        EnumWindowsProc = ctypes.WINFUNCTYPE(
            ctypes.c_bool,
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int))

        def foreach_window(hwnd, lParam):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    pid = ctypes.c_ulong()
                    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                    if pid.value == target_pid:
                        if user32.IsIconic(hwnd):
                            user32.ShowWindow(hwnd, 9)       # SW_RESTORE
                        user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 3)  # HWND_TOPMOST
                        user32.SetWindowPos(hwnd, -2, 0, 0, 0, 0, 3)  # HWND_NOTOPMOST
                        user32.SetForegroundWindow(hwnd)
                        return False
            return True

        user32.EnumWindows(EnumWindowsProc(foreach_window), 0)
    except Exception:
        pass
    sys.exit(0)

# ── Save PID for future instances ──────────────────────────────────────────────
os.makedirs(DATA_DIR, exist_ok=True)
with open(pid_file, "w") as f:
    f.write(str(os.getpid()))

# ── Launch ─────────────────────────────────────────────────────────────────────
from app.app import App  # noqa: E402  (import after single-instance check)

if __name__ == "__main__":
    app = App()
    app.mainloop()
