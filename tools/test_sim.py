"""
tools/test_sim.py - Test end-to-end toàn bộ bot trong thế giới mô phỏng.

Chạy: python tools/test_sim.py [số_chu_kỳ]
Pass = cả 8 module (farming/animals/production/market/orders/achievements/
miner/followers) đều tác động được lên thế giới game ảo.
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

real_sleep = time.sleep
time.sleep = lambda s: real_sleep(0.02 if s < 5 else s)   # nén sleep cho nhanh


def main():
    cycles = int(sys.argv[1]) if len(sys.argv) > 1 else 5

    with open("config.json", encoding="utf-8") as f:
        cfg = json.load(f)
    for c in cfg["plant_rotation"]["crops"]:
        c["grow_seconds"] = 4
    cfg["general"]["cycle_interval_seconds"] = 1
    for key in ("achievements", "orders", "animals", "production"):
        cfg[key]["collect_every_cycles" if key == "achievements"
                 else "run_every_cycles"] = 1
    for t in cfg["animals"]["types"]:
        t["enabled"] = True
    for m in cfg["production"]["machines"]:
        m["enabled"] = True
    cfg["followers"].update(enabled=True, run_every_cycles=1)
    cfg["miner"].update(enabled=True, run_every_cycles=1)
    cfg["sim"] = {**cfg.get("sim", {}), "animal_product_seconds": 1,
                  "hungry_seconds": 3600, "cook_seconds": 2, "sale_seconds": 2}
    json.dump(cfg, open("debug/cfg_test.json", "w", encoding="utf-8"),
              ensure_ascii=False)

    from bot import HayDayBot
    bot = HayDayBot("debug/cfg_test.json", use_sim=True)
    bot.farming._sleep_interruptible = lambda s: None

    w = bot.adb.world
    coins0, followers0 = w.coins, len(w.followers)
    print(f"BAN DAU: coins={coins0} followers={followers0} dynamite={w.dynamite}")
    bot.run(max_cycles=cycles, start_app=False)
    real_sleep(2.5)   # cho quảng cáo bán xong / máy nấu xong

    print("\n===== SAU", cycles, "CHU KY =====")
    print(f"coins={w.coins} followers={len(w.followers)} ore={w.inventory['ore']}")
    print(f"bread={w.inventory['bread']} cream={w.inventory['cream']}")
    print(f"egg={w.inventory['egg']} bacon={w.inventory['bacon']} wool={w.inventory['wool']}")

    dairy = w.inventory["cream"] + w.inventory["butter"] + \
        w.inventory["cheese"] + w.inventory["milk"]
    assert w.coins > coins0, "coins không tăng"
    assert len(w.followers) < followers0, "chưa xoá follower"
    assert w.inventory["ore"] > 0, "mỏ chưa chạy"
    assert w.inventory["egg"] > 0, "chưa thu trứng"
    assert w.inventory["bacon"] > 0 and w.inventory["wool"] > 0, "thiếu heo/cừu"
    assert dairy > 0, "hệ thống sữa không chạy"
    assert w.inventory["bread"] > 0 and w.inventory["cream"] > 0, "máy chưa nấu"
    assert w.achievement_ready == 0, "chưa nhận thành tựu"
    print("\nE2E SIM PASS ✔")


if __name__ == "__main__":
    main()
