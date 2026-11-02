"""
modules/animals.py - Chăn nuôi: cho ăn và thu sản phẩm.

Template cần thiết:
  animal_shed_<name>.png     - chuồng/nhà của con vật (để mở vùng chăn nuôi)
  animal_hungry_<name>.png   - bong bóng "đói" trên đầu con vật
  animal_feed_<name>.png     - thức ăn trên thanh chọn thức ăn
  animal_product_<name>.png  - bong bóng sản phẩm sẵn sàng thu (trứng/sữa/...)
"""

import time

from modules.base import BaseModule
from vision import center


class AnimalsModule(BaseModule):
    name = "animals"

    def run_cycle(self, cycle: int):
        cfg = self.config.get("animals", {})
        if not cfg.get("enabled"):
            return
        if cycle % max(1, int(cfg.get("run_every_cycles", 5))) != 0:
            return

        types = [t for t in cfg.get("types", []) if t.get("enabled")]
        for t in types:
            self._handle(t)

    def _handle(self, animal: dict):
        name = animal["name"]
        every = max(1, int(animal.get("run_every_cycles",
                                      self.config["animals"].get("run_every_cycles", 5))))
        self.log(f"[animals] Xử lý {name}...")

        # 1) Thu sản phẩm sẵn sàng (trứng, sữa, ...)
        img = self.shot()
        ready = self.find(img, f"animal_product_{name}", 0.80, "animal_area")
        if ready:
            self.log(f"[animals] {name}: thu {len(ready)} sản phẩm")
            self.tap_matches(ready, pause=0.35)
            time.sleep(0.8)

        # 2) Cho ăn những con đang đói
        img = self.shot()
        hungry = self.find(img, f"animal_hungry_{name}", 0.80, "animal_area")
        if not hungry:
            self.log(f"[animals] {name}: không con nào đói.")
            return

        feed = self.find_one(self.shot(), f"animal_feed_{name}", 0.80)
        if not feed:
            self.log(f"[animals] Thiếu template animal_feed_{name}.png - không cho ăn được.")
            return

        self.log(f"[animals] {name}: cho {len(hungry)} con ăn")
        fx, fy = center(feed)
        self.adb.tap(fx, fy)          # chọn thức ăn
        time.sleep(0.5)
        self.tap_matches(hungry, pause=0.30)
        time.sleep(0.5)
