# HƯỚNG DẪN CÀI ĐẶT & TRIỂN KHAI CHI TIẾT

## 📋 Mục lục
1. [Kiểm tra Yêu cầu](#1-kiểm-tra-yêu-cầu)
2. [Cài đặt Module](#2-cài-đặt-module)
3. [Cấu hình Ban đầu](#3-cấu-hình-ban-đầu)
4. [Tạo Dữ liệu Demo](#4-tạo-dữ-liệu-demo)
5. [Test Chức năng](#5-test-chức-năng)
6. [Khắc phục Sự cố](#6-khắc-phục-sự-cố)

---

## 1. Kiểm tra Yêu cầu

### 1.1. Phiên bản Odoo
```bash
# Kiểm tra phiên bản
./odoo-bin --version
# → Kết quả: Odoo Server 15.0...
```

### 1.2. Module phụ thuộc
Kiểm tra các module sau đã được cài đặt:
- ✅ `base` (mặc định)
- ✅ `account` (Accounting)
- ✅ `quan_ly_tai_san`
- ✅ `nhan_su`

**Cách kiểm tra:**
```
Odoo → Apps → Tìm "quan_ly_tai_san"
→ Nếu chưa có: Cài đặt trước
```

### 1.3. Quyền User
Đảm bảo user có quyền:
- Settings / Administration
- Accounting / Advisor

---

## 2. Cài đặt Module

### Bước 1: Copy module vào addons
```bash
# Đường dẫn
cd /home/vietlv/odo/odoo-fitdnu/addons

# Kiểm tra module đã có
ls -la ke_toan_tai_san/

# Cấu trúc chuẩn:
# ke_toan_tai_san/
# ├── __init__.py
# ├── __manifest__.py
# ├── models/
# ├── views/
# ├── data/
# ├── security/
# └── README.md
```

### Bước 2: Update Apps List
```
1. Vào Odoo
2. Menu: Apps
3. Click: Update Apps List (góc phải)
4. Confirm
```

### Bước 3: Tìm & Install
```
1. Apps → Search: "Kế toán Tài sản"
2. Click vào card module
3. Click: Install
4. Đợi cài đặt (1-2 phút)
```

### Bước 4: Kiểm tra
```
1. Menu xuất hiện: "Kế toán Tài sản"
2. Vào: Kế toán Tài sản → Cấu hình → Danh mục Tài khoản
3. Thấy 6 tài khoản mặc định (211, 214, 627, 642, 111, 112)
```

---

## 3. Cấu hình Ban đầu

### 3.1. Tài khoản Kế toán

**Kiểm tra:**
```
Menu: Kế toán Tài sản → Cấu hình → Danh mục Tài khoản
```

**Tài khoản cần có:**
| Mã  | Tên                                | Loại      |
|-----|------------------------------------|-----------|
| 211 | Tài sản cố định hữu hình          | Tài sản   |
| 214 | Hao mòn TSCĐ hữu hình             | Tài sản   |
| 627 | Chi phí sản xuất chung            | Chi phí   |
| 642 | Chi phí quản lý doanh nghiệp      | Chi phí   |

**Nếu thiếu:** Tạo thủ công hoặc chạy:
```bash
./odoo-bin -d your_database -u ke_toan_tai_san --stop-after-init
```

### 3.2. Liên kết Account Odoo (Quan trọng!)

**Bước 1:** Kiểm tra account.account
```
Menu: Accounting → Configuration → Chart of Accounts
```

**Bước 2:** Tạo account nếu chưa có
```
Accounting → Configuration → Chart of Accounts → Create

Account 211:
- Code: 211
- Account Name: Tài sản cố định hữu hình
- Type: Fixed Assets
- ✅ Save

Account 214:
- Code: 214
- Account Name: Hao mòn TSCĐ
- Type: Fixed Assets
- ✅ Save

Account 627:
- Code: 627
- Account Name: Chi phí khấu hao
- Type: Expenses
- ✅ Save
```

**Bước 3:** Liên kết tự động
```
Khi sinh bút toán lần đầu, hệ thống sẽ tự động liên kết
hoặc tạo account.account nếu chưa có
```

### 3.3. Journal (Sổ nhật ký)

**Kiểm tra:**
```
Menu: Accounting → Configuration → Journals
→ Phải có ít nhất 1 journal type = "General"
```

**Tạo mới (nếu cần):**
```
Accounting → Configuration → Journals → Create
- Journal Name: Khấu hao
- Type: General
- Short Code: KHAO
- ✅ Save
```

### 3.4. Cấu hình Khấu hao theo Loại Tài sản

**Ví dụ: Thiết bị điện tử**
```
Menu: Kế toán Tài sản → Cấu hình → Cấu hình Khấu hao → Create

- Loại tài sản: Thiết bị điện tử
- Phương pháp: Đường thẳng
- Thời gian: 60 tháng (5 năm)
- Tỷ lệ: 20%/năm
- TK Chi phí: 627 - Chi phí sản xuất chung
- ✅ Save
```

**Tương tự cho các loại khác:**
- Phương tiện di chuyển: 48 tháng (4 năm)
- Nội thất văn phòng: 72 tháng (6 năm)
- ...

---

## 4. Tạo Dữ liệu Demo

### 4.1. Tạo Đơn vị (nếu chưa có)
```
Menu: Nhân sự → Đơn vị → Create

Đơn vị 1:
- Tên: Phòng IT
- Mã: IT
- ✅ Save

Đơn vị 2:
- Tên: Phòng Kế toán
- Mã: KT
- ✅ Save
```

### 4.2. Tạo Nhân viên (nếu chưa có)
```
Menu: Nhân sự → Nhân viên → Create

Nhân viên 1:
- Họ tên đệm: Nguyễn Văn
- Tên: An
- Ngày sinh: 01/01/1990
- Email: an.nv@company.com
- ✅ Save
```

### 4.3. Tạo Tài sản
```
Menu: Quản lý Tài sản → Tài sản → Create

Tài sản 1: Máy tính Dell
- Tên: Máy tính Dell Inspiron 15
- Số serial: DELL-2024-001
- Ngày mua: 01/01/2024
- Giá mua: 15,000,000 VNĐ
- Loại: Thiết bị điện tử
- Vị trí: Phòng IT
- Nhà cung cấp: Dell Vietnam
- ✅ Save

Tài sản 2: Máy in HP
- Tên: Máy in HP LaserJet
- Số serial: HP-2024-001
- Ngày mua: 15/01/2024
- Giá mua: 8,000,000 VNĐ
- Loại: Thiết bị điện tử
- ✅ Save

... (Tạo thêm 8-10 tài sản nữa)
```

### 4.4. Liên kết Tài sản với Kế toán
```
Menu: Kế toán Tài sản → Kế toán → Kế toán Tài sản → Create

Record 1:
- Tài sản: Máy tính Dell Inspiron 15
- (Hệ thống tự động điền các field khác từ cấu hình)
- TK Nguyên giá: 211
- TK Hao mòn: 214
- TK Chi phí: 627
- Phương pháp: Đường thẳng
- Thời gian: 60 tháng
- Đơn vị: Phòng IT
- Có khấu hao: ✅
- ✅ Save

Record 2:
- Tài sản: Máy in HP LaserJet
- ... (tương tự)
- ✅ Save
```

### 4.5. Tạo Lịch sử Bảo trì (cho AI)
```
Menu: Quản lý Tài sản → Bảo trì → Lịch sử Bảo trì → Create

Bảo trì 1:
- Tài sản: Máy tính Dell
- Ngày bảo trì: 15/02/2024
- Chi phí: 500,000
- Nội dung: Vệ sinh, cài lại Windows
- ✅ Save

Bảo trì 2:
- Tài sản: Máy tính Dell
- Ngày bảo trì: 15/05/2024
- Chi phí: 300,000
- Nội dung: Kiểm tra định kỳ
- ✅ Save

... (Tạo thêm vài bản ghi cho các tài sản khác)
```

---

## 5. Test Chức năng

### 5.1. Test Khấu hao Thủ công

**Bước 1:** Chọn tài sản
```
Menu: Kế toán → Kế toán Tài sản
Click vào: Máy tính Dell
```

**Bước 2:** Khấu hao
```
Click nút: "Khấu hao Thủ công"
→ Hệ thống tạo bút toán
→ Kiểm tra:
  - Mã bút toán: BTKH-00001
  - Số tiền = 15,000,000 / 60 = 250,000 VNĐ
  - TK Nợ: 627
  - TK Có: 214
  - State: Draft
```

**Bước 3:** Đăng bút toán
```
Trong form Bút toán → Click: "Đăng bút toán"
→ State chuyển: Posted
→ Giá trị tài sản giảm: 15,000,000 - 250,000 = 14,750,000
```

**Bước 4:** Xem bút toán Odoo
```
Click nút: "Xem Bút toán Odoo"
→ Mở account.move
→ Kiểm tra 2 dòng:
  Line 1: Account 627, Debit 250,000
  Line 2: Account 214, Credit 250,000
→ State: Posted
```

### 5.2. Test Khấu hao Tự động (Cron)

**Cách 1: Chạy thủ công**
```
Menu: Settings → Technical → Automation → Scheduled Actions
Tìm: "Khấu hao tài sản tự động hàng tháng"
Click: Run Manually
→ Đợi 10-30 giây
→ Kiểm tra log (nếu có quyền)
```

**Cách 2: Chạy từ code (Development mode)**
```python
# Vào Settings → Activate Developer Mode
# Menu: Settings → Technical → Python Code
# Chạy:

model = env['ke_toan.tai_san']
model.cron_khau_hao_tu_dong()
```

**Kiểm tra kết quả:**
```
Menu: Kế toán → Bút toán Khấu hao
→ Thấy bút toán mới cho tất cả tài sản
→ State = Posted
→ Giá trị tài sản đã giảm
```

### 5.3. Test AI Dự đoán

**Bước 1:** Cập nhật dự đoán
```
Menu: AI & Phân tích → Dự đoán AI
→ Nếu chưa có record: Chạy cron
Settings → Technical → Scheduled Actions
Tìm: "Cập nhật dự đoán AI hàng tuần"
→ Run Manually
```

**Bước 2:** Xem dự đoán
```
Menu: AI & Phân tích → Dự đoán AI
Click vào: Máy tính Dell
→ Kiểm tra:
  - Tuổi tài sản: X tháng
  - Số lần bảo trì: 2
  - Xác suất hỏng: XX%
  - Ngày bảo trì dự kiến: ...
  - Đề xuất thanh lý: Có/Không
```

**Bước 3:** Test filter
```
Filter: "Đề xuất thanh lý"
→ Chỉ hiện tài sản nên thanh lý

Filter: "Xác suất cao"
→ Chỉ hiện tài sản có xác suất hỏng > 60%
```

### 5.4. Test Phân tích Hiệu quả

**Bước 1:** Tạo báo cáo
```
Menu: AI & Phân tích → Phân tích Hiệu quả → Create
- Tên: Phân tích tháng 10/2024
- Ngày: 31/10/2024
- ✅ Save
```

**Bước 2:** Chạy phân tích
```
Click nút: "Phân tích"
→ Đợi 5-10 giây
→ State: Done
```

**Bước 3:** Xem kết quả
```
Tab "Top Hiệu quả Cao"
→ 10 tài sản có điểm cao nhất

Tab "Đề xuất Thanh lý"
→ Danh sách tài sản kém hiệu quả
```

---

## 6. Khắc phục Sự cố

### Lỗi 1: Module không xuất hiện trong Apps

**Nguyên nhân:**
- Module chưa được Odoo nhận diện

**Giải pháp:**
```bash
# 1. Kiểm tra __manifest__.py có lỗi syntax không
python3 -m py_compile __manifest__.py

# 2. Restart Odoo
sudo systemctl restart odoo

# 3. Update Apps List lại
Apps → Update Apps List
```

### Lỗi 2: Cài đặt lỗi "Module dependency not found"

**Nguyên nhân:**
- Thiếu module phụ thuộc

**Giải pháp:**
```
1. Kiểm tra module quan_ly_tai_san đã cài chưa
2. Kiểm tra module nhan_su đã cài chưa
3. Cài đặt các module thiếu trước
4. Cài lại ke_toan_tai_san
```

### Lỗi 3: Không tạo được bút toán

**Lỗi:** "No journal found"

**Giải pháp:**
```
Accounting → Configuration → Journals → Create
- Type: General
- ✅ Save
```

**Lỗi:** "Account not found"

**Giải pháp:**
```
Accounting → Configuration → Chart of Accounts
→ Tạo account với code = 211, 214, 627
```

### Lỗi 4: Cron không chạy

**Nguyên nhân:**
- Cron bị tắt
- Odoo không chạy ở chế độ multi-threading

**Giải pháp:**
```bash
# 1. Kiểm tra cron
Settings → Technical → Scheduled Actions
→ Active = True
→ Next Execution Date đã qua chưa

# 2. Kiểm tra Odoo config
# Trong odoo.conf:
max_cron_threads = 1  # Tối thiểu = 1

# 3. Restart Odoo
sudo systemctl restart odoo
```

### Lỗi 5: AI không có dữ liệu

**Nguyên nhân:**
- Chưa chạy cron hoặc chưa có tài sản

**Giải pháp:**
```
1. Tạo ít nhất 5 tài sản
2. Tạo lịch sử bảo trì cho các tài sản
3. Chạy cron thủ công:
   Settings → Technical → Scheduled Actions
   → "Cập nhật dự đoán AI" → Run Manually
4. Kiểm tra lại
```

### Lỗi 6: Giá trị tài sản không cập nhật

**Nguyên nhân:**
- Bút toán chưa được đăng (state = draft)

**Giải pháp:**
```
1. Mở bút toán
2. Click: "Đăng bút toán"
3. Kiểm tra state = Posted
4. Kiểm tra giá trị tài sản đã giảm
```

---

## 📌 Checklist Hoàn thành

### Cài đặt
- [ ] Module cài đặt thành công
- [ ] Menu "Kế toán Tài sản" xuất hiện
- [ ] 6 tài khoản mặc định có sẵn
- [ ] Cấu hình khấu hao đã tạo

### Dữ liệu
- [ ] Có ít nhất 10 tài sản
- [ ] Có ít nhất 5 nhân viên
- [ ] Có ít nhất 10 bản ghi kế toán tài sản
- [ ] Có lịch sử bảo trì

### Chức năng
- [ ] Khấu hao thủ công: OK
- [ ] Bút toán sinh ra: OK
- [ ] Bút toán Odoo liên kết: OK
- [ ] Cron khấu hao tự động: OK
- [ ] AI dự đoán: OK
- [ ] Phân tích hiệu quả: OK

### Test
- [ ] Khấu hao 1 tài sản thủ công
- [ ] Xem bút toán Odoo
- [ ] Chạy cron khấu hao
- [ ] Xem dự đoán AI
- [ ] Chạy phân tích hiệu quả

---

## 🎯 Next Steps

1. **Tạo Demo Data đầy đủ** (20+ tài sản)
2. **Chạy Cron 2-3 tháng** để có lịch sử khấu hao
3. **Chuẩn bị báo cáo** với screenshots
4. **Quay video demo** 5-10 phút
5. **Trình bày** trước giảng viên

---

## 📞 Liên hệ Hỗ trợ

Nếu gặp vấn đề không giải quyết được:
1. Check log: `/var/log/odoo/odoo.log`
2. Google error message
3. Odoo Community: https://www.odoo.com/forum
4. Email: support@example.com

---

**Chúc bạn cài đặt thành công! 🚀**
