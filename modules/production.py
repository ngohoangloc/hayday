"""
modules/production.py - Máy chế biến: Bakery, Dairy, Sugar Mill...

Template cần thiết:
  machine_<name>.png         - tòa nhà máy trên trang trại (để mở UI)
  machine_ready_<name>.png   - biểu tượng sản phẩm xong trên nóc máy
  recipe_<recipe>.png        - ô công thức trong UI máy
  btn_close.png              - nút X đóng cửa sổ máy
"""

import time

from modules.base import BaseModule
from vision import center


class ProductionModule(BaseModule):
    name = "production"

    def run_cycle(self, cycle: int):
        cfg = self.config.get("production", {})
        if not cfg.get("enabled"):
            return
        if cycle % max(1, int(cfg.get("run_every_cycles", 5))) != 0:
            return

        for machine in cfg.get("machines", []):
            if not machine.get("enabled"):
                continue
            every = max(1, int(machine.get("run_every_cycles",
                                           cfg.get("run_every_cycles", 5))))
            self._handle_machine(machine)

    def _handle_machine(self, machine: dict):
        name = machine["name"]
        self.log(f"[production] Xử lý {name}...")

        # 1) Thu thành phẩm đã xong (đứng ngoài trang trại)
        img = self.shot()
        ready = self.find(img, f"machine_ready_{name}", 0.80, "machine_area")
        if ready:
            self.log(f"[production] {name}: thu {len(ready)} thành phẩm")
            self.tap_matches(ready, pause=0.4)
            time.sleep(0.8)

        # 2) Mở máy và đặt công thức mới
        img = self.shot()
        door = self.find_one(img, f"machine_{name}", 0.80, "machine_area")
        if not door:
            self.log(f"[production] Không thấy máy {name} trên màn hình.")
            return
        self.adb.tap(*center(door))
        time.sleep(1.5)

        active = 0
        for recipe in machine.get("recipes", []):
            count = int(recipe.get("count", 0))
            if count <= 0:
                continue
            rname = recipe["name"]
            placed = self._start_recipe(rname, count)
            active += placed

        # 3) Đóng cửa sổ máy
        if not self.tap_template("btn_close", 0.80, tries=1):
            self.adb.back()
        time.sleep(0.6)

        if active:
            self.log(f"[production] {name}: đã đặt {active} lô sản xuất.")
        else:
            self.log(f"[production] {name}: không đặt thêm lô mới (kho nguyên liệu hoặc hàng đợi).")

    def _start_recipe(self, recipe_name: str, count: int) -> int:
        placed = 0
        for _ in range(count):
            img = self.shot()
            slot = self.find_one(img, f"recipe_{recipe_name}", 0.78)
            if not slot:
                break
            self.adb.tap(*center(slot))
            time.sleep(1.0)
            placed += 1
        return placed
