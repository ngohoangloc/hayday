"""
adb_core.py - Lớp điều khiển thiết bị Android qua ADB.

Cung cấp: kết nối thiết bị, chụp màn hình, tap, swipe, phím, mở/đóng app.
Hoạt động tốt trên Windows (USB hoặc WiFi) và Linux.
"""

import subprocess
import time
import random

import numpy as np
import cv2


class ADBError(RuntimeError):
    pass


class ADB:
    """Wrapper mỏng quanh binary `adb` của Android SDK Platform-Tools."""

    def __init__(self, adb_path: str = "adb", serial: str | None = None,
                 package: str = "com.supercell.hayday", activity: str | None = None):
        self.adb_path = adb_path
        self.serial = serial
        self.package = package
        self.activity = activity
        self._size_cache = None

    # ------------------------------------------------------------------ #
    # Lớp thấp
    # ------------------------------------------------------------------ #

    def _base_cmd(self) -> list[str]:
        cmd = [self.adb_path]
        if self.serial:
            cmd += ["-s", self.serial]
        return cmd

    def run(self, args: list[str], binary: bool = False, timeout: float = 30) -> bytes | str:
        """Chạy một lệnh adb cho thiết bị đã chọn."""
        cmd = self._base_cmd() + args
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=timeout)
        except FileNotFoundError:
            raise ADBError(
                f"Không tìm thấy '{self.adb_path}'. Hãy cài Android Platform-Tools "
                f"và thêm adb vào PATH (hoặc đặt đường dẫn trong config.json)."
            )
        if result.returncode != 0:
            err = result.stderr.decode(errors="replace").strip()
            raise ADBError(f"ADB thất bại: {' '.join(args)}\n{err}")
        return result.stdout if binary else result.stdout.decode(errors="replace")

    @staticmethod
    def list_devices(adb_path: str = "adb") -> list[str]:
        """Danh sách serial của các thiết bị đang kết nối (trạng thái 'device')."""
        try:
            out = subprocess.run([adb_path, "devices"], capture_output=True,
                                 timeout=10).stdout.decode(errors="replace")
        except FileNotFoundError:
            raise ADBError(f"Không tìm thấy adb: '{adb_path}'")
        devices = []
        for line in out.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device":
                devices.append(parts[0])
        return devices

    # ------------------------------------------------------------------ #
    # Thiết bị
    # ------------------------------------------------------------------ #

    def screen_size(self) -> tuple[int, int]:
        """(width, height) của màn hình, có cache."""
        if self._size_cache is None:
            out = self.run(["shell", "wm", "size"])
            # Ví dụ: "Physical size: 1080x2400"
            for token in out.split():
                if "x" in token and token.replace("x", "").isdigit():
                    w, h = token.strip().split("x")
                    self._size_cache = (int(w), int(h))
                    break
            if self._size_cache is None:
                raise ADBError(f"Không đọc được độ phân giải: {out!r}")
        return self._size_cache

    def screenshot(self) -> np.ndarray:
        """Chụp màn hình, trả về ảnh BGR (numpy). Không cần root."""
        raw = self.run(["exec-out", "screencap", "-p"], binary=True, timeout=20)
        img = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            # Một số thiết bị cũ trả về CR/LF làm hỏng PNG - thử sửa
            fixed = raw.replace(b"\r\n", b"\n")
            img = cv2.imdecode(np.frombuffer(fixed, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            raise ADBError("Không giải mã được ảnh screencap.")
        return img

    # ------------------------------------------------------------------ #
    # Điều khiển
    # ------------------------------------------------------------------ #

    def tap(self, x: int, y: int, jitter_ms: int = 0):
        """Chạm tại toạ độ pixel."""
        if jitter_ms:
            x += random.randint(-jitter_ms, jitter_ms)
            y += random.randint(-jitter_ms, jitter_ms)
        self.run(["shell", "input", "tap", str(int(x)), str(int(y))])

    def long_press(self, x: int, y: int, ms: int = 700):
        self.run(["shell", "input", "swipe", str(int(x)), str(int(y)),
                  str(int(x)), str(int(y)), str(int(ms))])

    def swipe(self, x1: int, y1: int, x2: int, y2: int, ms: int = 400):
        self.run(["shell", "input", "swipe", str(int(x1)), str(int(y1)),
                  str(int(x2)), str(int(y2)), str(int(ms))])

    def drag_row(self, y: int, x1: int, x2: int, ms: int = 700, jiggle_px: int = 0):
        """Vuốt kéo ngang qua một hàng ruộng (giữ ngón tay, không nhấc).

        Giữ NGUYÊN chiều (x1 -> x2) do caller quyết định để tạo zigzag.
        Jiggle nhỏ giúp quét trọn từng ô như kỹ thuật drag của InfiniFarm
        (h8d13/HayDay): quét chính -> lệch nhẹ lên -> quét ngược -> lệch nhẹ xuống.
        """
        self.swipe(x1, y, x2, y, ms)
        if jiggle_px > 0:
            self.swipe(x2, y - jiggle_px, x1, y - jiggle_px, ms)
            self.swipe(x1, y + jiggle_px, x2, y + jiggle_px, ms)

    def drag_rows(self, rows, ms: int = 700, jiggle_px: int = 0, pause: float = 0.4):
        """Vuốt lần lượt từng hàng, đổi chiều mỗi hàng (zigzag)."""
        for i, (y, x1, x2) in enumerate(rows):
            if i % 2 == 1:
                x1, x2 = x2, x1
            self.drag_row(y, x1, x2, ms=ms, jiggle_px=jiggle_px)
            time.sleep(pause)

    def drag_fraction(self, fx1: float, fy1: float, fx2: float, fy2: float, ms: int = 500):
        """Vuốt theo tỉ lệ khung hình (0.0-1.0)."""
        w, h = self.screen_size()
        self.swipe(fx1 * w, fy1 * h, fx2 * w, fy2 * h, ms)

    def key(self, keycode: str):
        self.run(["shell", "input", "keyevent", keycode])

    def back(self):
        self.key("KEYCODE_BACK")

    def home(self):
        self.key("KEYCODE_HOME")

    # ------------------------------------------------------------------ #
    # Ứng dụng
    # ------------------------------------------------------------------ #

    def is_package_running(self) -> bool:
        out = self.run(["shell", "pidof", self.package], timeout=10)
        return bool(out.strip())

    def start_game(self, wait_seconds: int = 45):
        self.run(["shell", "monkey", "-p", self.package,
                  "-c", "android.intent.category.LAUNCHER", "1"], timeout=30)
        time.sleep(wait_seconds)

    def stop_game(self):
        self.run(["shell", "am", "force-stop", self.package], timeout=20)

    # ------------------------------------------------------------------ #
    # Tiện ích theo tỉ lệ
    # ------------------------------------------------------------------ #

    def tap_fraction(self, fx: float, fy: float):
        """Chạm theo toạ độ tỉ lệ (0.0-1.0) - độc lập độ phân giải."""
        w, h = self.screen_size()
        self.tap(int(fx * w), int(fy * h))
