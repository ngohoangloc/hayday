"""
modules/market.py - Market Operations: bán sản phẩm & quản lý quảng cáo.

Template cần thiết:
  btn_shop.png            - nút mở cửa hàng (biển quảng cáo ở góc)
  market_slot_empty.png   - ô bán hàng trống trong cửa hàng
  item_<name>.png         - vật phẩm trong danh sách chọn khi bán
  btn_price_low.png       - nút chọn giá "Thấp"
  btn_price_high.png      - nút chọn giá "Cao"
  btn_sell.png            - nút "Bán"
  btn_confirm.png         - nút xác nhận
  btn_advertise.png       - nút quảng cáo ô bán hàng
  btn_advertise_free.png  - biểu tượng quảng cáo còn miễn phí
"""

import time

from modules.base import BaseModule
from vision import center


class MarketModule(BaseModule):
    name = "market"

    def run_cycle(self, cycle: int):
        cfg = self.config.get("market", {})
        if not cfg.get("enabled"):
            return
        if cycle % max(1, int(cfg.get("sell_every_cycles", 1))) != 0:
            return
        self.sell_items(cycle)
        if cfg.get("material_selling", {}).get("enabled"):
            self.sell_materials(cycle)

    # ------------------------------------------------------------------ #

    def sell_items(self, cycle: int):
        cfg = self.config["market"]
        items = [i for i in cfg.get("sell_items", []) if i.get("enabled")]
        if not items:
            self.log("[market] Không có vật phẩm nào được bật để bán.")
            return

        if not self.tap_template("btn_shop", 0.80, tries=3):
            self.log("[market] Không mở được cửa hàng.")
            return
        time.sleep(1.5)

        slots = int(cfg.get("slots_per_cycle", 10))
        sold = 0
        for _ in range(slots):
            if not self._sell_one_slot(items, cfg):
                break
            sold += 1

        if cfg.get("manage_advertisements"):
            self._manage_ads()

        self.adb.back()
        time.sleep(0.8)
        self.log(f"[market] Đã bán {sold} ô trong chu kỳ này.")

    def _sell_one_slot(self, items, cfg) -> bool:
        """Bán một lô vào ô trống. Trả về False nếu hết ô/không tiếp tục được."""
        img = self.shot()
        slot = self.find_one(img, "market_slot_empty", 0.80, "shop_area")
        if not slot:
            return False
        self.adb.tap(*center(slot))
        time.sleep(1.2)

        # Chọn vật phẩm bán
        chosen = None
        for item in items:
            m = self.find_one(self.shot(), f"item_{item['name']}", 0.78, "shop_area")
            if m:
                chosen = m
                break
        if not chosen:
            self.log("[market] Không tìm thấy vật phẩm nào trong kho để bán.")
            self.adb.back()
            time.sleep(0.6)
            return False
        self.adb.tap(*center(chosen))
        time.sleep(0.8)

        # Chọn mức giá
        price = cfg.get("price_option", "low")
        price_btn = "btn_price_low" if price == "low" else "btn_price_high"
        self.tap_template(price_btn, 0.80, tries=1)
        time.sleep(0.3)

        # Bán + xác nhận
        ok = self.tap_template("btn_sell", 0.80, tries=2)
        if ok:
            time.sleep(0.5)
            self.tap_template("btn_confirm", 0.80, tries=1)
            time.sleep(0.5)
        return ok

    def _manage_ads(self):
        cfg = self.config["market"]
        img = self.shot()
        free = self.find(img, "btn_advertise_free", 0.78, "shop_area")
        if not free:
            self.log("[market] Không có ô quảng cáo miễn phí nào.")
            return
        if cfg.get("advert_only_when_full"):
            self.log(f"[market] Quảng cáo {len(free)} ô còn lượt miễn phí.")
        self.tap_matches(free, pause=0.6)

    def sell_materials(self, cycle: int):
        mcfg = self.config["market"]["material_selling"]
        mats = [m for m in mcfg.get("materials", []) if m.get("enabled")]
        if not mats:
            return
        if cycle % max(1, int(mcfg.get("sell_every_cycles", 10))) != 0:
            return
        self.log(f"[market] Bán vật liệu xây dựng: {', '.join(m['name'] for m in mats)}")
        # Vật liệu bán cùng cơ chế ô bán hàng; danh sách item_xxx phải có template.
        items = [{"name": m["name"], "enabled": True} for m in mats]
        if not self.tap_template("btn_shop", 0.80, tries=3):
            return
        time.sleep(1.5)
        for _ in range(len(mats)):
            if not self._sell_one_slot(items, {**self.config["market"],
                                               "price_option": mcfg.get("price_option", "high")}):
                break
        self.adb.back()
        time.sleep(0.8)
