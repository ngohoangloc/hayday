# HayDay Auto Bot (PC + ADB điều khiển Android)

Tool treo máy **Hay Day** tự động trên **điện thoại Android thật** (USB/WiFi),
điều khiển từ máy tính qua **ADB** và nhận diện màn hình bằng **OpenCV**.

Tính năng (giống bảng Farm Config trong bản bot desktop):

| Module | Chức năng |
|---|---|
| `farming` | Plant Rotation — thu hoạch cây chín, gieo hạt lại, chờ cây lớn |
| `animals` | Chăn nuôi — thu sản phẩm (trứng/sữa/len...) và cho con đói ăn |
| `production` | Bakery / Dairy / Sugar Mill — thu thành phẩm, đặt lô sản xuất |
| `market` | Bán đồ ở chợ, chọn giá Thấp/Cao, quản lý quảng cáo, bán vật liệu |
| `orders` | Bảng đơn hàng — gửi đơn (Send Orders), xoá đơn, xin giúp |
| `achievements` | Collect Achievements — nhận thưởng thành tựu |
| `miner` | Auto Miner — dùng Dynamite/TNT lấy quặng |
| `followers` | Remove Followers — dọn danh sách người theo dõi |

### Chạy thử không cần điện thoại (mô phỏng)

Repo kèm **máy ảo game Hay Day** ([sim.py](sim.py)) — render màn hình game ảo
1080×2340 + trạng thái (ruộng, kho, gia súc, máy, chợ, đơn hàng...) và tự sinh
template nhận diện. Dùng để phát triển/test trên Linux/PC:

```bash
python run_bot.py --sim --cycles 5      # bot tự canh tác thế giới ảo
python tools/test_sim.py 5              # test end-to-end 8 module, in PASS
```

Mọi tính năng đều chạy qua cùng một đường code với máy thật, chỉ thay
`adb_core.ADB` bằng `SimADB`.

### Nhận diện ruộng theo màu + drag-plant (kỹ thuật InfiniFarm)

