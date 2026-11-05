#!/usr/bin/env python3
"""
Sinh template cho bot từ sprite game thật (bóc từ APK Hay Day).

Quy trình: decode atlas -> tách sprite (tools/crop_atlas.py) -> ánh xạ tay
tên template <-> sprite -> ghi PNG vào templates/apk/ để dùng song song
với template chụp từ màn hình.

Chạy: python tools/gen_templates_from_apk.py [sprites_root] [templates/apk]
"""
import json
import os
import sys

import cv2
import numpy as np

# Ánh xạ: tên template của bot -> (thư mục atlas, tên file sprite, alpha cận)
# sprite đã xác minh bằng mắt trên contact sheet
MAPPING = {
    "item_wheat":     ("icons_2", "icons_2_0039", 40),
    "item_corn":      ("icons_2", "icons_2_0119", 40),
    "item_carrot":    ("icons_2", "icons_2_0026", 40),
    "item_sugarcane": ("icons_2", "icons_2_0170", 40),
    "item_tomato":    ("icons_2", "icons_2_0161", 40),
}


def flatten_alpha(img, alpha_min):
    a = img[:, :, 3:4].astype(np.float32) / 255.0
    rgb = img[:, :, :3].astype(np.float32)
    out = (rgb * a + 255.0 * (1 - a)).astype(np.uint8)   # nền trắng hoá phần mờ
    # giữ kênh alpha nhị phân để matching bỏ nền
    out = cv2.cvtColor(out, cv2.COLOR_BGR2BGRA)
    out[:, :, 3] = (img[:, :, 3] >= alpha_min).astype(np.uint8) * 255
    return out


def main():
    sprites_root = sys.argv[1] if len(sys.argv) > 1 else "apk_work/sprites"
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "templates/apk"
    os.makedirs(out_dir, exist_ok=True)
    made = []
    for name, (group, sprite, amin) in MAPPING.items():
        p = os.path.join(sprites_root, group, sprite + ".png")
        if not os.path.isfile(p):
            print(f"!! thiếu {p}")
            continue
        img = cv2.imread(p, cv2.IMREAD_UNCHANGED)
        if img is None or img.shape[2] != 4:
            print(f"!! sai định dạng {p}")
            continue
        flat = flatten_alpha(img, amin)
        dst = os.path.join(out_dir, name + ".png")
        cv2.imwrite(dst, flat)
        made.append((name, flat.shape[1], flat.shape[0]))
        print(f"✓ {name}.png ({flat.shape[1]}x{flat.shape[0]}) <- {sprite}")
    print(f"\n{len(made)} template -> {out_dir}/")
    print("Lưu ý: sprite gốc của game, dùng kèm multi-scale matching của bot;")
    print("chạy tools/capture_templates.py nếu cần khớp chính xác UI máy thật.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
