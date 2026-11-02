"""
vision.py - Nhận diện hình ảnh cho HayDay Auto Bot.

- TemplateStore: nạp các mẫu (template PNG) từ thư mục templates/
- find_all / find_best: template matching đa tỉ lệ (độc lập độ phân giải màn hình)
- NMS để loại bỏ các khung trùng nhau
"""

import os

import cv2
import numpy as np


class TemplateStore:
    """Nạp và cache các ảnh mẫu từ một thư mục.

    Tên mẫu = tên file (không đuôi), ví dụ templates/crop_ready_wheat.png
    sẽ được tra bằng store.get("crop_ready_wheat").
    """

    def __init__(self, directory: str):
        self.directory = directory
        self._cache: dict[str, np.ndarray] = {}
        if not os.path.isdir(directory):
            os.makedirs(directory, exist_ok=True)

    def exists(self, name: str) -> bool:
        return os.path.isfile(os.path.join(self.directory, name + ".png"))

    def get(self, name: str) -> np.ndarray:
        if name not in self._cache:
            path = os.path.join(self.directory, name + ".png")
            tpl = cv2.imread(path, cv2.IMREAD_COLOR)
            if tpl is None:
                raise FileNotFoundError(f"Thiếu template: {path}")
            self._cache[name] = tpl
        return self._cache[name]

    def list_available(self) -> list[str]:
        names = []
        for f in os.listdir(self.directory):
            if f.lower().endswith(".png"):
                names.append(os.path.splitext(f)[0])
        return sorted(names)


def _match_single(image, template, threshold):
    res = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
    ys, xs = np.where(res >= threshold)
    h, w = template.shape[:2]
    return [(int(x), int(y), w, h, float(res[y, x])) for x, y in zip(xs, ys)]


def _nms(matches: list[tuple], overlap: float = 0.4) -> list[tuple]:
    """Non-Maximum Suppression đơn giản theo IoU."""
    if not matches:
        return []
    matches = sorted(matches, key=lambda m: m[4], reverse=True)
    keep: list[tuple] = []
    for m in matches:
        x, y, w, h, _ = m
        ok = True
        for kx, ky, kw, kh, _ in keep:
            ix = max(0, min(x + w, kx + kw) - max(x, kx))
            iy = max(0, min(y + h, ky + kh) - max(y, ky))
            inter = ix * iy
            union = w * h + kw * kh - inter
            if union > 0 and inter / union > overlap:
                ok = False
                break
        if ok:
            keep.append(m)
    return keep


def find_all(image: np.ndarray, template: np.ndarray,
             threshold: float = 0.80,
             scales: tuple[float, ...] | None = None,
             max_matches: int = 80,
             region: tuple[int, int, int, int] | None = None,
             nms_overlap: float = 0.4) -> list[tuple[int, int, int, int, float]]:
    """Tìm TẤT CẢ vị trí khớp template trong ảnh.

    scales: danh sách hệ số thu phóng template (mặc định tự sinh quanh 1.0
            để hỗ trợ nhiều độ phân giải màn hình).
    region: (x, y, w, h) giới hạn vùng tìm - giúp nhanh hơn.

    Trả về danh sách (x, y, w, h, score) đã qua NMS, sắp xếp theo score giảm dần.
    Toạ độ là tương đối với ảnh gốc (kể cả khi dùng region).
    """
    if scales is None:
        scales = (0.7, 0.8, 0.9, 1.0, 1.1, 1.25, 1.5)

    ox, oy = 0, 0
    if region is not None:
        rx, ry, rw, rh = region
        ox, oy = rx, ry
        image = image[ry:ry + rh, rx:rx + rw]

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    results: list[tuple] = []
    for s in scales:
        tpl = template if s == 1.0 else cv2.resize(
            template, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        th, tw = tpl.shape[:2]
        if th >= gray.shape[0] or tw >= gray.shape[1]:
            continue
        results.extend((x + ox, y + oy, tw, th, sc)
                       for x, y, _, _, sc in _match_single(gray, cv2.cvtColor(tpl, cv2.COLOR_BGR2GRAY), threshold))
        if len(results) > max_matches * 4:
            break

    kept = _nms(results, nms_overlap)[:max_matches]
    return kept


def find_best(image: np.ndarray, template: np.ndarray,
              threshold: float = 0.80, scales=None,
              region=None) -> tuple[int, int, int, int, float] | None:
    """Tìm vị trí khớp TỐT NHẤT, hoặc None nếu dưới ngưỡng."""
    all_m = find_all(image, template, threshold, scales, region=region)
    return all_m[0] if all_m else None


def center(match: tuple) -> tuple[int, int]:
    """Toạ độ điểm giữa của một kết quả find_*."""
    x, y, w, h, _ = match
    return (x + w // 2, y + h // 2)


def crop_region(image: np.ndarray, fraction: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    """Đổi vùng tỉ lệ [fx1, fy1, fx2, fy2] thành pixel (x, y, w, h)."""
    h, w = image.shape[:2]
    fx1, fy1, fx2, fy2 = fraction
    x1, y1 = int(fx1 * w), int(fy1 * h)
    x2, y2 = int(fx2 * w), int(fy2 * h)
    return (max(0, x1), max(0, y1), max(0, x2 - x1), max(0, y2 - y1))


def annotate(image: np.ndarray, matches: list, label: str = "") -> np.ndarray:
    """Vẽ khung debug lên ảnh (không thay đổi ảnh gốc)."""
    out = image.copy()
    for x, y, w, h, sc in matches:
        cv2.rectangle(out, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(out, f"{sc:.2f}", (x, max(0, y - 4)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)
    if label:
        cv2.putText(out, label, (10, 24), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (0, 255, 255), 2)
    return out
