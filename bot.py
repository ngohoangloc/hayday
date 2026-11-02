"""
bot.py - Bộ máy chính: vòng lặp treo máy, gọi các module theo chu kỳ.
"""

import os
import json
import time
import traceback

from adb_core import ADB, ADBError
from vision import TemplateStore

from modules.farming import FarmingModule
from modules.animals import AnimalsModule
from modules.production import ProductionModule
from modules.market import MarketModule


class HayDayBot:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        self.adb = ADB(
            adb_path=self.config["adb"].get("adb_path", "adb"),
            serial=self.config["adb"].get("serial"),
            package=self.config["adb"].get("package", "com.supercell.hayday"),
            activity=self.config["adb"].get("activity"),
        )
        self.templates = TemplateStore(self.config.get("templates_dir", "templates"))

        self.farming = FarmingModule(self.adb, self.templates, self.config, log=self.log)
        self.animals = AnimalsModule(self.adb, self.templates, self.config, log=self.log)
        self.production = ProductionModule(self.adb, self.templates, self.config, log=self.log)
        self.market = MarketModule(self.adb, self.templates, self.config, log=self.log)
        self.modules = [self.farming, self.animals, self.production, self.market]

        self.cycle = 0
        self.running = False

    # ------------------------------------------------------------------ #

    @staticmethod
    def log(msg: str):
        print(time.strftime("[%H:%M:%S]"), msg, flush=True)

    def check_device(self) -> str:
        serials = ADB.list_devices(self.config["adb"].get("adb_path", "adb"))
        if not serials:
            raise ADBError(
                "Không có thiết bị Android nào kết nối.\n"
                " - Bật 'Gỡ lỗi USB' trong Tùy chọn nhà phát triển\n"
                " - Cắm cáp và chạy: adb devices\n"
                " - Chấp nhận hộp thoại trên điện thoại."
            )
        if self.adb.serial and self.adb.serial not in serials:
            raise ADBError(f"Thiết bị {self.adb.serial} chưa kết nối. Đang có: {serials}")
        if not self.adb.serial:
            self.adb.serial = serials[0]
        self.log(f"Thiết bị: {self.adb.serial} | Màn hình: {self.adb.screen_size()}")
        return self.adb.serial

    def ensure_game(self):
        if not self.adb.is_package_running():
            wait = int(self.config.get("advanced", {}).get("game_open_wait_seconds", 120))
            self.log(f"Game chưa chạy - mở {self.adb.package}, chờ {wait}s...")
            self.adb.start_game(wait_seconds=min(wait, 60))
            # chờ thêm nếu cần
            deadline = time.time() + wait
            while time.time() < deadline and not self.adb.is_package_running():
                time.sleep(5)

    def missing_templates(self) -> list[str]:
        """Liệt kê template đang thiếu so với những gì config yêu cầu."""
        needed = set()
        cfg = self.config.get("plant_rotation", {})
        if cfg.get("enabled"):
            for c in cfg.get("crops", []):
                if c.get("enabled"):
                    needed.add(f"crop_ready_{c['name']}")
                    needed.add(f"seed_{c['name']}")
            needed.add("field_empty")
        acfg = self.config.get("animals", {})
        if acfg.get("enabled"):
            for t in acfg.get("types", []):
                if t.get("enabled"):
                    needed |= {f"animal_product_{t['name']}",
                               f"animal_hungry_{t['name']}",
                               f"animal_feed_{t['name']}"}
        pcfg = self.config.get("production", {})
        if pcfg.get("enabled"):
            for m in pcfg.get("machines", []):
                if m.get("enabled"):
                    needed |= {f"machine_{m['name']}", f"machine_ready_{m['name']}"}
                    for r in m.get("recipes", []):
                        if r.get("count", 0) > 0:
                            needed.add(f"recipe_{r['name']}")
            needed.add("btn_close")
        mcfg = self.config.get("market", {})
        if mcfg.get("enabled"):
            needed |= {"btn_shop", "market_slot_empty", "btn_price_low",
                       "btn_sell", "btn_confirm", "btn_advertise_free"}
            for i in mcfg.get("sell_items", []):
                if i.get("enabled"):
                    needed.add(f"item_{i['name']}")
        have = set(self.templates.list_available())
        return sorted(needed - have)

    # ------------------------------------------------------------------ #

    def run_cycle(self):
        self.cycle += 1
        self.log(f"===== CHU KỲ {self.cycle} =====")
        for module in self.modules:
            try:
                module.run_cycle(self.cycle)
            except Exception as exc:  # một module lỗi không dừng cả bot
                self.log(f"[{module.name}] LỖI: {exc}")
                self.log(traceback.format_exc(limit=2))

    def run(self, max_cycles: int | None = None, start_app: bool = True):
        gen_cfg = self.config.get("general", {})
        interval = int(gen_cfg.get("cycle_interval_seconds", 30))
        max_cycles = max_cycles if max_cycles else int(gen_cfg.get("max_cycles", 0)) or None

        self.check_device()
        missing = self.missing_templates()
        if missing:
            self.log("CẢNH BÁO - thiếu các template sau (module liên quan sẽ bỏ qua bước đó):")
            for m in missing:
                self.log(f"  - templates/{m}.png")
            self.log("Dùng: python tools/capture_templates.py để chụp thêm mẫu.")

        if start_app:
            self.ensure_game()

        self.running = True
        self.log(f"Bắt đầu treo máy. Ctrl+C để dừng.")
        try:
            while self.running:
                self.run_cycle()
                if max_cycles and self.cycle >= max_cycles:
                    self.log(f"Đã hoàn thành {max_cycles} chu kỳ - dừng.")
                    break
                self.log(f"Nghỉ {interval}s trước chu kỳ tiếp theo...")
                time.sleep(interval)
        except KeyboardInterrupt:
            self.log("Đã dừng theo yêu cầu người dùng.")
        finally:
            self.running = False
