#!/usr/bin/env python3
"""
Import dữ liệu game thật từ CSV trong APK Hay Day -> game_data.json.

Nguồn: apk_work/xapk/extracted/assets/data/  (bóc từ install_time_asset_pack.apk)
- fields.csv: cây trồng (thời gian lớn thật, cấp mở khoá, giá)
- *_goods.csv: công thức máy chế biến (nguyên liệu, thời gian, giá)
- animal_feed.csv: thức ăn chăn nuôi
- animal_goods.csv: sản phẩm vật nuôi

Chạy: python tools/import_game_data.py [thu_muc_data] [ra: game_data.json]
"""
import csv
import glob
import json
import os
import sys


def parse_csv(path):
    """Đọc CSV Hay Day: dòng 1 = header, dòng 2 = kiểu, dữ liệu từ dòng 3;
    nhiều sản phẩm dùng chung block (Requirement các dòng kế tiếp)."""
    with open(path, encoding="utf-8", errors="replace") as f:
        rows = list(csv.reader(f))
    if len(rows) < 3:
        return []
    header = [h.strip() for h in rows[0]]
    items = []
    cur = None
    for r in rows[2:]:
        if not any(c.strip() for c in r):
            continue
        d = dict(zip(header, r))
        if d.get("Name", "").strip():          # item mới
            cur = d
            items.append({"name": cur["Name"].strip(), "requirements": []})
            req_n = _int(d.get("RequirementAmount"))
            req_name = d.get("Requirement", "").strip()
            if req_name:
                items[-1]["requirements"].append({"item": req_name, "amount": req_n})
        elif cur is not None and d.get("Requirement", "").strip():
            items[-1]["requirements"].append(
                {"item": d["Requirement"].strip(),
                 "amount": _int(d.get("RequirementAmount"))})
    return items


def _int(v):
    v = (v or "").strip().replace(";", "")
    try:
        return int(float(v)) if v else None
    except ValueError:
        return None


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else \
        "apk_work/xapk/extracted/assets/data"
    out = sys.argv[2] if len(sys.argv) > 2 else "game_data.json"

    data = {"source": "Hay Day APK asset pack", "crops": {}, "products": {},
            "feed": {}, "animal_goods": {}}

    # --- cây trồng: fields.csv (Name + TimeMin + UnlockLevel + OrderPrice) ---
    with open(os.path.join(src, "fields.csv"), encoding="utf-8", errors="replace") as f:
        rows = list(csv.reader(f))
    header = [h.strip() for h in rows[0]]
    for r in rows[2:]:
        d = dict(zip(header, r))
        name = d.get("Name", "").strip()
        if not name or name in ("EmptyField",):
            continue
        tm = _int(d.get("TimeMin")) or 0
        ts = _int(d.get("TimeSec")) or 0
        data["crops"][name] = {
            "grow_seconds": tm * 60 + ts,
            "unlock_level": _int(d.get("UnlockLevel")),
            "order_price": _int(d.get("OrderPrice")),
        }

    # --- sản phẩm máy chế biến ---
    for path in glob.glob(os.path.join(src, "*_goods.csv")):
        base = os.path.basename(path).replace("_goods.csv", "")
        if base in ("countyfair_dummy",):
            continue
        for it in parse_csv(path):
            key = f"{base}:{it['name']}"
            with open(path, encoding="utf-8", errors="replace") as f:
                pass
            data["products"][key] = it
            # lấy thêm TimeMin/OrderPrice từ dòng chính
    # đọc lại chi tiết TimeMin/OrderPrice cho products
    for path in glob.glob(os.path.join(src, "*_goods.csv")):
        base = os.path.basename(path).replace("_goods.csv", "")
        if base == "countyfair_dummy":
            continue
        with open(path, encoding="utf-8", errors="replace") as f:
            rows = list(csv.reader(f))
        header = [h.strip() for h in rows[0]]
        cur = None
        for r in rows[2:]:
            d = dict(zip(header, r))
            if d.get("Name", "").strip():
                cur = d["Name"].strip()
                key = f"{base}:{cur}"
                if key in data["products"]:
                    data["products"][key]["time_min"] = _int(d.get("TimeMin"))
                    data["products"][key]["order_price"] = _int(d.get("OrderPrice"))
                    data["products"][key]["unlock_level"] = _int(d.get("UnlockLevel"))

    # --- thức ăn + sản phẩm vật nuôi ---
    for it in parse_csv(os.path.join(src, "animal_feed.csv")):
        data["feed"][it["name"]] = it
    for it in parse_csv(os.path.join(src, "animal_goods.csv")):
        data["animal_goods"][it["name"]] = it

    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    print(f"Cây trồng : {len(data['crops'])}")
    for k, v in list(data["crops"].items())[:10]:
        print(f"  - {k:12} lớn {v['grow_seconds']//60:>3} phút  mở khoá lv{v['unlock_level']}")
    print(f"Sản phẩm máy: {len(data['products'])}")
    for k, v in list(data["products"].items())[:8]:
        reqs = ", ".join(f"{r['amount']}x{r['item']}" for r in v["requirements"])
        print(f"  - {k:28} ({reqs}) {v.get('time_min')} phút, giá ~{v.get('order_price')}")
    print(f"Thức ăn   : {len(data['feed'])}, Sản phẩm nuôi: {len(data['animal_goods'])}")
    print(f"-> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
