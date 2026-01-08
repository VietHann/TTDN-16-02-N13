# Module Kế toán Tài sản - Odoo 15

## 🎓 Đồ án Sinh viên: Quản lý Tài sản kết hợp Kế toán & AI

---

## 📋 Tổng quan

Module **Kế toán Tài sản** là giải pháp tích hợp quản lý tài sản cố định với kế toán, bao gồm:

✅ **Khấu hao tự động** hàng tháng (Cron Job)  
✅ **Sinh bút toán kế toán** tự động (account.move)  
✅ **Tích hợp AI**: Dự đoán bảo trì/thanh lý, phân tích hiệu quả  
✅ **Liên kết 3 module**: Tài sản - Kế toán - Nhân sự

---

## 🚀 Tính năng chính

### 1. Kế toán Tài sản
- Quản lý danh mục tài khoản kế toán (211, 214, 627, 642...)
- Liên kết tài sản với hệ thống kế toán
- Cấu hình khấu hao theo loại tài sản
- Theo dõi giá trị: Nguyên giá, Hao mòn lũy kế, Giá trị còn lại

### 2. Khấu hao Tự động
- **Cron Job** chạy ngày 1 hàng tháng (00:00)
- Hỗ trợ 2 phương pháp:
  - Đường thẳng (Straight Line)
  - Số dư giảm dần (Declining Balance)
- Tự động cập nhật giá trị tài sản

### 3. Bút toán Kế toán
- Tự động sinh `account.move` và `account.move.line`
- Ánh xạ tài khoản nội bộ ↔ Odoo
- Tự động đăng bút toán (state = 'posted')
- Ghi nhận vào sổ cái

### 4. AI & Phân tích
#### 4.1. Dự đoán AI (Rule-based)
- Dự đoán ngày bảo trì tiếp theo
- Tính xác suất hỏng (0-100%)
- Đề xuất thanh lý dựa trên:
  - Tuổi tài sản
  - Số lần bảo trì
  - Chi phí bảo trì / Giá mua
  - Tỷ lệ khấu hao
  - Số lần hỏng hóc

#### 4.2. Phân tích Hiệu quả
- Tính điểm hiệu quả sử dụng (0-100)
- Top 10 tài sản hiệu quả cao
- Danh sách tài sản đề xuất thanh lý
- Thống kê tổng quan

---

## 📦 Cài đặt

### Yêu cầu
- Odoo 15.0
- Python 3.7+
- Module phụ thuộc:
  - `base`
  - `account`
  - `quan_ly_tai_san`
  - `nhan_su`

### Các bước cài đặt

1. **Sao chép module vào thư mục addons**
```bash
cd /path/to/odoo/addons
cp -r ke_toan_tai_san .
```

2. **Cập nhật danh sách module**
```bash
# Trong Odoo
Apps → Update Apps List
```

3. **Cài đặt module**
```
Apps → Search "Kế toán Tài sản" → Install
```

4. **Cấu hình ban đầu**
- Vào **Kế toán Tài sản → Cấu hình → Danh mục Tài khoản**
- Kiểm tra tài khoản mặc định (211, 214, 627, 642)
- Vào **Cấu hình → Cấu hình Khấu hao**
- Tạo cấu hình cho từng loại tài sản

5. **Liên kết tài sản với kế toán**
- Vào **Kế toán → Kế toán Tài sản**
- Tạo mới hoặc liên kết tài sản hiện có
- Cấu hình phương pháp khấu hao

---

## 📖 Hướng dẫn sử dụng

### 1. Cấu hình Khấu hao

**Bước 1:** Tạo cấu hình cho loại tài sản
```
Menu: Kế toán Tài sản → Cấu hình → Cấu hình Khấu hao
- Chọn loại tài sản: VD "Thiết bị điện tử"
- Phương pháp: Đường thẳng
- Thời gian: 60 tháng (5 năm)
- Tỷ lệ: 20%/năm
- TK Chi phí: 627
```

**Bước 2:** Tạo Kế toán Tài sản
```
Menu: Kế toán → Kế toán Tài sản → Tạo mới
- Chọn tài sản
- Hệ thống tự động lấy cấu hình từ loại tài sản
- Điều chỉnh nếu cần
- Lưu
```

### 2. Khấu hao Tự động

**Cron Job** chạy tự động vào **ngày 1 hàng tháng, 00:00**

Kiểm tra:
```
Menu: Settings → Technical → Automation → Scheduled Actions
Tìm: "Khấu hao tài sản tự động hàng tháng"
```

**Chạy thủ công:**
```
Menu: Kế toán → Kế toán Tài sản
Chọn tài sản → Nút "Khấu hao Thủ công"
```

### 3. Xem Bút toán

**Cách 1:** Từ Kế toán Tài sản
```
Menu: Kế toán → Kế toán Tài sản
Chọn tài sản → Tab "Bút toán Khấu hao"
```

