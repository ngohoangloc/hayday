#!/usr/bin/env python3
"""Dựng contact sheet có nhãn chỉ số để tra sprite bằng mắt.

Chạy: python tools/make_sheet.py <thu_muc_sprites> <ra.jpg> [per_row]
"""
import glob
import os
import sys

import cv2
import numpy as np


def main():
    src, out = sys.argv[1], sys.argv[2]
    per_row = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    thumb = 130
    files = sorted(glob.glob(os.path.join(src, "*.png")))
    cells = []
    for p in files:
        img = cv2.imread(p, cv2.IMREAD_UNCHANGED)
        if img is None:
            continue
        if img.shape[2] == 4:
            a = img[:, :, 3:4].astype(np.float32) / 255.0
            rgb = img[:, :, :3].astype(np.float32)
            img = (rgb * a + 255 * (1 - a)).astype(np.uint8)
        h, w = img.shape[:2]
        s = min(thumb / max(h, 1), thumb / max(w, 1), 1.0)
        img = cv2.resize(img, (max(1, int(w * s)), max(1, int(h * s))))
        canvas = np.full((thumb + 18, thumb + 4, 3), 255, np.uint8)
        canvas[18:18 + img.shape[0], 2:2 + img.shape[1]] = img
        label = os.path.splitext(os.path.basename(p))[0].split("_")[-1]
        cv2.putText(canvas, label, (2, 14), cv2.FONT_HERSHEY_SIMPLEX,
                    0.42, (0, 0, 255), 1, cv2.LINE_AA)
        cells.append(canvas)
    if not cells:
        print("trống"); return 1
    rows = (len(cells) + per_row - 1) // per_row
    sheet = np.full((rows * (thumb + 18), per_row * (thumb + 4), 3), 255, np.uint8)
    for i, c in enumerate(cells):
        r, col = divmod(i, per_row)
        sheet[r * (thumb + 18):r * (thumb + 18) + c.shape[0],
              col * (thumb + 4):col * (thumb + 4) + c.shape[1]] = c
    cv2.imwrite(out, sheet, [cv2.IMWRITE_JPEG_QUALITY, 88])
    print(f"{len(cells)} sprite -> {out} ({sheet.shape[1]}x{sheet.shape[0]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
