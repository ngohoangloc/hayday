"""
sim.py - MÁY ẢO GAME HAY DAY để phát triển & test bot ngay trên Linux/PC
không cần điện thoại thật.

- `SimWorld`  : trạng thái game (ruộng, kho, gia súc, máy, chợ, đơn hàng...)
- `render()`  : vẽ màn hình 1080x2340 + bảng hitbox cho từng phần tử
- `SimADB`    : thay thế ADB, cùng giao diện (screenshot/tap/swipe/drag/back)
  nên toàn bộ module bot chạy không cần sửa. Template cho bot được sinh tự
  động vào `templates_sim/` từ chính các sprite dùng để render => khớp 100%.
"""

import os
import shutil
import sys
import time

import cv2
import numpy as np

W, H = 1080, 2340
GRASS = (80, 170, 90)

# Thời gian mô phỏng (giây) - chỉnh trong config["sim"]
SIM_DEFAULTS = {
    "grow_seconds": 4,            # cây lớn (ghi đè bởi grow_seconds từng cây)
    "cook_seconds": 6,            # máy chế biến 1 lô
    "animal_product_seconds": 6,  # cho ăn -> có sản phẩm
    "hungry_seconds": 12,         # có sản phẩm -> đói lại
    "sale_seconds": 8,            # đăng quảng cáo -> bán được
    "achievement_regen": 60,      # thành tựu mới xuất hiện lại
    "silo_capacity": 100,
    "start_coins": 200,
    "start_wheat": 40,
    "dynamite_start": 5,
}

CROP_COLORS = {          # BGR - màu bông lúa/kn GREEN-RED
    "wheat":     (0, 230, 240),
    "corn":      (30, 200, 120),
    "carrot":    (0, 120, 255),
    "soybean":   (60, 200, 60),
    "sugarcane": (100, 220, 80),
}
CROP_NAMES = list(CROP_COLORS)

PRODUCTS = {             # sản phẩm của gia súc
    "chicken": ("egg",  (200, 220, 230)),
    "cow":     ("milk", (200, 200, 240)),
    "pig":     ("bacon", (150, 120, 190)),
    "sheep":   ("wool", (180, 180, 200)),
}
ANIMAL_COLORS = {
    "chicken": (150, 180, 90), "cow": (140, 140, 200),
    "pig": (160, 150, 220), "sheep": (170, 170, 210),
}
FEED_COLORS = {
    "chicken": (150, 180, 90), "cow": (140, 140, 200),
    "pig": (160, 150, 220), "sheep": (170, 170, 210),
}
MACHINES = {             # name -> (màu nhà máy, công thức: product -> (nguyên liệu, số lượng, giá bán thấp))
    "bakery": ((110, 90, 60), {
        "bread": ("wheat", 3, 20), "corn_bread": ("corn", 2, 35), "cookie": ("butter", 2, 60)}),
    "dairy": ((200, 150, 90), {
        "cream": ("milk", 2, 50), "butter": ("milk", 3, 70), "cheese": ("milk", 4, 90),
        "goat_cheese": ("milk", 5, 120)}),
    "sugar_mill": ((90, 110, 160), {
        "brown_sugar": ("sugarcane", 2, 40), "white_sugar": ("sugarcane", 3, 60),
        "syrup": ("sugarcane", 4, 90)}),
}
PRIMARY_PRODUCT = {"bakery": "bread", "dairy": "cream", "sugar_mill": "brown_sugar"}
CROP_PRICE = {"wheat": 10, "corn": 20, "carrot": 30, "soybean": 40, "sugarcane": 25}


def _canvas(w, h, bg=GRASS):
    return np.full((h, w, 3), bg, np.uint8)


def _round_rect(img, p1, p2, color, thickness=-1):
    cv2.rectangle(img, p1, p2, color, thickness)
    return img


# --------------------------------------------------------------------- #
# Xưởng sprite: dùng chung cho render và xuất template
# --------------------------------------------------------------------- #

