#!/usr/bin/env bash
# Rút APK Hay Day từ điện thoại Android đã kết nối ADB.
# Hay Day phát hành dạng AAB -> trên máy có base.apk + các split;
# script kéo TẤT CẢ các phần về apk_work/ (androguard đọc được base.apk).
set -e
cd "$(dirname "$0")/.."
mkdir -p apk_work

SERIAL="${1:-}"
OPT=""; [ -n "$SERIAL" ] && OPT="-s $SERIAL"

echo "== Danh sách thiết bị =="
adb $OPT devices -l

PATHS=$(adb $OPT shell pm path com.supercell.hayday | sed 's/package://' | tr -d '\r')
if [ -z "$PATHS" ]; then
  echo "Hay Day chưa cài trên máy này."
  echo "Cài rồi chạy lại script, hoặc kéo bản đã cài từ tài khoản Google Play của bạn."
  exit 1
fi

echo "== Các phần APK trên máy =="
echo "$PATHS"

i=0
while IFS= read -r p; do
  i=$((i+1))
  name=$(basename "$p")
  echo "→ Kéo $name ..."
  adb $OPT pull "$p" "apk_work/$name"
done <<< "$PATHS"

echo
echo "Xong. Phân tích:"
echo "  .venv/bin/python tools/apk_info.py apk_work/base.apk apk_work/api_list.json"
