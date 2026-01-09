# Quy Trình Mượn/Trả Tài Sản Trong Module quan_ly_tai_san_ban_dau

## 📋 Tổng Quan Quy Trình

**Mượn/Trả tài sản** là một trong những chức năng cốt lõi của module quản lý tài sản, cho phép nhân viên mượn tài sản công ty để sử dụng và trả lại khi không cần thiết nữa.

---

## 🎯 Luồng Nghiệp Vụ Chi Tiết

### Bước 1: **Tạo Phiếu Mượn** 📝
**Người thực hiện:** Nhân viên cần mượn tài sản

**Thao tác:**
1. Vào menu **"Quản lý phiếu và Lịch sử" > "Phiếu mượn"**
2. Click **"Create"** để tạo phiếu mới
3. Nhập thông tin:
   - **Mã phiếu**: Tự động tạo (PM-XXXXX)
   - **Thời gian mượn dự kiến**: Ngày giờ muốn mượn
   - **Thời gian trả dự kiến**: Ngày giờ dự kiến trả
   - **Nhân sự**: Chọn nhân viên mượn (từ module nhan_su)
   - **Tài sản**: Chọn tài sản cần mượn (chỉ hiện tài sản có trạng thái "Lưu trữ")
   - **Ghi chú**: Mục đích mượn (tùy chọn)

**Trạng thái ban đầu:** `Nháp` (draft)

---

### Bước 2: **Duyệt Phiếu Mượn** ✅
**Người thực hiện:** Người quản lý tài sản (quan_ly_id trong tài sản)

**Thao tác:**
1. Tìm phiếu mượn ở trạng thái `Nháp`
2. Click **"Approve"** hoặc **"Duyệt"**
3. Hệ thống tự động:
   - Tạo bản ghi **Lịch sử sử dụng** với thông tin từ phiếu
   - Cập nhật trạng thái tài sản từ `LuuTru` → `Muon`
   - Gán `nguoi_dang_dung_id` cho tài sản

**Trạng thái sau duyệt:** `Đã duyệt` (approved)

---

### Bước 3: **Nhận Tài Sản** 📦
**Người thực hiện:** Nhân viên mượn tài sản

**Thao tác:**
1. Sau khi phiếu được duyệt, nhân viên đến nhận tài sản
2. Người quản lý ghi nhận **"Thời gian mượn thực tế"**
3. Tài sản được giao cho nhân viên

**Trạng thái:** Vẫn `Đã duyệt`, nhưng có `ngay_muon_thuc_te`

---

### Bước 4: **Trả Tài Sản** 🔄
**Người thực hiện:** Nhân viên mượn tài sản

**Thao tác:**
1. Khi không cần dùng nữa, nhân viên trả tài sản
2. Người quản lý ghi nhận **"Thời gian trả thực tế"**
3. Click **"Done"** hoặc **"Hoàn thành"**

**Hệ thống tự động:**
- Cập nhật thông tin trả thực tế vào **Lịch sử sử dụng**
- Đặt lại trạng thái tài sản về `LuuTru`
- Xóa `nguoi_dang_dung_id`

**Trạng thái cuối:** `Hoàn thành` (done)

---

## 🔍 Chi Tiết Technical

### Models Liên Quan

#### 1. **`phieu_muon`** - Phiếu mượn chính
```python
class PhieuMuon(models.Model):
    _name = 'phieu_muon'

    # Thông tin cơ bản
    ma_phieu_muon = fields.Char("Mã phiếu mượn")  # PM-XXXXX
    ngay_muon_du_kien = fields.Datetime("Thời gian mượn dự kiến", required=True)
    ngay_muon_thuc_te = fields.Datetime("Thời gian mượn thực tế")
    ngay_tra_du_kien = fields.Datetime("Thời gian trả dự kiến", required=True)
    ngay_tra_thuc_te = fields.Datetime("Thời gian trả thực tế")

    # Liên kết
    nhan_vien_id = fields.Many2one("nhan_vien", "Nhân sự", required=True)
    tai_san_id = fields.Many2one("tai_san", "Tài sản", required=True,
                                domain=[('trang_thai', '=', 'LuuTru')])

    # Trạng thái
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('approved', 'Đã duyệt'),
        ('done', 'Hoàn thành'),
        ('cancelled', 'Hủy')
    ], default='draft')

    # Computed field
    trang_thai_muon = fields.Char(compute='_compute_trang_thai_muon')
```

#### 2. **`lich_su_su_dung`** - Lịch sử sử dụng
```python
class LichSuSuDung(models.Model):
    _name = 'lich_su_su_dung'

    ma_lich_su_su_dung = fields.Char("Mã lịch sử")  # LS-XXXXX
    ngay_muon = fields.Datetime("Thời gian mượn", required=True)
    ngay_tra = fields.Datetime("Thời gian trả", required=True)
    ghi_chu = fields.Char("Ghi chú")

    # Liên kết
    nhan_vien_id = fields.Many2one("nhan_vien", "Nhân sự")
    tai_san_id = fields.Many2one("tai_san", "Tài sản")
```

#### 3. **`tai_san`** - Cập nhật trạng thái
```python
# Trong tai_san.py
trang_thai = fields.Selection([
    ("LuuTru", "Lưu trữ"),
    ("Muon", "Mượn"),
    ("BaoTri", "Bảo trì"),
    ("Hong", "Hỏng"),
    ("DaThanhLy", "Đã thanh lý")
], default="LuuTru")

quan_ly_id = fields.Many2one("nhan_vien", "Người quản lý")
nguoi_dang_dung_id = fields.Many2one("nhan_vien", "Người đang sử dụng")

lich_su_su_dung_ids = fields.One2many('lich_su_su_dung', 'tai_san_id')
```

