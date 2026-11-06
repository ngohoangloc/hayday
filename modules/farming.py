"""
modules/farming.py - Plant Rotation: thu hoạch và gieo trồng tự động.

Hai chiến lược:
- "drag" (mặc định, kỹ thuật InfiniFarm - h8d13/HayDay): nhận diện vùng đất
  theo màu -> chọn hạt/cây -> VUỐT KÉO qua từng hàng ruộng. Nhanh, phủ toàn bộ
  ruộng, ít phụ thuộc template.
- "tap": tìm từng ô bằng template (cây chín / ô trống) và tap lần lượt.

Tự động chuyển sang "tap" nếu không nhận diện được đất.

Template cần thiết:
  crop_ready_<crop>.png  - biểu tượng cây chín (tuỳ chọn, giúp xác định điểm bắt đầu)
  field_empty.png        - ô ruộng trống (chỉ cần cho chiến lược tap)
  seed_<crop>.png        - hạt giống trên thanh chọn hạt giống
  soil.jpg               - ảnh mẫu đất cày (cho chiến lược drag)
"""

import time

from modules.base import BaseModule
from vision import center


class FarmingModule(BaseModule):
    name = "farming"

    def __init__(self, *args, soil_detector=None, market_module=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.soil = soil_detector
        self.market = market_module

    def run_cycle(self, cycle: int):
        cfg = self.config.get("plant_rotation", {})
        if not cfg.get("enabled"):
            return
        crops = [c for c in cfg.get("crops", []) if c.get("enabled")]
        if not crops:
            self.log("[farming] Không có loại cây nào được bật.")
            return

        strategy = cfg.get("strategy", "drag")
        planted = False
        if strategy == "drag" and self.soil is not None:
            planted = self._cycle_drag(crops)
        if not planted:
            self._cycle_tap(crops)

        if cfg.get("wait_for_crop_growth"):
            shortest = min(c.get("grow_seconds", 120) for c in crops)
            # Bán bớt kho trong thời gian chờ (kỹ thuật "sell during growth")
            if cfg.get("sell_during_growth") and self.market is not None \
                    and self.config.get("market", {}).get("enabled"):
                self.log(f"[farming] Chờ {shortest}s - tranh thủ bán hàng ở chợ...")
                try:
                    self.market.sell_items(cycle)
                except Exception as exc:
                    self.log(f"[farming] Bán hàng khi chờ bị lỗi: {exc}")
            self.log(f"[farming] Chờ cây lớn...")
            self._sleep_interruptible(max(5, shortest - 20))

    def _find_seed(self, crop_name: str):
        """Tìm hạt trên thanh giống, lật tối đa 3 trang nếu chưa thấy."""
        for page in range(3):
            seed = self.find_one(self.shot(), f"seed_{crop_name}", 0.80, "seed_bar")
            if seed:
                return seed
            self.adb.tap(int(0.2625 * self._w()), int(0.7685 * self._h()))
            time.sleep(0.9)
        return None

    def _w(self) -> int:
        return int(self.adb.size[0]) if hasattr(self.adb, "size") else 2400

    def _h(self) -> int:
        return int(self.adb.size[1]) if hasattr(self.adb, "size") else 1080

    # ------------------------------------------------------------------ #
    # Chiến lược drag (InfiniFarm)
    # ------------------------------------------------------------------ #

    def _cycle_drag(self, crops) -> bool:
        img = self.shot()
        soil = self.soil.detect(img)
        if not soil:
            self.log("[farming] Không nhận diện được đất bằng màu - chuyển sang tap.")
            return False
        cx, cy = soil["centroid"]
        rows = soil["rows"]
        self.log(f"[farming] Thấy vùng ruộng {soil['rect']}, centroid ({cx},{cy}), "
                 f"{len(rows)} hàng.")

        sweep_ms = int(self.config.get("soil_detection", {}).get("row_sweep_duration_ms", 700))
        jiggle = int(self.config.get("soil_detection", {}).get("jiggle_pixels", 15))

        # 1) THU HOẠCH: tap một cây chín (nếu có template) để "cầm liềm",
        #    rồi kéo qua toàn bộ ruộng
        start = None
        for crop in crops:
            m = self.find_one(img, f"crop_ready_{crop['name']}", 0.78, "field_area")
            if m:
                start = center(m)
                break
        if start is None and rows:
            ry, rx1, rx2 = rows[len(rows) // 2]
            start = ((rx1 + rx2) // 2, ry)
        if start is None:
            start = (cx, cy)
        self.adb.tap(*start)
        time.sleep(1.0)                      # chờ công cụ liềm xuất hiện
        self.adb.drag_rows(rows, ms=sweep_ms, jiggle_px=jiggle)
        self.log("[farming] Đã kéo thu hoạch toàn ruộng.")

        # 2) GIEO HẠT: phát hiện lại ruộng (camera có thể đã trôi sau khi kéo),
        #    tap một ô TRỐNG để mở thanh giống -> chọn hạt -> kéo qua ruộng
        crop = crops[0]
        img2 = self.shot()
        soil2 = self.soil.detect(img2)
        if soil2:
            cx, cy = soil2["centroid"]
            self.log(f"[farming] Ruộng sau thu hoạch: {soil2['rect']}")
        empties = self.find(img2, "field_empty", 0.80, "field_area")
        spot = center(empties[0]) if empties else (cx, cy)
        self.adb.tap(*spot)                  # mở thanh chọn hạt
        time.sleep(1.0)
        seed = self._find_seed(crop["name"])
        if not seed:
            self.log(f"[farming] Không tìm thấy hạt {crop['name']} trên thanh chọn.")
            return True
        self.adb.tap(*center(seed))
        time.sleep(0.6)
        self.adb.tap(cx, cy)                 # bắt đầu gieo tại tâm ruộng
        time.sleep(0.8)
        self.adb.drag_rows(rows, ms=sweep_ms, jiggle_px=jiggle)
        self.log(f"[farming] Đã kéo gieo {crop['name']} toàn ruộng.")
        self.save_debug(img, "drag")
        return True

    # ------------------------------------------------------------------ #
    # Chiến lược tap (dự phòng)
    # ------------------------------------------------------------------ #

    def _cycle_tap(self, crops):
        self._harvest(crops)
        self._replant(crops)

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
                img = self.shot()
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
        crop = crops[0]
        # Tap ô trống ĐẦU TIÊN để mở thanh chọn hạt
        first = center(empty[0])
        self.adb.tap(*first)
        time.sleep(1.0)
        seed = self._find_seed(crop["name"])
        if not seed:
            self.log(f"[farming] Không tìm thấy hạt {crop['name']} trên thanh chọn.")
            return 0
        self.log(f"[farming] Gieo {crop['name']} vào {len(empty)} ô trống")
        self.adb.tap(*center(seed))
        time.sleep(0.5)
        self.tap_matches(empty, pause=0.22)
        return len(empty)

    def _sleep_interruptible(self, seconds: float):
        end = time.time() + seconds
        while time.time() < end:
            remain = end - time.time()
            time.sleep(min(10, remain))