**Cách 2:** Danh sách tất cả bút toán
```
Menu: Kế toán → Bút toán Khấu hao
```

**Xem bút toán Odoo:**
```
Mở bút toán → Nút "Xem Bút toán Odoo"
```

### 4. AI Dự đoán

**Cron Job** cập nhật dự đoán **hàng tuần** (Chủ nhật 02:00)

**Xem dự đoán:**
```
Menu: AI & Phân tích → Dự đoán AI
- Filter "Đề xuất thanh lý": Tài sản nên thanh lý
- Filter "Xác suất cao": Tài sản có nguy cơ hỏng
```

**Cập nhật thủ công:**
```
Mở một dự đoán → Nút "Cập nhật Dự đoán"
```

### 5. Phân tích Hiệu quả

```
Menu: AI & Phân tích → Phân tích Hiệu quả → Tạo mới
Nhập tên báo cáo → Nút "Phân tích"
→ Xem kết quả:
  - Top 10 tài sản hiệu quả cao
  - Tài sản đề xuất thanh lý
```

---

## 🔧 Cấu trúc Module

```
ke_toan_tai_san/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── tai_khoan.py               # Danh mục tài khoản
│   ├── ke_toan_tai_san.py         # Bridge model (TS ↔ KT)
│   ├── but_toan_khau_hao.py       # Bút toán khấu hao
│   ├── cau_hinh_khau_hao.py       # Cấu hình theo loại TS
│   ├── ai_predictor.py            # AI Dự đoán
│   └── ai_analytics.py            # Phân tích hiệu quả
├── views/
│   ├── menu.xml
│   ├── tai_khoan_views.xml
│   ├── ke_toan_tai_san_views.xml
│   ├── but_toan_khau_hao_views.xml
│   ├── cau_hinh_khau_hao_views.xml
│   ├── ai_predictor_views.xml
│   └── ai_analytics_views.xml
├── data/
│   ├── tai_khoan_data.xml         # Dữ liệu mặc định
│   └── cron_khau_hao.xml          # Cron jobs
└── security/
    └── ir.model.access.csv
```

---

## 🧮 Công thức Khấu hao

### Phương pháp Đường thẳng
```
Khấu hao/tháng = (Nguyên giá - Giá trị thanh lý) / Số tháng khấu hao

Ví dụ:
- Nguyên giá: 120,000,000 VNĐ
- Thời gian: 60 tháng
- Giá trị thanh lý: 0
→ Khấu hao/tháng = 120,000,000 / 60 = 2,000,000 VNĐ
```

### Phương pháp Số dư giảm dần
```
Khấu hao/tháng = Giá trị còn lại × (Tỷ lệ %/năm / 12)

Ví dụ:
- Giá trị còn lại: 120,000,000 VNĐ
- Tỷ lệ: 20%/năm = 1.67%/tháng
→ Khấu hao tháng 1 = 120,000,000 × 1.67% = 2,000,000 VNĐ
→ Khấu hao tháng 2 = 118,000,000 × 1.67% = 1,967,000 VNĐ
```

---

## 🎯 Bút toán Kế toán

### Khấu hao tài sản
```
Nợ: TK 627 (Chi phí khấu hao)      2,000,000
Có: TK 214 (Hao mòn TSCĐ)           2,000,000
```

### Mua tài sản
```
Nợ: TK 211 (TSCĐ)                   120,000,000
Có: TK 111/112 (Tiền)               120,000,000
```

---

## 🤖 AI: Thuật toán Dự đoán

### Tính xác suất hỏng (Rule-based)

```python
Score = 0

# 1. Tuổi tài sản (max 30 điểm)
if tuoi > 60 tháng: score += 30
elif tuoi > 36 tháng: score += 20
elif tuoi > 24 tháng: score += 10

# 2. Số lần bảo trì (max 25 điểm)
if so_lan_bao_tri > 15: score += 25
elif so_lan_bao_tri > 10: score += 20
elif so_lan_bao_tri > 5: score += 10

# 3. Chi phí bảo trì (max 25 điểm)
ty_le_chi_phi = chi_phi_bao_tri / gia_mua * 100
if ty_le > 60%: score += 25
elif ty_le > 40%: score += 20
elif ty_le > 20%: score += 10

# 4. Khấu hao (max 15 điểm)
if khau_hao > 90%: score += 15
elif khau_hao > 70%: score += 10

# 5. Số lần hỏng (max 20 điểm)
if so_lan_hong >= 5: score += 20
elif so_lan_hong >= 3: score += 15

# 6. Bonus: Quá hạn bảo trì (max 15 điểm)
if qua_han_bao_tri: score += 15

→ Xác suất hỏng = min(score, 100)
```

### Đề xuất thanh lý

Thanh lý nếu:
- Xác suất hỏng > 75% HOẶC
- Chi phí bảo trì > 70% giá mua HOẶC
- Khấu hao > 90% + Hỏng >= 3 lần HOẶC
- Tuổi > 60 tháng + Ít sử dụng HOẶC
- Giá trị còn lại < 5% nguyên giá

