"""
modules/followers.py - Remove Followers: xoá người theo dõi định kỳ.

Template cần thiết:
  btn_followers.png       - nút danh sách người theo dõi
  btn_remove_follower.png - nút xoá từng người theo dõi
  btn_confirm.png         - nút xác nhận
  btn_close.png           - nút đóng
"""

import time

from modules.base import BaseModule
from vision import center


class FollowersModule(BaseModule):
    name = "followers"

    def run_cycle(self, cycle: int):
        cfg = self.config.get("followers", {})
        if not cfg.get("enabled"):
            return
        if cycle % max(1, int(cfg.get("run_every_cycles", 20))) != 0:
            return

        if not self.tap_template("btn_followers", 0.80, tries=2):
            self.log("[followers] Không mở được danh sách theo dõi.")
            return
        time.sleep(1.0)

        removed = 0
        for _ in range(20):
            img = self.shot()
            btn = self.find_one(img, "btn_remove_follower", 0.80)
            if not btn:
                break
            self.adb.tap(*center(btn))
            time.sleep(0.5)
            self.tap_template("btn_confirm", 0.80, tries=1)
            removed += 1

        if not self.tap_template("btn_close", 0.80, tries=1):
            self.adb.back()
        time.sleep(0.5)
        self.log(f"[followers] Đã xoá {removed} người theo dõi.")