Lấy ý tưởng từ [h8d13/HayDay](https://github.com/h8d13/HayDay):

- **SoilDetector** ([soil.py](soil.py)): tính màu trung bình của ảnh mẫu đất cày
  `templates/soil.jpg` → mask các pixel sai khác < `color_threshold` → contour
  lớn nhất → centroid bằng `cv2.moments` → sinh các **đường quét ngang** phủ
  toàn thửa ruộng.
- **Drag-plant / drag-harvest**: thay vì tap từng ô, bot tap 1 điểm để "cầm
  liềm"/chọn hạt rồi **vuốt kéo zigzag qua từng hàng** (kèm jiggle ±`jiggle_pixels`)
  — một lượt phủ toàn bộ ruộng, nhanh và ổn định hơn nhiều.
- **Sell during growth**: trong ~100s chờ lúa mì lớn, bot tự mở chợ bán bớt
  (`sell_during_growth: true`), đúng lối chơi "trồng → bán khi chờ → thu hoạch".

Không nhận diện được đất (màu lạ, giao diện chặn...) thì tự chuyển về chiến lược
`tap` từng ô bằng template.

---

## 1. Cài đặt (Windows)

1. **Cài Python 3.10+** từ https://python.org (nhớ tick *Add to PATH*).
2. **Cài Android Platform-Tools** (chứa `adb`):
   - Tải: https://developer.android.com/tools/releases/platform-tools
   - Giải nén, ví dụ `C:\platform-tools`, thêm vào PATH
     (hoặc ghi đường dẫn đầy đủ `C:\platform-tools\adb.exe` vào `config.json`).
3. Cài thư viện Python:
   ```bat
   pip install -r requirements.txt
   ```
4. **Trên điện thoại**: Vào *Cài đặt → Giới thiệu* → bấm 7 lần vào "Số bản dựng"
   để mở **Tùy chọn nhà phát triển** → bật **Gỡ lỗi USB (USB debugging)**.
5. Cắm cáp USB, chạy:
   ```bat
   adb devices
   ```
   → Bấm "Cho phép" trên điện thoại. Wifi ADB thì dùng `adb tcpip 5555` + `adb connect <ip>:5555`.

## 2. Kiểm tra

```bat
python run_bot.py --check
python tools/calibrate.py           # chụp màn hình thử -> debug_screen.png
python tools/calibrate.py --grid    # xuất lưới tỉ lệ + vị trí các vùng regions
```

## 3. Chụp template (bước quan trọng nhất)

Bot nhận diện bằng **template matching**: cần ảnh mẫu của từng biểu tượng game.
Cách làm:

1. Mở Hay Day trên điện thoại, tới đúng màn hình có biểu tượng cần chụp.
2. Chạy:
   ```bat
   python tools/capture_templates.py
   ```
3. Gõ tên template (theo bảng dưới) → kéo chuột chọn khung → Enter → lưu.

### Template sẵn có từ APK (không cần chụp)

Repo có công cụ bóc **asset gốc của game** từ APK Hay Day:

```bash
# 1. Bóc atlas sprite từ XAPK/APK (một lần, cần file xapk đặt ở apk_work/)
python tools/decode_sc_batch.py icons nature_new hud_roadside_shop
# 2. Tách sprite riêng lẻ + xem contact sheet để tra chỉ số
python tools/crop_atlas.py apk_work/decoded/icons/icons_2.png apk_work/sprites/icons_2
python tools/make_sheet.py apk_work/sprites/icons_2 apk_work/sheet_icons2.jpg
# 3. Sinh template vào templates/apk/ (bot tự đọc thư mục này)
python tools/gen_templates_from_apk.py
```

Đã có sẵn: `item_wheat/corn/carrot/sugarcane/tomato.png` trong `templates/apk/`.

### Dữ liệu game thật (game_data.json)

`tools/import_game_data.py` đọc CSV dữ liệu game trong APK → `game_data.json`:
thời gian lớn **thật** của 40 loại cây (lúa 2 phút, ngô 5 phút, đậu tương 20,
mía 30 phút...), 424 công thức máy (nguyên liệu + thời gian + giá bán),
thức ăn chăn nuôi. Bot dùng các giá trị này để chờ đúng thời điểm và định giá
khi bán.

### Danh sách template cần chụp

| Tên | Nội dung | Chụp ở đâu |
|---|---|---|
| `crop_ready_wheat` … `crop_ready_sugarcane` | Cây chín trên ruộng | Trang trại khi lúa chín |
| `field_empty` | Ô ruộng trống | Trang trại |
| `seed_wheat` … `seed_sugarcane` | Hạt giống trên thanh chọn hạt | Khi chọn gieo hạt |
| `animal_product_chicken/cow/pig/sheep` | Bong bóng sản phẩm sẵn sàng | Chuồng gà/bò/… |
| `animal_hungry_chicken/cow/pig/sheep` | Bong bóng đói | Chuồng |
| `animal_feed_chicken/cow/pig/sheep` | Thức ăn (cám/bả/…) | Bảng thức ăn |
| `machine_bakery/dairy/sugar_mill` | Tòa nhà máy | Trang trại |
| `machine_ready_bakery/…` | Sản phẩm xong trên nóc máy | Trang trại |
| `recipe_bread/cream/brown_sugar/…` | Ô công thức trong UI máy | Cửa sổ máy |
| `btn_close` | Nút X đóng cửa sổ | Cửa sổ bất kỳ |
| `btn_shop` | Biển "Shop" ở góc màn hình | Trang trại |
| `market_slot_empty` | Ô bán hàng trống | Cửa hàng của mình |
| `item_wheat` … | Vật phẩm khi chọn bán | Cửa sổ chọn đồ bán |
| `btn_price_low`, `btn_price_high` | Nút giá Thấp / Cao | Cửa sổ bán |
| `btn_sell`, `btn_confirm` | Nút Bán / Xác nhận | Cửa sổ bán |
| `btn_advertise_free` | Ô quảng cáo còn miễn phí | Cửa hàng |

Chỉ chụp những template cho tính năng bạn bật trong `config.json` —
chạy `python run_bot.py --check` để biết chính xác thiếu cái nào.

## 4. Cấu hình `config.json`

- `regions`: các vùng màn hình theo **tỉ lệ 0.0–1.0** (độc lập độ phân giải) —
  xem `debug_regions.png` từ `calibrate.py --grid` để chỉnh.
- `soil_detection`: ngưỡng màu (`color_threshold`), mật độ đường quét
  (`sweep_step_ratio`), biên độ jiggle. Nếu ruộng của máy bạn có màu khác,
  chụp lại `templates/soil.jpg` bằng `capture_templates.py`.
- `plant_rotation.strategy`: `drag` (mặc định, dùng SoilDetector) hoặc `tap`.
- `plant_rotation.sell_during_growth`: bán hàng trong thời gian chờ cây lớn.
- `plant_rotation.crops[]`: bật/tắt từng loại cây, thời gian lớn.
- `animals.types[]`, `production.machines[]`, `market.sell_items[]`: bật/tắt từng mục,
  `run_every_cycles` để giãn chu kỳ (giống "Run Every: 5 cycles" trong bot desktop).
- `advanced`: các tham số như Game off wait, Market retries...

## 5. Chạy treo máy

```bat
python run_bot.py                 # chạy vô hạn
python run_bot.py --cycles 20     # 20 chu kỳ rồi dừng
python run_bot.py --serial R58N1234AB   # chọn thiết bị nếu cắm nhiều máy
```

Bot sẽ: kiểm tra game mở chưa (không thì mở) → chạy chuỗi
**farming → animals → production → market** → nghỉ `cycle_interval_seconds`
và lặp lại. Ctrl+C để dừng an toàn.

## 6. Đóng gói: AppImage (Linux) và .exe (Windows)

```bash
# Linux: binary + AppImage
bash build.sh                       # -> dist/hayday-bot + packaging/hayday-bot-<ver>-x86_64.AppImage
# Windows: exe
build.bat                           # -> dist\hayday-bot.exe
```

Hoặc để GitHub Actions build cả hai (tab **Actions → build → Run workflow**,
hoặc đẩy tag `v1.2.0`): workflow [.github/workflows/build.yml](.github/workflows/build.yml)
chạy smoke test sim rồi upload artifact `hayday-bot-windows-x64` (exe) và
`hayday-bot-linux-x64` (AppImage).

Chạy sau khi tải về:
- **AppImage**: `chmod +x hayday-bot-*.AppImage && ./hayday-bot-*.AppImage --sim --cycles 2`
- **exe**: `hayday-bot.exe --sim --cycles 2` (bỏ `--sim` khi nối điện thoại thật)

`config.json` và thư mục `templates/` được ưu tiên đọc **cạnh file chạy** —
hãy đặt template chụp từ điện thoại vào đó. Cấu trúc thư mục đầy đủ:

```
hayday/
├── run_bot.py            # điểm vào (--sim để chạy thế giới ảo)
├── bot.py                # vòng lặp chính + kiểm tra template + resolve đường dẫn
├── adb_core.py           # ADB: screenshot, tap, swipe, drag-row, mở app
├── vision.py             # template matching đa tỉ lệ + NMS
├── soil.py               # SoilDetector: nhận diện ruộng theo màu
├── sim.py                # máy ảo game Hay Day (SimADB) - test không cần máy
├── config.json           # toàn bộ cấu hình
├── requirements.txt
├── hayday-bot.spec       # PyInstaller (exe + AppImage)
├── build.sh / build.bat  # script đóng gói Linux / Windows
├── .github/workflows/build.yml  # CI build exe + AppImage
├── modules/
│   ├── base.py           # lớp cơ sở chung
│   ├── farming.py        # trồng & thu hoạch (drag hoặc tap)
│   ├── animals.py        # chăn nuôi
│   ├── production.py     # máy chế biến
│   ├── market.py         # chợ & quảng cáo
│   ├── orders.py         # bảng đơn hàng
│   ├── achievements.py   # thành tựu
│   ├── miner.py          # mỏ tự động
│   └── followers.py      # xoá người theo dõi
├── tools/
│   ├── capture_templates.py  # chụp template tương tác
│   ├── calibrate.py          # kiểm tra thiết bị / vùng / toạ độ
│   └── test_sim.py           # test end-to-end trong mô phỏng
└── templates/            # ảnh mẫu .png/.jpg (đã có sẵn soil.jpg)
```

## 7. Lưu ý

- **Không dùng tài khoản chính duy nhất** — mọi tool tự động đều có rủi ro bị
  Supercell khoá tài khoản. Hãy cân nhắc dùng tài khoản phụ.
- Nếu đổi độ phân giải/DPI điện thoại, chụp lại template cho thiết bị đó
  (bot có multi-scale matching nên thường vẫn nhận tốt).
- Cây lúa mì (wheat) vòng 2 phút là lối chơi "wheat farming" kinh điển để lấy
  vật liệu silo + XP nhanh; kết hợp bán lúa ở chợ để không đầy kho.
