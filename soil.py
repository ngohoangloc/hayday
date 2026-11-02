"""
soil.py - Nhận diện vùng đất ruộng bằng MÀU SẮC (kỹ thuật lấy từ
https://github.com/h8d13/HayDay - dự án "InfiniFarm").

Nguyên lý:
 1. Lấy màu trung bình của ảnh mẫu đất cày (templates/soil.jpg).
 2. Tạo mask các pixel có sai khác màu < ngưỡng.
 3. Tìm contour lớn nhất -> bounding rect + centroid (cv2.moments).
 4. Gom các pixel của mask thành các "hàng ruộng" để vuốt kéo
    (drag-plant / drag-harvest) qua từng hàng.
"""

import os

import cv2
import numpy as np


class SoilDetector:
    def __init__(self, template_path: str, color_threshold: float = 18.0,
                 min_area_ratio: float = 0.01, step_ratio: float = 0.12):
        tpl = cv2.imread(template_path)
        if tpl is None:
            raise FileNotFoundError(f"Không đọc được ảnh mẫu đất: {template_path}")
        self.color = np.mean(tpl, axis=(0, 1))          # BGR trung bình
        self.threshold = color_threshold
        self.min_area_ratio = min_area_ratio
        self.step_ratio = step_ratio
        self.last_mask = None

    def detect(self, screen: np.ndarray) -> dict | None:
        """Trả về {'rect', 'centroid', 'rows', 'area'} hoặc None nếu không thấy ruộng."""
        h, w = screen.shape[:2]
        diff = np.abs(screen.astype(np.int16) - self.color.astype(np.int16))
        mask = (np.mean(diff, axis=2) < self.threshold).astype(np.uint8) * 255
        # Xoá nhiễu li ti
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
        self.last_mask = mask

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None
        largest = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest)
        if area < self.min_area_ratio * w * h:
            return None

        x, y, bw, bh = cv2.boundingRect(largest)
        M = cv2.moments(largest)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
        else:
            cx, cy = x + bw // 2, y + bh // 2

        rows = self._rows(mask[y:y + bh, x:x + bw], x, y,
                          step_ratio=self.step_ratio)
        return {
            "rect": (x, y, bw, bh),
            "centroid": (cx, cy),
            "rows": rows,
            "area": int(area),
            "mask": mask,
        }

    @staticmethod
    def _rows(mask: np.ndarray, ox: int, oy: int,
              step_ratio: float = 0.12) -> list[tuple[int, int, int]]:
        """Sinh các đường quét ngang phủ toàn bộ thửa ruộng.

        Các đường cách nhau `step_ratio` * chiều cao ruộng (giống kéo lược
        qua từng hàng - đảm bảo không bỏ sót ô nào). Trả về
        [(y_center, x_left, x_right), ...] theo thứ tự trên -> dưới.
        """
        bh = mask.shape[0]
        if bh < 8:
            return []
        step = max(8, int(bh * step_ratio))
        half = max(2, step // 4)
        rows = []
        yy = half
        while yy < bh:
            band = mask[max(0, yy - half):yy + half]
            xs = np.where(band.any(axis=0))[0]
            if len(xs) > 20:
                rows.append((oy + yy, ox + int(xs[0]), ox + int(xs[-1])))
            yy += step
        return rows


def annotate_soil(screen: np.ndarray, result: dict) -> np.ndarray:
    """Vẽ mask + khung + centroid + các hàng để debug."""
    vis = screen.copy()
    if not result:
        return vis
    x, y, bw, bh = result["rect"]
    overlay = vis.copy()
    region = result["mask"][y:y + bh, x:x + bw] == 255
    overlay[y:y + bh, x:x + bw][region] = (0, 255, 0)
    vis = cv2.addWeighted(vis, 1, overlay, 0.4, 0)
    cv2.rectangle(vis, (x, y), (x + bw, y + bh), (0, 255, 0), 2)
    cx, cy = result["centroid"]
    cv2.circle(vis, (cx, cy), 6, (0, 0, 255), -1)
    for ry, rx1, rx2 in result["rows"]:
        cv2.line(vis, (rx1, ry), (rx2, ry), (255, 0, 255), 1)
    return vis
