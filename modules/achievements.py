"""
modules/achievements.py - Thu thưởng thành tựu (Collect Achievements).

Template cần thiết:
  btn_achievement.png - huy hiệu thành tựu đang chờ nhận trên trang trại
"""

import time

from modules.base import BaseModule


class AchievementsModule(BaseModule):
    name = "achievements"

    def run_cycle(self, cycle: int):
        cfg = self.config.get("achievements", {})
        if not cfg.get("enabled"):
            return
        if cycle % max(1, int(cfg.get("collect_every_cycles", 5))) != 0:
            return

        img = self.shot()
        medals = self.find(img, "btn_achievement", 0.80)
        if medals:
            self.log(f"[achievements] Nhận {len(medals)} thành tựu")
            self.tap_matches(medals, pause=0.6)
            self.adb.back()
            time.sleep(0.5)
        else:
            self.log("[achievements] Không có thành tựu nào chờ nhận.")