def sprite_crop_ready(name):
    """Bông cây chín - nền màu cỏ để dán lên ruộng."""
    s = _canvas(70, 70)
    color = CROP_COLORS[name]
    if name == "carrot":
        cv2.fillPoly(s, [np.array([[35, 8], [20, 60], [50, 60]], np.int32)], color)
    elif name == "sugarcane":
        for dx in (-14, 0, 14):
            cv2.line(s, (35 + dx, 62), (35 + dx, 6), color, 6)
    elif name == "soybean":
        cv2.ellipse(s, (35, 40), (24, 16), 25, 0, 360, color, -1)
        cv2.ellipse(s, (30, 30), (14, 9), -20, 0, 360, color, -1)
    else:
        cv2.ellipse(s, (35, 40), (22, 26), 0, 0, 360, color, -1)
        for dx in (-8, 0, 8):
            cv2.line(s, (35 + dx, 30), (35 + dx * 2, 4), color, 3)
    return s


def sprite_seed(name):
    s = _canvas(60, 60, (60, 60, 60))          # nền thanh giống (xám đậm)
    color = CROP_COLORS[name]
    cv2.circle(s, (30, 38), 18, color, -1)
    cv2.fillPoly(s, [np.array([[30, 6], [22, 26], [38, 26]], np.int32)], color)
    return s


def sprite_field_empty():
    """Ô ruộng trống - màu đất (khớp soil.jpg). Viền lệch màu < ngưỡng 18."""
    s = _canvas(94, 54, (30, 70, 155))
    cv2.rectangle(s, (4, 4), (89, 49), (31, 82, 167), -1)
    return s


def sprite_field_growing():
    s = sprite_field_empty()
    # vuông (không phải tròn) để không nhầm với bong bóng tròn của gia súc
    cv2.rectangle(s, (41, 21), (53, 33), (60, 180, 60), -1)
    return s


def sprite_shed(name):
    s = _canvas(150, 90)
    cv2.rectangle(s, (5, 25), (144, 85), ANIMAL_COLORS[name], -1)
    cv2.fillPoly(s, [np.array([[5, 25], [75, 0], [144, 25]], np.int32)],
                 tuple(int(c * 0.6) for c in ANIMAL_COLORS[name]))
    return s


def sprite_bubble_ready(product, color):
    """Bong bóng sản phẩm - 34px, dấu hiệu bên trong khác nhau từng loại."""
    s = _canvas(34, 34)
    cv2.circle(s, (17, 17), 14, color, -1)
    cv2.circle(s, (17, 17), 14, (240, 240, 240), 2)
    if product == "egg":
        cv2.circle(s, (17, 17), 5, (0, 220, 230), -1)
    elif product == "milk":
        cv2.rectangle(s, (6, 22), (28, 27), (200, 100, 40), -1)
    elif product == "bacon":
        cv2.line(s, (7, 24), (27, 10), (60, 60, 200), 4)
    elif product == "wool":
        cv2.line(s, (7, 17), (27, 17), (90, 90, 90), 3)
        cv2.line(s, (17, 7), (17, 27), (90, 90, 90), 3)
    return s


def sprite_bubble_hungry():
    s = _canvas(34, 34)
    cv2.circle(s, (17, 17), 14, (235, 235, 235), -1)
    cv2.putText(s, "!", (11, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 220), 2)
    return s


def sprite_feed(name):
    s = _canvas(50, 50, (60, 60, 60))
    cv2.rectangle(s, (8, 6), (41, 44), FEED_COLORS[name], -1)
    cv2.line(s, (8, 16), (41, 16), (40, 40, 40), 3)
    return s


def sprite_machine(name):
    s = _canvas(130, 80)
    color = MACHINES[name][0]
    cv2.rectangle(s, (5, 20), (124, 75), color, -1)
    cv2.fillPoly(s, [np.array([[5, 20], [64, 0], [124, 20]], np.int32)],
                 tuple(int(c * 0.6) for c in color))
    return s


