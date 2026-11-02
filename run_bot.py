"""
run_bot.py - Điểm vào chính của HayDay Auto Bot.

Cách dùng:
    python run_bot.py                     # chạy vô hạn theo config.json
    python run_bot.py --cycles 10         # chạy 10 chu kỳ rồi dừng
    python run_bot.py --config my.json    # dùng file config khác
    python run_bot.py --serial R58N...    # chọn thiết bị cụ thể
    python run_bot.py --check             # chỉ kiểm tra thiết bị + template
"""

import argparse
import sys

from bot import HayDayBot


def main():
    parser = argparse.ArgumentParser(description="HayDay Auto Bot (PC + ADB)")
    parser.add_argument("--config", default="config.json", help="Đường dẫn file config")
    parser.add_argument("--cycles", type=int, default=0, help="Số chu kỳ chạy (0 = vô hạn)")
    parser.add_argument("--serial", default=None, help="Serial thiết bị ADB")
    parser.add_argument("--check", action="store_true",
                        help="Chỉ kiểm tra thiết bị, độ phân giải và template rồi thoát")
    parser.add_argument("--sim", action="store_true",
                        help="Chạy trong thế giới mô phỏng (không cần điện thoại)")
    args = parser.parse_args()

    bot = HayDayBot(args.config, use_sim=args.sim)
    if args.serial:
        bot.adb.serial = args.serial

    if args.check:
        try:
            bot.check_device()
        except Exception as exc:
            print(f"[!] {exc}\n    (Vẫn kiểm tra template được khi chưa cắm thiết bị.)\n")
        missing = bot.missing_templates()
        if missing:
            print("\nThiếu template:")
            for m in missing:
                print(f"  - templates/{m}.png")
            print("\nChạy: python tools/capture_templates.py để chụp mẫu.")
        else:
            print("\nĐủ template. Sẵn sàng chạy!")
        return

    bot.run(max_cycles=args.cycles or None)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
