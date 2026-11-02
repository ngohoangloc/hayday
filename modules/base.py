"""
modules/base.py - Lớp cơ sở cho mọi module tự động.
"""

import os
import time

import cv2

from vision import TemplateStore, find_all, find_best, center, crop_region, annotate


class BaseModule:
    name = "base"

    def __init__(self, adb, templates: TemplateStore, config: dict, log=print):
        self.adb = adb
        self.tpl = templates
        self.config = config
        self.log = log

    # ---------- Tiện ích chung ---------- #

    def shot(self):
        return self.adb.screenshot()

    def region(self, key: str):
        frac = self.config.get("regions", {}).get(key)
        return crop_region(self.shot(), frac) if frac else None

    def find(self, image, template_name: str, threshold: float = 0.80, region_key: str | None = None):
        """Tìm template; tự bỏ qua nếu thiếu file template."""
        if not self.tpl.exists(template_name):
            self.log(f"[{self.name}] Cần template '{template_name}.png' - bỏ qua bước này.")
            return []
        region = crop_region(image, self.config["regions"][region_key]) if region_key else None
        return find_all(image, self.tpl.get(template_name), threshold, region=region)

    def find_one(self, image, template_name: str, threshold: float = 0.80, region_key: str | None = None):
        matches = self.find(image, template_name, threshold, region_key)
        return matches[0] if matches else None

    def tap_matches(self, matches, pause: float = 0.35, max_taps: int = 50, reverse: bool = False):
        """Chạm lần lượt vào các kết quả tìm được (y tăng dần để không che nhau)."""
        if reverse:
            matches = list(reversed(matches))
        else:
            matches = sorted(matches, key=lambda m: (m[1], m[0]))
        for m in matches[:max_taps]:
            x, y = center(m)
            self.adb.tap(x, y)
            time.sleep(pause)

    def tap_template(self, template_name: str, threshold: float = 0.80,
                     region_key: str | None = None, tries: int = 2) -> bool:
        """Tìm và chạm 1 template. True nếu chạm được."""
        for _ in range(tries):
            img = self.shot()
            m = self.find_one(img, template_name, threshold, region_key)
            if m:
                x, y = center(m)
                self.adb.tap(x, y)
                time.sleep(0.5)
                return True
            time.sleep(0.8)
        return False

    def save_debug(self, image, tag: str):
        dbg = self.config.get("general", {}).get("screenshot_debug_dir", "debug")
        if self.config.get("general", {}).get("save_debug_screens"):
            os.makedirs(dbg, exist_ok=True)
            path = os.path.join(dbg, f"{time.strftime('%H%M%S')}_{tag}.png")
            cv2.imwrite(path, image)