def sprite_product(name):
    """Vật phẩm chung (đạo cụ item và thành phẩm)."""
    colors = {p: c for p, (_, c) in PRODUCTS.items()}
    colors.update({r: (90, 140, 200) for m in MACHINES for r in MACHINES[m][1]})
    colors["ore"] = (120, 120, 140)
    s = _canvas(120, 120, (250, 245, 235))
    color = colors.get(name, (90, 140, 200))
    cv2.circle(s, (60, 52), 34, color, -1)
    cv2.rectangle(s, (10, 92), (109, 114), (230, 230, 230), -1)
    cv2.putText(s, name[:9], (14, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                (40, 40, 40), 1)
    return s


def sprite_recipe(product):
    s = _canvas(150, 110, (245, 240, 230))
    icon = cv2.resize(sprite_product(product), (60, 60))
    s[10:70, 45:105] = icon
    cv2.rectangle(s, (0, 0), (149, 109), (90, 90, 90), 3)
    return s


def sprite_btn(label, color, size=(120, 90), border=(40, 40, 40)):
    w, h = size
    s = _canvas(w, h, color)
    cv2.rectangle(s, (2, 2), (w - 3, h - 3), border, 3)
    cv2.putText(s, label[:8], (6, h // 2 + 6), cv2.FONT_HERSHEY_SIMPLEX,
                0.55, (255, 255, 255), 1)
    return s


def make_sprites():
    """Sinh toàn bộ sprite cần thiết (tên template -> ảnh BGR)."""
    sp = {}
    for c in CROP_NAMES:
        sp[f"crop_ready_{c}"] = sprite_crop_ready(c)
        sp[f"seed_{c}"] = sprite_seed(c)
        sp[f"item_{c}"] = sprite_product(c)
    sp["field_empty"] = sprite_field_empty()
    sp["field_growing"] = sprite_field_growing()
    for a in PRODUCTS:
        product, color = PRODUCTS[a]
        sp[f"animal_shed_{a}"] = sprite_shed(a)
        sp[f"animal_product_{a}"] = sprite_bubble_ready(product, color)
        sp[f"animal_hungry_{a}"] = sprite_bubble_hungry()
        sp[f"animal_feed_{a}"] = sprite_feed(a)
        sp[f"item_{product}"] = sprite_product(product)
    for m in MACHINES:
        sp[f"machine_{m}"] = sprite_machine(m)
        sp[f"machine_ready_{m}"] = sprite_product(PRIMARY_PRODUCT[m])
        for r in MACHINES[m][1]:
            sp[f"recipe_{r}"] = sprite_recipe(r)
            sp[f"item_{r}"] = sprite_product(r)
    sp["btn_shop"] = sprite_btn("SHOP", (250, 240, 230))
    sp["btn_orders"] = sprite_btn("ORDERS", (0, 215, 255))
    sp["btn_followers"] = sprite_btn("FRIENDS", (170, 200, 240))
    sp["btn_miner"] = sprite_btn("MINE", (120, 120, 130))
    sp["btn_achievement"] = sprite_btn("MEDAL", (0, 215, 255), (70, 70))
    sp["btn_close"] = sprite_btn("X", (60, 60, 230), (60, 60))
    sp["market_slot_empty"] = sprite_btn("", (200, 200, 205), (150, 150),
                                         (120, 120, 120))
    sp["btn_price_low"] = sprite_btn("LOW", (60, 180, 60), (180, 80))
    sp["btn_price_high"] = sprite_btn("HIGH", (60, 60, 220), (180, 80))
    sp["btn_sell"] = sprite_btn("SELL", (40, 130, 240), (180, 80))
    sp["btn_confirm"] = sprite_btn("OK", (60, 180, 60), (180, 80))
    sp["btn_advertise_free"] = sprite_btn("AD", (230, 170, 40), (50, 50))
    sp["btn_orders_card"] = sprite_btn("", (245, 240, 230), (700, 260),
                                       (120, 120, 120))
    sp["btn_send_order"] = sprite_btn("SEND", (60, 180, 60), (140, 70))
    sp["btn_del_order"] = sprite_btn("DEL", (60, 60, 230), (140, 70))
    sp["btn_ask_help"] = sprite_btn("HELP", (230, 170, 40), (140, 70))
    sp["btn_remove_follower"] = sprite_btn("DEL", (60, 60, 230), (120, 60))
    sp["btn_dynamite"] = sprite_btn("DYNO", (40, 40, 220), (80, 80))
    sp["btn_tnt"] = sprite_btn("TNT", (40, 40, 190), (80, 80))
    return sp


# --------------------------------------------------------------------- #
# Thế giới game
# --------------------------------------------------------------------- #

class SimWorld:
    def __init__(self, config):
        s = dict(SIM_DEFAULTS)
        s.update(config.get("sim", {}))
        self.settings = s
        self.coins = s["start_coins"]
        self.inventory = {c: s["start_wheat"] if c == "wheat" else 0
                          for c in CROP_NAMES}
        self.inventory.update({p: 0 for m in MACHINES
                               for p in MACHINES[m][1]})
        self.inventory.update({p: 0 for _, (p, _) in PRODUCTS.items()})
        self.inventory["ore"] = 0
        self.dynamite = s["dynamite_start"]
        self.fields = [{"crop": None, "planted_at": None} for _ in range(30)]
        self.animals = {a: {"hungry": [True] * 4, "ready": [False] * 4,
                            "fed_at": [0.0] * 4} for a in PRODUCTS}
        self.machines = {m: {"queue": []} for m in MACHINES}
        self.slots = [None] * 10                 # ô bán hàng chợ
        self.free_ads = 5
        self.achievement_ready = 1
        self.achievement_at = time.time() + s["achievement_regen"]
        self.orders = [self._new_order() for _ in range(3)]
        self.followers = ["user_%d" % i for i in range(1, 4)]
        self.selected_seed = None
        self.selected_feed = None
        self.pending = {}                        # trạng thái cửa sổ bán hàng
        self.pending_ore = []                    # (done_at)
        self.window = None                       # None = màn hình trang trại

    def _new_order(self):
        return {"item": "wheat", "qty": 5, "reward": 60}

    # ----- dòng thời gian ----- #
    def update(self):
        now = time.time()
        s = self.settings
        for a, st in self.animals.items():
            for i in range(4):
                if not st["hungry"][i] and not st["ready"][i] and \
                        now - st["fed_at"][i] >= s["animal_product_seconds"]:
                    st["ready"][i] = True
                if st["ready"][i] and now - st["fed_at"][i] > s["hungry_seconds"]:
                    st["ready"][i] = False
                    st["hungry"][i] = True
        for m, mq in self.machines.items():
            for job in mq["queue"]:
                if not job["done"] and now >= job["done_at"]:
                    job["done"] = True
        for i, slot in enumerate(self.slots):
            if slot and slot.get("advertised") and time.time() >= slot["sold_at"]:
                self.coins += slot["price"]
                self.slots[i] = None
        if self.achievement_ready == 0 and time.time() >= self.achievement_at:
            self.achievement_ready = 1
        done_ore = [t for t in self.pending_ore if time.time() >= t]
        if done_ore:
            self.inventory["ore"] += 2 * len(done_ore)
            self.pending_ore = [t for t in self.pending_ore if time.time() < t]


# --------------------------------------------------------------------- #
# Render màn hình
# --------------------------------------------------------------------- #

FIELD_X0, FIELD_Y0, TW, TH = 300, 1300, 100, 60
ROW_XOFF = 20
PEN_POS = {"chicken": (80, 850), "cow": (560, 850),
           "pig": (80, 1030), "sheep": (560, 1030)}
MACHINE_POS = {"bakery": (150, 1650), "dairy": (450, 1650), "sugar_mill": (750, 1650)}
FEED_BAR_Y = 1900
SEED_BAR_Y = 2200

BTN_POS = {"btn_orders": (60, 80), "btn_followers": (230, 80),
           "btn_miner": (760, 80), "btn_shop": (950, 80)}


class Renderer:
    def __init__(self, sprites, world, config):
        self.sp = sprites
        self.world = world
        self.enabled_crops = [c["name"] for c in
                              config["plant_rotation"]["crops"] if c["enabled"]]
        self.enabled_animals = [a["name"] for a in
                                config["animals"]["types"] if a["enabled"]]
        self.enabled_machines = [m["name"] for m in
                                 config["production"]["machines"] if m["enabled"]]

    def render(self):
        if self.world.window is None:
            return self.render_farm()
        w = self.world.window
        if w == "shop":
            return self.render_shop()
        if w == "shop_item":
            return self.render_shop_item()
        if w == "shop_price":
            return self.render_shop_price()
        if w == "shop_confirm":
            return self.render_confirm()
        if w and w.startswith("machine:"):
            return self.render_machine(w.split(":", 1)[1])
        if w == "orders":
            return self.render_orders()
        if w == "followers":
            return self.render_followers()
        if w == "miner":
            return self.render_miner()
        return self.render_farm()

    # ----- helpers ----- #
    def _panel(self):
        img = _canvas(W, H, (70, 70, 75))
        cv2.rectangle(img, (0, 0), (W - 1, 260), (50, 50, 55), -1)
        return img, []

    def _paste(self, img, hitboxes, name, x, y, action=None, data=None):
        s = self.sp[name]
        h, w = s.shape[:2]
        img[y:y + h, x:x + w] = s
        if action:
            hitboxes.append((x, y, w, h, action, data))
        return img

    # ----- trang trại ----- #
    def render_farm(self):
        img = _canvas(W, H)
        hb = []
        cv2.rectangle(img, (0, 0), (W - 1, 200), (60, 60, 60), -1)
        for name, (x, y) in BTN_POS.items():
            self._paste(img, hb, name, x, y, "open_window", name[4:])
        wd = self.world
        if wd.achievement_ready > 0:
            self._paste(img, hb, "btn_achievement", 500, 100, "achievement")
        # ruộng
        for i, tile in enumerate(wd.fields):
            r, c = divmod(i, 6)
            x = FIELD_X0 + c * TW + r * ROW_XOFF
            y = FIELD_Y0 + r * TH
            if tile["crop"] is None:
                img[y:y + 54, x:x + 94] = self.sp["field_empty"]
                hb.append((x, y, 94, 54, "field", i))
            elif time.time() - tile["planted_at"] >= tile.get("grow", 120):
                img[y:y + 54, x:x + 94] = self.sp["field_empty"]
                ready = self.sp[f"crop_ready_{tile['crop']}"]
                img[y - 45:y + 25, x + 12:x + 82] = ready
                hb.append((x, y, 94, 54, "field", i))
            else:
                img[y:y + 54, x:x + 94] = self.sp["field_growing"]
        # gia súc
        fy = 0
        for a in self.enabled_animals:
            px, py = PEN_POS[a]
            self._paste(img, hb, f"animal_shed_{a}", px, py, "noop")
            st = wd.animals[a]
            for j in range(4):
                bx = px + 4 + j * 36          # không chồng nhau (34px + 2px hở)
                if st["ready"][j]:
                    self._paste(img, hb, f"animal_product_{a}", bx, py - 40,
                                "collect", (a, j))
                elif st["hungry"][j]:
                    self._paste(img, hb, f"animal_hungry_{a}", bx, py - 40,
                                "feed", (a, j))
            self._paste(img, hb, f"animal_feed_{a}", 920, FEED_BAR_Y + fy * 60,
                        "select_feed", a)
            fy += 1
        # máy
        for m in self.enabled_machines:
            mx, my = MACHINE_POS[m]
            self._paste(img, hb, f"machine_{m}", mx, my, "open_machine", m)
            if any(j["done"] for j in wd.machines[m]["queue"]):
                self._paste(img, hb, f"machine_ready_{m}", mx + 45, my - 45,
                            "collect_machine", m)
        # thanh hạt giống
        for i, c in enumerate(self.enabled_crops):
            self._paste(img, hb, f"seed_{c}", 460 + i * 80, SEED_BAR_Y,
                        "select_seed", c)
        return img, hb

    # ----- cửa sổ máy ----- #
    def render_machine(self, m):
        img, hb = self._panel()
        wd = self.world
        i = 0
        for r in MACHINES[m][1]:
            self._paste(img, hb, f"recipe_{r}", 200 + (i % 4) * 170,
                        800 + (i // 4) * 160, "queue_recipe", (m, r))
            i += 1
        self._paste(img, hb, "btn_close", 950, 150, "close")
        return img, hb

    # ----- chợ ----- #
    def render_shop(self):
        img, hb = self._panel()
        for i, slot in enumerate(self.world.slots):
            x, y = 140 + (i % 5) * 170, 500 + (i // 5) * 210
            if slot is None:
                self._paste(img, hb, "market_slot_empty", x, y,
                            "open_slot", i)
            else:
                item = cv2.resize(self.sp[f"item_{slot['item']}"], (150, 150))
                img[y:y + 150, x:x + 150] = item
                hb.append((x, y, 150, 150, "noop", None))
                if not slot["advertised"] and self.world.free_ads > 0:
                    self._paste(img, hb, "btn_advertise_free", x + 95, y + 95,
                                "advertise", i)
        self._paste(img, hb, "btn_close", 950, 150, "close")
        return img, hb

    def render_shop_item(self):
        img, hb = self._panel()
        i = 0
        for name, qty in self.world.inventory.items():
            if qty > 0 and f"item_{name}" in self.sp:
                self._paste(img, hb, f"item_{name}", 200 + (i % 5) * 150,
                            600 + (i // 5) * 180, "pick_item", name)
                i += 1
        self._paste(img, hb, "btn_close", 950, 150, "close")
        return img, hb

    def render_shop_price(self):
        img, hb = self._panel()
        pend = self.world.pending
        item = pend.get("item")
        if item:
            icon = cv2.resize(self.sp[f"item_{item}"], (180, 180))
            img[400:580, 450:630] = icon
        self._paste(img, hb, "btn_price_low", 250, 1400, "price", "low")
        self._paste(img, hb, "btn_price_high", 650, 1400, "price", "high")
        self._paste(img, hb, "btn_sell", 450, 1650, "sell")
        self._paste(img, hb, "btn_close", 950, 150, "close")
        return img, hb

    def render_confirm(self):
        img, hb = self._panel()
        cv2.rectangle(img, (240, 900), (840, 1500), (90, 90, 95), -1)
        self._paste(img, hb, "btn_confirm", 450, 1150, "confirm_sell")
        self._paste(img, hb, "btn_close", 950, 150, "close")
        return img, hb

    # ----- đơn hàng ----- #
    def render_orders(self):
        img, hb = self._panel()
        for i, order in enumerate(self.world.orders):
            y = 350 + i * 300
            self._paste(img, hb, "btn_orders_card", 100, y, "noop")
            icon = cv2.resize(self.sp[f"item_{order['item']}"], (110, 110))
            img[y + 20:y + 130, 140:250] = icon
            if self.world.inventory.get(order["item"], 0) >= order["qty"]:
                self._paste(img, hb, "btn_send_order", 550, y + 40, "send_order", i)
            self._paste(img, hb, "btn_del_order", 550, y + 160, "del_order", i)
        self._paste(img, hb, "btn_close", 950, 150, "close")
        return img, hb

    def render_followers(self):
        img, hb = self._panel()
        for i, name in enumerate(self.world.followers):
            y = 400 + i * 250
            cv2.rectangle(img, (150, y), (750, y + 120), (110, 110, 115), -1)
            cv2.putText(img, name, (180, y + 70), cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, (255, 255, 255), 1)
            self._paste(img, hb, "btn_remove_follower", 560, y + 30,
                        "remove_follower", i)
        self._paste(img, hb, "btn_close", 950, 150, "close")
        return img, hb

    def render_miner(self):
        img, hb = self._panel()
        if self.world.dynamite > 0:
            self._paste(img, hb, "btn_dynamite", 300, 800, "dynamite")
        self._paste(img, hb, "btn_tnt", 600, 800, "tnt")
        self._paste(img, hb, "btn_close", 950, 150, "close")
        return img, hb


# --------------------------------------------------------------------- #
# SimADB - thay ADB cho toàn bộ bot
# --------------------------------------------------------------------- #

class SimADB:
    """Cùng giao diện với adb_core.ADB nhưng điều khiển thế giới mô phỏng."""

    def __init__(self, config, templates_dir="templates_sim"):
        self.world = SimWorld(config)
        self.sprites = make_sprites()
        self.renderer = Renderer(self.sprites, self.world, config)
        self.templates_dir = templates_dir
        self._crop_cfg = config["plant_rotation"]["crops"]
        self._write_templates()
        self._hitboxes = []

    # ----- xuất template cho bot (khớp pixel với render) ----- #
    def _write_templates(self):
        d = self.templates_dir
        os.makedirs(d, exist_ok=True)
        for name, img in self.sprites.items():
            cv2.imwrite(os.path.join(d, name + ".png"), img)
        soil_dst = os.path.join(d, "soil.jpg")
        if not os.path.isfile(soil_dst):
            base = getattr(sys, "_MEIPASS", None) or os.path.dirname(os.path.abspath(__file__))
            for src in (os.path.join(base, "templates", "soil.jpg"),
                        os.path.join("templates", "soil.jpg"),
                        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "templates", "soil.jpg")):
                if os.path.isfile(src):
                    shutil.copy(src, soil_dst)
                    break
            else:
                cv2.imwrite(soil_dst, sprite_field_empty())
        # kích thước tile/hàng dùng cho drag
        self.tile_boxes = self._field_boxes()

    def _field_boxes(self):
        boxes = []
        for i in range(30):
            r, c = divmod(i, 6)
            boxes.append((FIELD_X0 + c * TW + r * ROW_XOFF,
                          FIELD_Y0 + r * TH))
        return boxes

    # ----- giao diện giống ADB ----- #
    def screen_size(self):
        return (W, H)

    def screenshot(self):
        self.world.update()
        img, self._hitboxes = self.renderer.render()
        return img

    def tap(self, x, y):
        self.world.update()
        # duyệt NGƯỢC thứ tự vẽ: phần tử vẽ sau (nút con) đè phần tử vẽ trước
        for hx, hy, hw, hh, action, data in reversed(self._hitboxes):
            if hx <= x < hx + hw and hy <= y < hy + hh:
                self._dispatch(action, data)
                return

    def _dispatch(self, action, data):
        wd = self.world
        s = wd.settings
        now = time.time()
        if action == "open_window":
            wd.window = data
        elif action == "close":
            wd.window = None
            wd.pending = {}
        elif action == "achievement":
            wd.achievement_ready -= 1
            wd.coins += 50
            wd.achievement_at = now + s["achievement_regen"]
        elif action == "field":
            tile = wd.fields[data]
            if tile["crop"] and now - tile["planted_at"] >= tile["grow"]:
                cap = s["silo_capacity"]
                have = sum(wd.inventory[c] for c in CROP_NAMES)
                if have + 2 <= cap:
                    wd.inventory[tile["crop"]] += 2
                    tile["crop"] = None
                    tile["planted_at"] = None
            elif tile["crop"] is None and wd.selected_seed:
                tile["crop"] = wd.selected_seed
                tile["planted_at"] = now
                tile["grow"] = self._grow_seconds(wd.selected_seed)
        elif action == "select_seed":
            wd.selected_seed = data
        elif action == "select_feed":
            wd.selected_feed = data
        elif action == "feed":
            a, j = data
            if wd.selected_feed == a and wd.animals[a]["hungry"][j]:
                st = wd.animals[a]
                st["hungry"][j] = False
                st["fed_at"][j] = now
        elif action == "collect":
            a, j = data
            if wd.animals[a]["ready"][j]:
                wd.animals[a]["ready"][j] = False
                product, _ = PRODUCTS[a]
                wd.inventory[product] += 1
        elif action == "open_machine":
            wd.window = f"machine:{data}"
        elif action == "queue_recipe":
            m, r = data
            ingr, need, _ = MACHINES[m][1][r]
            mq = wd.machines[m]
            if len(mq["queue"]) < 4 and wd.inventory.get(ingr, 0) >= need:
                wd.inventory[ingr] -= need
                mq["queue"].append({"recipe": r, "done": False,
                                    "done_at": now + s["cook_seconds"]})
        elif action == "collect_machine":
            mq = wd.machines[data]
            for job in [j for j in mq["queue"] if j["done"]]:
                wd.inventory[job["recipe"]] += 1
            mq["queue"] = [j for j in mq["queue"] if not j["done"]]
        elif action == "open_slot":
            wd.window = "shop_item"
            wd.pending["slot"] = data
        elif action == "pick_item":
            wd.pending["item"] = data
            wd.pending["price"] = None
            wd.window = "shop_price"
        elif action == "price":
            wd.pending["price"] = data
        elif action == "sell":
            if wd.pending.get("item"):
                wd.window = "shop_confirm"
        elif action == "confirm_sell":
            if "remove" in wd.pending:
                i = wd.pending.pop("remove")
                if i < len(wd.followers):
                    del wd.followers[i]
                wd.window = "followers"
                return
            item = wd.pending.get("item")
            slot_i = wd.pending.get("slot")
            price = CROP_PRICE.get(item, 40)
            if item and wd.inventory.get(item, 0) > 0 and slot_i is not None \
                    and wd.slots[slot_i] is None:
                wd.inventory[item] -= 1
                wd.slots[slot_i] = {"item": item, "price": price,
                                    "advertised": False, "sold_at": None}
            wd.pending = {}
            wd.window = "shop"
        elif action == "advertise":
            slot = wd.slots[data]
            if slot and not slot["advertised"]:
                slot["advertised"] = True
                slot["sold_at"] = now + s["sale_seconds"]
        elif action == "send_order":
            o = wd.orders[data]
            if wd.inventory.get(o["item"], 0) >= o["qty"]:
                wd.inventory[o["item"]] -= o["qty"]
                wd.coins += o["reward"]
                wd.orders[data] = wd._new_order()
        elif action == "del_order":
            wd.orders[data] = wd._new_order()
        elif action == "remove_follower":
            wd.pending["remove"] = data
            wd.window = "shop_confirm"     # dùng chung hộp thoại xác nhận
        elif action == "dynamite":
            if wd.dynamite > 0:
                wd.dynamite -= 1
                wd.inventory["ore"] += 2
        elif action == "tnt":
            wd.inventory["ore"] += 4

    def _grow_seconds(self, crop):
        for c in self._crop_cfg:
            if c["name"] == crop:
                return c.get("grow_seconds", 120)
        return 120

    # ----- drag theo hàng (kỹ thuật InfiniFarm) ----- #
    def drag_row(self, y, x1, x2, ms=700, jiggle_px=0):
        self.world.update()
        radius = TH / 2
        segs = [(x1, y, x2, y)]
        if jiggle_px:
            segs += [(x2, y - jiggle_px, x1, y - jiggle_px),
                     (x1, y + jiggle_px, x2, y + jiggle_px)]
        touched = set()
        for i, (tx, ty) in enumerate(self.tile_boxes):
            ccx, ccy = tx + 47, ty + 27
            for ax1, ay1, ax2, ay2 in segs:
                if _dist_point_seg(ccx, ccy, ax1, ay1, ax2, ay2) <= radius:
                    touched.add(i)
        for i in touched:
            self._dispatch("field", i)

    def drag_rows(self, rows, ms=700, jiggle_px=0, pause=0.4):
        for i, (y, x1, x2) in enumerate(rows):
            if i % 2 == 1:
                x1, x2 = x2, x1
            self.drag_row(y, x1, x2, ms=ms, jiggle_px=jiggle_px)

    def swipe(self, x1, y1, x2, y2, ms=400):
        self.drag_row(y1, x1, x2, ms=ms, jiggle_px=0)

    def back(self):
        if self.world.window:
            self.world.window = None
            self.world.pending = {}

    def is_package_running(self):
        return True

    def start_game(self, wait_seconds=45):
        pass

    def stop_game(self):
        pass

    def tap_fraction(self, fx, fy):
        self.tap(int(fx * W), int(fy * H))

    # thuộc tính phụ để test đọc trạng thái
    def bind_crop_cfg(self, crop_cfg):
        self._crop_cfg = crop_cfg


def _dist_point_seg(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    if dx == dy == 0:
        return float(np.hypot(px - x1, py - y1))
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
    return float(np.hypot(px - (x1 + t * dx), py - (y1 + t * dy)))
