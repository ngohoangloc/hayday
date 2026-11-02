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

## 6. Cấu trúc thư mục

```
hayday/
├── run_bot.py            # điểm vào
├── bot.py                # vòng lặp chính + kiểm tra template
├── adb_core.py           # ADB: screenshot, tap, swipe, mở app
├── vision.py             # template matching đa tỉ lệ + NMS
├── config.json           # toàn bộ cấu hình
├── requirements.txt
├── modules/
│   ├── base.py           # lớp cơ sở chung
│   ├── farming.py        # trồng & thu hoạch
│   ├── animals.py        # chăn nuôi
│   ├── production.py     # máy chế biến
│   └── market.py         # chợ & quảng cáo
├── tools/
│   ├── capture_templates.py  # chụp template tương tác
│   └── calibrate.py          # kiểm tra thiết bị / vùng / toạ độ
└── templates/            # (tự tạo) ảnh mẫu .png của bạn
```

## 7. Lưu ý

- **Không dùng tài khoản chính duy nhất** — mọi tool tự động đều có rủi ro bị
  Supercell khoá tài khoản. Hãy cân nhắc dùng tài khoản phụ.
- Nếu đổi độ phân giải/DPI điện thoại, chụp lại template cho thiết bị đó
  (bot có multi-scale matching nên thường vẫn nhận tốt).
- Cây lúa mì (wheat) vòng 2 phút là lối chơi "wheat farming" kinh điển để lấy
  vật liệu silo + XP nhanh; kết hợp bán lúa ở chợ để không đầy kho.
