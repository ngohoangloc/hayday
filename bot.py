"""
bot.py - Bộ máy chính: vòng lặp treo máy, gọi các module theo chu kỳ.
"""

import os
import sys
import json
import time
import traceback

from adb_core import ADB, ADBError
from vision import TemplateStore


def app_dir() -> str:
    """Thư mục ghi được bên cạnh chương trình (exe/AppImage/script)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def bundle_dir() -> str:
    """Thư mục tài nguyên đọc-only nhúng trong binary (PyInstaller)."""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", app_dir())
    return os.path.dirname(os.path.abspath(__file__))


def resolve_config_path(config_path: str) -> str:
    if os.path.isfile(config_path):
        return config_path
    for base in (app_dir(), bundle_dir()):
        cand = os.path.join(base, config_path)
        if os.path.isfile(cand):
            return cand
    return config_path


def resolve_templates_dir(td: str) -> str:
    """Ưu tiên thư mục templates ghi được cạnh chương trình (người dùng bổ sung
    template), nếu trống thì dùng templates nhúng trong binary."""
    if os.path.isabs(td):
        return td
    app = os.path.join(app_dir(), td)
    if os.path.isdir(app) and any(
            f.lower().endswith((".png", ".jpg", ".jpeg"))
            for f in os.listdir(app)):
        return app
    bundled = os.path.join(bundle_dir(), td)
    if os.path.isdir(bundled):
        return bundled
    return app

from modules.farming import FarmingModule
from modules.animals import AnimalsModule
from modules.production import ProductionModule
from modules.market import MarketModule
from modules.orders import OrdersModule
from modules.achievements import AchievementsModule
from modules.miner import MinerModule
from modules.followers import FollowersModule


class HayDayBot:
    def __init__(self, config_path: str = "config.json", use_sim: bool = False):
        self.config_path = resolve_config_path(config_path)
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)
        self.use_sim = use_sim

        # resolve thư mục template TRƯỚC khi tạo SimADB (nó cần ghi template vào đó)
        td = resolve_templates_dir(self.config.get("templates_dir", "templates"))
        self.config["templates_dir"] = td

        if use_sim:
            from sim import SimADB
            td = resolve_templates_dir("templates_sim")   # sim luôn dùng thư mục riêng
            self.config["templates_dir"] = td
            # vùng màn hình riêng của thế giới mô phỏng (máy thật chỉnh regions phía trên)
            self.config["regions"] = {
                "field_area":   [0.03, 0.55, 0.97, 0.72],
                "seed_bar":     [0.25, 0.90, 0.75, 1.00],
                "animal_area":  [0.03, 0.32, 0.95, 0.52],
                "machine_area": [0.03, 0.68, 0.97, 0.75],
                "shop_area":    [0.10, 0.10, 0.90, 0.90],
            }
            self.adb = SimADB(self.config, templates_dir=td)
        else:
            self.adb = ADB(
                adb_path=self.config["adb"].get("adb_path", "adb"),
                serial=self.config["adb"].get("serial"),
                package=self.config["adb"].get("package", "com.supercell.hayday"),
                activity=self.config["adb"].get("activity"),
            )
        self.templates = TemplateStore(td)

        # SoilDetector (kỹ thuật h8d13/HayDay): chỉ tạo nếu đủ điều kiện
        self.soil_detector = None
        sdcfg = self.config.get("soil_detection", {})
        if sdcfg.get("enabled") and self.templates.exists(
                os.path.splitext(sdcfg.get("template", "soil.jpg"))[0]):
            from soil import SoilDetector
            self.soil_detector = SoilDetector(
                os.path.join(self.config.get("templates_dir", "templates"),
                             sdcfg.get("template", "soil.jpg")),
                color_threshold=float(sdcfg.get("color_threshold", 18)),
                min_area_ratio=float(sdcfg.get("min_area_ratio", 0.01)),
                step_ratio=float(sdcfg.get("sweep_step_ratio", 0.12)),
            )
            self.log("SoilDetector sẵn sàng (nhận diện ruộng theo màu).")

        self.market = MarketModule(self.adb, self.templates, self.config, log=self.log)
        self.farming = FarmingModule(self.adb, self.templates, self.config, log=self.log,
                                     soil_detector=self.soil_detector, market_module=self.market)
        self.animals = AnimalsModule(self.adb, self.templates, self.config, log=self.log)
        self.production = ProductionModule(self.adb, self.templates, self.config, log=self.log)
        self.orders = OrdersModule(self.adb, self.templates, self.config, log=self.log)
        self.achievements = AchievementsModule(self.adb, self.templates, self.config, log=self.log)
        self.miner = MinerModule(self.adb, self.templates, self.config, log=self.log)
        self.followers = FollowersModule(self.adb, self.templates, self.config, log=self.log)
        self.modules = [self.farming, self.animals, self.production, self.market,
                        self.orders, self.achievements, self.miner, self.followers]

        self.cycle = 0
        self.running = False

    # ------------------------------------------------------------------ #

    @staticmethod
    def log(msg: str):
        print(time.strftime("[%H:%M:%S]"), msg, flush=True)

    def check_device(self) -> str:
        if self.use_sim:
            self.log("CHẾ ĐỘ MÔ PHỎNG - không cần thiết bị Android.")
            return "sim"
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
        if self.use_sim:
            return
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
