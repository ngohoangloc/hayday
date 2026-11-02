"""
tools/capture_templates.py - Công cụ chụp template (mẫu hình ảnh) cho bot.

Cách dùng:
    python tools/capture_templates.py

Mỗi vòng:
 1. Chụp màn hình điện thoại hiện tại.
 2. Cửa sổ OpenCV hiện ra - KÉO CHUỘT chọn các khung (ROI) chứa biểu tượng
    cần làm mẫu (ví dụ cây lúa chín, nút cửa hàng...). Enter xác nhận,
    Esc bỏ qua khung đang chọn.
 3. Nhập tên template (ví dụ: crop_ready_wheat) - mỗi khung là một file
    PNG trong thư mục templates/.

Mẹo: mở game tới màn hình có biểu tượng cần chụp trước khi chạy tool.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np

from adb_core import ADB
from bot import HayDayBot


def capture_loop(bot: HayDayBot):
    out_dir = bot.config.get("templates_dir", "templates")
    os.makedirs(out_dir, exist_ok=True)

    bot.log("Công cụ chụp template. Đưa màn hình game tới biểu tượng cần chụp.")
    while True:
        name = input("\nTên template mới (Enter trống để thoát): ").strip()
        if not name:
            print("Kết thúc.")
            return

        img = bot.adb.screenshot()
        # thu nhỏ nếu quá lớn để dễ chọn
        h, w = img.shape[:2]
        scale = 1.0
        if w > 1400:
            scale = 1400 / w
            img_small = cv2.resize(img, None, fx=scale, fy=scale)
        else:
            img_small = img

        print("Kéo chuột chọn khung chứa biểu tượng. Enter = xác nhận tất cả, Esc = bỏ.")
        rois = cv2.selectROIs("Chon vung template (Enter khi xong)", img_small,
                              showCrosshair=True, fromCenter=False)
        cv2.destroyAllWindows()

        saved = 0
        for i, (x, y, rw, rh) in enumerate(rois):
            if rw <= 0 or rh <= 0:
                continue
            if scale != 1.0:  # đổi lại toạ độ gốc
                x, y, rw, rh = (int(v / scale) for v in (x, y, rw, rh))
            crop = img[y:y + rh, x:x + rw]
            fname = name if len(rois) == 1 else f"{name}_{i + 1}"
            path = os.path.join(out_dir, fname + ".png")
            cv2.imwrite(path, crop)
            print(f"  Đã lưu {path} ({rw}x{rh})")
            saved += 1
        if saved == 0:
            print("  Không có khung nào được chọn.")


def main():
    bot = HayDayBot("config.json")
    bot.check_device()
    capture_loop(bot)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