---

## 📊 Dashboard & Báo cáo

### Thống kê Khấu hao
```sql
SELECT 
    ts.ma_tai_san,
    ts.ten_tai_san,
    ts.gia_tien_mua AS nguyen_gia,
    SUM(bt.so_tien) AS hao_mon_luy_ke,
    ts.gia_tri_hien_tai AS gia_tri_con_lai
FROM tai_san ts
LEFT JOIN ke_toan_tai_san kts ON kts.tai_san_id = ts.id
LEFT JOIN ke_toan_but_toan_khau_hao bt ON bt.ke_toan_tai_san_id = kts.id
WHERE bt.state = 'posted'
GROUP BY ts.id
```

### Top Tài sản Chi phí Cao
```sql
SELECT 
    ts.ten_tai_san,
    SUM(bt.chi_phi) AS tong_chi_phi
FROM tai_san ts
JOIN lich_su_bao_tri bt ON bt.tai_san_id = ts.id
GROUP BY ts.id
ORDER BY tong_chi_phi DESC
LIMIT 10
```

---

## 🐛 Xử lý Lỗi

### Lỗi 1: Không tìm thấy tài khoản Odoo
```
Nguyên nhân: Chưa có account.account tương ứng
Giải pháp:
1. Vào Accounting → Configuration → Chart of Accounts
2. Tạo account với code = mã tài khoản (VD: 211, 214, 627)
3. Hoặc liên kết thủ công trong Danh mục Tài khoản
```

### Lỗi 2: Cron job không chạy
```
Kiểm tra:
1. Settings → Technical → Scheduled Actions
2. Tìm "Khấu hao tài sản tự động"
3. Kiểm tra:
   - Active = True
   - Next Execution Date
4. Chạy thủ công: Nút "Run Manually"
```

### Lỗi 3: Bút toán không tạo được
```
Nguyên nhân:
- Thiếu journal (sổ nhật ký)
- Thiếu quyền
Giải pháp:
1. Tạo journal type = "General"
2. Cấp quyền Accounting / Advisor
```

---

## 📝 Log & Debug

### Xem Log
```bash
# Trong file odoo.conf
log_level = info

# Hoặc chạy Odoo với:
./odoo-bin --log-level=debug
```

### Tìm log khấu hao tự động
```bash
grep "KHẤU HAO TỰ ĐỘNG" /var/log/odoo/odoo.log
```

---

## 🎓 Hướng dẫn Đồ án

### 1. Demo cho giảng viên

**Chuẩn bị:**
- Tạo 10+ tài sản (máy tính, máy in, xe...)
- Tạo 5+ nhân viên
- Liên kết tài sản với kế toán
- Chạy khấu hao 1-2 lần

**Flow demo:**
1. Giới thiệu module + 3 liên kết
2. Cấu hình tài khoản + khấu hao
3. Tạo tài sản → Liên kết KT
4. Chạy khấu hao (thủ công)
5. Xem bút toán sinh ra
6. Demo AI: Dự đoán + Phân tích
7. Kết luận

### 2. Báo cáo

**Nội dung:**
- Giới thiệu đề tài
- Phân tích nghiệp vụ (ERD, Use case)
- Thiết kế hệ thống
- Công nghệ sử dụng
- Kết quả triển khai (screenshots)
- AI: Thuật toán + Demo
- Kết luận + Hướng phát triển

### 3. Video demo

**Outline (5-10 phút):**
1. Giới thiệu (30s)
2. Cấu hình (1 phút)
3. Khấu hao tự động (2 phút)
4. Bút toán kế toán (2 phút)
5. AI dự đoán (2 phút)
6. Phân tích hiệu quả (2 phút)
7. Kết luận (30s)

---

## 🚀 Hướng phát triển

### Phase 2 (Nâng cao)
- [ ] Machine Learning: Linear Regression, Random Forest
- [ ] Dashboard realtime (Chart.js)
- [ ] Báo cáo PDF tự động
- [ ] Email cảnh báo bảo trì

### Phase 3 (Tương lai)
- [ ] Mobile app (Odoo Mobile)
- [ ] QR Code / RFID tracking
- [ ] Blockchain audit trail
- [ ] Deep Learning prediction

---

## 📞 Hỗ trợ

- **Email**: doansinhvien@example.com
- **GitHub**: https://github.com/username/ke_toan_tai_san
- **Odoo Documentation**: https://www.odoo.com/documentation/15.0/

---

## 📄 License

LGPL-3.0 (Tương thích với Odoo Community)

---

## 👨‍💻 Tác giả

**Đồ án Sinh viên** - CNTT/KTPM  
Đề tài: *Quản lý Tài sản kết hợp Kế toán và AI*

---

**Chúc bạn thành công với đồ án! 🎓🚀**
