"""
modules/miner.py - Mỏ tự động: dùng thuốc nổ/Dynamite/TNT và thu quặng.

Template cần thiết:
  btn_miner.png      - nút/mỏ trên trang trại
  btn_dynamite.png   - thuốc nổ
  btn_tnt.png        - thùng TNT
  btn_close.png      - nút đóng
"""

import time

from modules.base import BaseModule


class MinerModule(BaseModule):
    name = "miner"

    def run_cycle(self, cycle: int):
        cfg = self.config.get("miner", {})
        if not cfg.get("enabled"):
            return
        if cycle % max(1, int(cfg.get("run_every_cycles", 10))) != 0:
            return

        if not self.tap_template("btn_miner", 0.80, tries=2):
            self.log("[miner] Không mở được khu mỏ.")
            return
        time.sleep(1.0)

        used = 0
        if cfg.get("dynamite"):
            used += self._use("btn_dynamite")
        if cfg.get("tnt_barrel"):
            used += self._use("btn_tnt")

        if not self.tap_template("btn_close", 0.80, tries=1):
            self.adb.back()
        time.sleep(0.5)
        self.log(f"[miner] Đã dùng {used} loại thuốc nổ.")

    def _use(self, template: str) -> int:
        img = self.shot()
        matches = self.find(img, template, 0.80)
        if matches:
            self.tap_matches(matches[:1], pause=0.8)
            time.sleep(1.0)
        return len(matches[:1])
