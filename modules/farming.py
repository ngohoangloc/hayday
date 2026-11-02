"""
modules/farming.py - Plant Rotation: thu hoạch và gieo trồng tự động.

Template cần thiết (đặt trong templates/):
  crop_ready_<crop>.png  - biểu tượng cây chín phía trên ô ruộng
  field_empty.png        - ô ruộng trống (chưa trồng)
  seed_<crop>.png        - hạt giống trên thanh chọn hạt giống
"""

import time

from modules.base import BaseModule
from vision import center


class FarmingModule(BaseModule):
    name = "farming"

    def run_cycle(self, cycle: int):
        cfg = self.config.get("plant_rotation", {})
        if not cfg.get("enabled"):
            return
        crops = [c for c in cfg.get("crops", []) if c.get("enabled")]

        if not crops:
            self.log("[farming] Không có loại cây nào được bật.")
            return

        self._harvest(crops)
        self._replant(crops)

        if cfg.get("wait_for_crop_growth"):
            # Chờ đủ thời gian cây ngắn nhất để chín rồi mới sang chu kỳ khác
            shortest = min(c.get("grow_seconds", 120) for c in crops)
            self.log(f"[farming] Chờ {shortest}s cho cây chín...")
            self._sleep_interruptible(shortest)

    # ------------------------------------------------------------------ #

    def _harvest(self, crops):
        img = self.shot()
        total = 0
        for crop in crops:
            name = crop["name"]
            matches = self.find(img, f"crop_ready_{name}", 0.78, "field_area")
            if matches:
                self.log(f"[farming] Thu hoạch {len(matches)} ô {name}")
                self.tap_matches(matches, pause=0.30)
                total += len(matches)
                time.sleep(1.0)
                img = self.shot()  # màn hình thay đổi sau khi thu hoạch
        self.save_debug(img, "harvest")
        if total == 0:
            self.log("[farming] Không thấy cây nào chín.")
        return total

    def _replant(self, crops):
        img = self.shot()
        empty = self.find(img, "field_empty", 0.80, "field_area")
        if not empty:
            self.log("[farming] Không còn ô ruộng trống.")
            return 0

        # Chọn hạt giống đầu tiên trong danh sách cây được bật
        crop = crops[0]
        seed_tpl = f"seed_{crop['name']}"
        seed = self.find_one(self.shot(), seed_tpl, 0.80, "seed_bar")
        if not seed:
            self.log(f"[farming] Không tìm thấy hạt {crop['name']} trên thanh chọn - bỏ qua gieo trồng.")
            return 0

        self.log(f"[farming] Gieo {crop['name']} vào {len(empty)} ô trống")
        x, y = center(seed)
        self.adb.tap(x, y)          # chọn loại hạt
        time.sleep(0.5)
        self.tap_matches(empty, pause=0.22)
        return len(empty)

    def _sleep_interruptible(self, seconds: float):
        """Ngủ dài nhưng chia nhỏ để log tiến trình."""
        end = time.time() + seconds
        while time.time() < end:
            remain = end - time.time()
            time.sleep(min(10, remain))
