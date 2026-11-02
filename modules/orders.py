"""
modules/orders.py - Bảng đơn hàng: gửi đơn (Send Orders), xoá đơn, xin giúp.

Template cần thiết:
  btn_orders.png        - bảng đơn hàng trên trang trại
  btn_send_order.png    - nút gửi đơn trên thẻ đơn
  btn_del_order.png     - nút xoá đơn
  btn_ask_help.png      - nút xin giúp đỡ
  btn_close.png         - nút đóng
"""

import time

from modules.base import BaseModule


class OrdersModule(BaseModule):
    name = "orders"

    def run_cycle(self, cycle: int):
        cfg = self.config.get("orders", {})
        if not cfg.get("enabled"):
            return
        if cycle % max(1, int(cfg.get("run_every_cycles", 5))) != 0:
            return

        if not cfg.get("send_orders") and not cfg.get("del_orders") \
                and not cfg.get("ask_for_help"):
            return

        if not self.tap_template("btn_orders", 0.80, tries=2):
            self.log("[orders] Không mở được bảng đơn hàng.")
            return
        time.sleep(1.2)

        sent = deleted = helped = 0
        if cfg.get("send_orders"):
            sent = self._send()
        if cfg.get("del_orders"):
            deleted = self._delete()
        if cfg.get("ask_for_help"):
            helped = self._ask_help()

        if not self.tap_template("btn_close", 0.80, tries=1):
            self.adb.back()
        time.sleep(0.6)
        self.log(f"[orders] Gửi {sent} đơn, xoá {deleted}, xin giúp {helped}.")

    def _tap_all(self, template: str) -> int:
        img = self.shot()
        matches = self.find(img, template, 0.80)
        if matches:
            self.tap_matches(matches, pause=0.6)
        return len(matches)

    def _send(self) -> int:
        n = self._tap_all("btn_send_order")
        if n:
            self.tap_template("btn_confirm", 0.80, tries=1)
        return n

    def _delete(self) -> int:
        return self._tap_all("btn_del_order")

    def _ask_help(self) -> int:
        return self._tap_all("btn_ask_help")
