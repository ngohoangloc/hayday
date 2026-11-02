"""
tools/calibrate.py - Kiểm tra thiết bị và hiệu chỉnh toạ độ.

Cách dùng:
    python tools/calibrate.py            # kiểm tra thiết bị + chụp màn hình thử
    python tools/calibrate.py --grid     # hiện lưới tỉ lệ để đo vùng regions
    python tools/calibrate.py --tap 0.5 0.5   # thử chạm giữa màn hình
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2

from bot import HayDayBot
from vision import annotate


def show_grid(bot: HayDayBot):
    img = bot.adb.screenshot()
    h, w = img.shape[:2]
    for i in range(1, 10):
        fx = i / 10
        fy = i / 10
        cv2.line(img, (int(fx * w), 0), (int(fx * w), h), (0, 255, 0), 1)
        cv2.putText(img, f"{fx:.1f}", (int(fx * w) + 2, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
        cv2.line(img, (0, int(fy * h)), (w, int(fy * h)), (0, 255, 0), 1)
        cv2.putText(img, f"{fy:.1f}", (4, int(fy * h) - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
    out = "debug_grid.png"
    cv2.imwrite(out, img)
    bot.log(f"Đã lưu lưới tỉ lệ: {out} (kích thước gốc {w}x{h})")
    # Vẽ luôn các vùng đang config
    drawn = img.copy()
    for key, frac in bot.config.get("regions", {}).items():
        if not isinstance(frac, list):
            continue
        h2, w2 = drawn.shape[:2]
        x1, y1 = int(frac[0] * w2), int(frac[1] * h2)
        x2, y2 = int(frac[2] * w2), int(frac[3] * h2)
        cv2.rectangle(drawn, (x1, y1), (x2, y2), (0, 0, 255), 2)
        cv2.putText(drawn, key, (x1 + 4, y1 + 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    cv2.imwrite("debug_regions.png", drawn)
    bot.log("Đã lưu debug_regions.png - kiểm tra các vùng regions có đúng vị trí không.")


def tap_fraction(bot: HayDayBot, fx: float, fy: float):
    bot.log(f"Chạm tại ({fx:.2f}, {fy:.2f}) sau 3 giây...")
    import time
    time.sleep(3)
    bot.adb.tap_fraction(fx, fy)
    bot.log("Đã chạm.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--grid", action="store_true", help="Xuất ảnh lưới tỉ lệ")
    parser.add_argument("--tap", nargs=2, type=float, metavar=("FX", "FY"),
                        help="Thử chạm theo tỉ lệ")
    args = parser.parse_args()

    bot = HayDayBot("config.json")
    bot.check_device()

    if args.grid:
        show_grid(bot)
    elif args.tap:
        tap_fraction(bot, args.tap[0], args.tap[1])
    else:
        img = bot.adb.screenshot()
        cv2.imwrite("debug_screen.png", img)
        bot.log(f"Chụp thử OK: {img.shape[1]}x{img.shape[0]} -> debug_screen.png")


if __name__ == "__main__":
    main()