---

## 🔄 Workflow Actions

### **`action_approve()`** - Duyệt phiếu
```python
def action_approve(self):
    # Tạo lịch sử sử dụng
    self.env['lich_su_su_dung'].create({
        'ngay_muon': record.ngay_muon_du_kien,
        'ngay_tra': record.ngay_tra_du_kien,
        'nhan_vien_id': record.nhan_vien_id.id,
        'tai_san_id': record.tai_san_id.id,
    })

    # Cập nhật trạng thái tài sản
    record.tai_san_id.write({
        'trang_thai': 'Muon',
        'nguoi_dang_dung_id': record.nhan_vien_id.id
    })
```

### **`action_done()`** - Hoàn thành phiếu
```python
def action_done(self):
    # Cập nhật ngày trả thực tế vào lịch sử
    lich_su.write({
        'ngay_muon': record.ngay_muon_thuc_te,
        'ngay_tra': record.ngay_tra_thuc_te
    })

    # Trả tài sản về kho
    record.tai_san_id.write({
        'trang_thai': 'LuuTru',
        'nguoi_dang_dung_id': False
    })
```

---

## 📊 Ví Dụ Cụ Thể

### **Scenario: Nhân viên Nguyễn Văn A mượn máy tính**

#### **Bước 1: Tạo phiếu**
- **Mã phiếu**: PM-00001 (tự động)
- **Nhân sự**: Nguyễn Văn A (ID: 123)
- **Tài sản**: Máy tính Dell Latitude (ID: 456, trạng thái: Lưu trữ)
- **Ngày mượn dự kiến**: 15/01/2026 08:00
- **Ngày trả dự kiến**: 20/01/2026 17:00
- **Ghi chú**: "Cần dùng cho dự án ABC"

#### **Bước 2: Duyệt phiếu**
- Người quản lý click "Approve"
- **Lịch sử sử dụng** được tạo:
  - Mã: LS-00001
  - Ngày mượn: 15/01/2026 08:00
  - Ngày trả: 20/01/2026 17:00
  - Nhân viên: Nguyễn Văn A
  - Tài sản: Máy tính Dell Latitude
- **Tài sản** cập nhật:
  - Trạng thái: Mượn
  - Người đang sử dụng: Nguyễn Văn A

#### **Bước 3: Nhận tài sản**
- Nhân viên đến nhận máy tính
- Ghi nhận **Ngày mượn thực tế**: 15/01/2026 09:15

#### **Bước 4: Trả tài sản**
- Nhân viên trả máy tính
- Ghi nhận **Ngày trả thực tế**: 19/01/2026 16:30
- Click "Done"
- **Lịch sử** cập nhật ngày thực tế
- **Tài sản** về trạng thái Lưu trữ

---

## 📈 Computed Fields

### **`trang_thai_muon`** - Tình trạng mượn
```python
@api.depends('ngay_muon_du_kien', 'ngay_muon_thuc_te', 'ngay_tra_du_kien', 'ngay_tra_thuc_te')
def _compute_trang_thai_muon(self):
    # Logic:
    # - "Mượn muộn và trả muộn"
    # - "Mượn muộn"
    # - "Trả muộn"
    # - "Đúng hạn"
    # - "Đang mượn"
    # - "Chưa mượn"
```

**Ví dụ các trạng thái:**
- Chưa đến ngày mượn → "Chưa mượn"
- Đã nhận tài sản → "Đang mượn"
- Trả đúng hạn → "Đúng hạn"
- Trả quá hạn → "Trả muộn"

---

## ⚠️ Các Rule & Validation

### **Domain Constraints**
- Chỉ chọn tài sản có `trang_thai = 'LuuTru'`
- Không cho phép chỉnh sửa sau khi duyệt

### **Business Rules**
- Phải nhập ngày trả thực tế trước khi hoàn thành
- Tự động tạo lịch sử khi duyệt
- Tự động cập nhật trạng thái tài sản

### **Error Handling**
- Validate format mã phiếu (PM-XXXXX)
- Kiểm tra trạng thái hợp lệ khi chuyển đổi

---

## 🔗 Tích Hợp Với Module Khác

### **quan_ly_tai_san_ban_dau** ↔ **nhan_su**
- `nhan_vien_id`: Lấy danh sách nhân viên từ module nhan_su
- `quan_ly_id`: Người quản lý tài sản (cũng từ nhan_su)

### **quan_ly_tai_san_ban_dau** ↔ **ke_toan_tai_san**
- Khi trả tài sản, có thể trigger khấu hao tự động
- Lịch sử sử dụng để phân tích hiệu quả tài sản

---

## 💡 Điểm Cần Cải Thiện

### **Thiếu trong module gốc:**
1. **Không có phê duyệt workflow**: Chỉ có nút Approve đơn giản
2. **Không có email thông báo**: Không tự động gửi mail
3. **Không có validation chặt chẽ**: Có thể mượn tài sản đã mượn
4. **Không có lịch nhắc nhở**: Không cảnh báo sắp đến hạn trả

### **Cải thiện trong module mới của bạn:**
- Thêm workflow states chi tiết
- Mail notifications tự động
- Validation tốt hơn
- Cron job nhắc nhở deadline

---

*Tóm tắt chi tiết quy trình mượn/trả tài sản trong module quan_ly_tai_san_ban_dau với ví dụ cụ thể và code technical.*