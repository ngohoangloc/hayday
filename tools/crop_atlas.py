#!/usr/bin/env python3
"""
Tách sprite riêng lẻ từ atlas đã decode (alpha-channel connected components).

Chạy: python tools/crop_atlas.py <atlas.png> <thu_muc_ra> [min_area]
Ra:   sprites/<ten>_NNN.png + sprites/_meta.json (toạ độ gốc từng sprite)
"""
import json
import os
import sys

import cv2
import numpy as np


def main():
    atlas_path, out_dir = sys.argv[1], sys.argv[2]
    min_area = int(sys.argv[3]) if len(sys.argv) > 3 else 400
    os.makedirs(out_dir, exist_ok=True)

    img = cv2.imread(atlas_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        print("Không đọc được", atlas_path)
        return 1
    h, w = img.shape[:2]
    alpha = img[:, :, 3] if img.shape[2] == 4 else np.full((h, w), 255, np.uint8)

    # lấp kẽ hở nhỏ trong sprite (chữ ký vẽ rời rạc) - nhẹ để không dính cụm kề nhau
    kernel = np.ones((3, 3), np.uint8)
    solid = cv2.morphologyEx(alpha, cv2.MORPH_CLOSE, kernel, iterations=1)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(solid, 8)
    meta, count = [], 0
    atlas_name = os.path.splitext(os.path.basename(atlas_path))[0]
    for i in range(1, n):
        x, y, bw, bh, area = stats[i]
        if area < min_area:
            continue
        if bw > w * 0.95 and bh > h * 0.95:   # toàn khung -> bỏ
            continue
        crop = img[y:y + bh, x:x + bw]
        name = f"{atlas_name}_{count:04d}"
        cv2.imwrite(os.path.join(out_dir, name + ".png"), crop)
        meta.append({"name": name, "x": int(x), "y": int(y),
                     "w": int(bw), "h": int(bh), "area": int(area)})
        count += 1
    with open(os.path.join(out_dir, "_meta.json"), "w") as f:
        json.dump({"atlas": atlas_path, "size": [w, h],
                   "sprites": meta}, f, indent=1)
    print(f"{atlas_name}: tách {count} sprite (từ {n - 1} vùng) -> {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
