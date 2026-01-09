# Module ke_toan_tai_san Cần Gì Từ quan_ly_tai_san & nhan_su

## 🔗 Tổng Quan Dependencies

Module `ke_toan_tai_san` phụ thuộc vào:
- **`quan_ly_tai_san`**: Nguồn dữ liệu tài sản chính
- **`nhan_su`**: Thông tin nhân viên, đơn vị sử dụng
- **`account`**: Module kế toán chuẩn của Odoo

---

## 📦 Từ Module quan_ly_tai_san

### 1. **Model `tai_san`** (Cần Thiết)
```python
# Liên kết chính
tai_san_id = fields.Many2one('tai_san', 'Tài sản', required=True)

# Dữ liệu cần thiết từ tai_san:
- ma_tai_san (mã tài sản)
- ten_tai_san (tên tài sản)
- gia_tien_mua (nguyên giá)
- gia_tri_hien_tai (giá trị còn lại)
- trang_thai (trạng thái tài sản)
- loai_tai_san_id (loại tài sản)
```

**Mục đích sử dụng:**
- Liên kết tài sản với kế toán
- Theo dõi khấu hao theo từng tài sản
- Tự động cập nhật giá trị khi khấu hao
- Phân tích hiệu quả tài sản

### 2. **Model `khau_hao`** (Quan Trọng)
```python
# Liên kết với bản ghi khấu hao
khau_hao_id = fields.Many2one('khau_hao', 'Khấu hao', required=True)

# Cần từ khau_hao:
- tai_san_id (tài sản được khấu hao)
- gia_tri_khau_hao (số tiền khấu hao)
- ngay_khau_hao (ngày khấu hao)
- phuong_phap_khau_hao (phương pháp)
```

**Mục đích sử dụng:**
- Sinh bút toán từ khấu hao
- Theo dõi lịch sử khấu hao
- Tự động tạo account.move

### 3. **Model `lich_su_bao_tri`** (Cho AI Analytics)
```python
# Thống kê chi phí bảo trì
lich_su_bt = self.env['lich_su_bao_tri'].search([('tai_san_id', 'in', all_tai_san.ids)])
record.tong_chi_phi_bao_tri = sum(lich_su_bt.mapped('chi_phi'))
```

**Mục đích sử dụng:**
- Tính toán hiệu quả tài sản
- Phân tích chi phí bảo trì
- AI dự đoán bảo trì

---

## 👥 Từ Module nhan_su

### 1. **Model `don_vi`** (Đơn Vị/Phong Ban)
```python
# Phân bổ chi phí khấu hao
don_vi_id = fields.Many2one(
    'don_vi',
    'Đơn vị sử dụng',
    help='Đơn vị/Phòng ban chịu chi phí khấu hao'
)
```

**Mục đích sử dụng:**
- Phân bổ chi phí khấu hao theo đơn vị
- Báo cáo chi phí theo phòng ban
- Phân tích hiệu quả sử dụng theo đơn vị

### 2. **Model `nhan_vien`** (Cho AI Chatbot)
```python
# Thống kê nhân viên
nhan_vien_count = env['nhan_vien'].search_count([])
nhan_vien_records = env['nhan_vien'].search(domain, limit=limit)

# Thông tin nhân viên:
- ma_dinh_danh, ho_va_ten
- lich_su_cong_tac_ids
- danh_sach_chung_chi_bang_cap_ids
```

**Mục đích sử dụng:**
- AI chatbot trả lời câu hỏi về nhân viên
- Thống kê số lượng nhân viên
- Tìm kiếm thông tin nhân viên

---

## 🔄 Data Flow Giữa Các Module

```
quan_ly_tai_san ──────────────► ke_toan_tai_san
     │                                │
     │ • tai_san (data)               │ • ke_toan.tai_san (bridge)
     │ • khau_hao (events)            │ • but_toan_khau_hao (accounting)
     │ • lich_su_bao_tri (costs)      │ • ai_analytics (insights)
     ▼                                ▼

nhan_su ─────────────────────────► ke_toan_tai_san
     │                                │
     │ • don_vi (cost centers)        │ • Phân bổ chi phí
     │ • nhan_vien (users)            │ • AI chatbot context
     ▼                                ▼
```

---

## ⚠️ Nếu Không Có Dependencies

### Thiếu quan_ly_tai_san:
- ❌ Không có dữ liệu tài sản để kế toán
- ❌ Không thể theo dõi khấu hao
- ❌ AI analytics không có dữ liệu
- ❌ Không thể sinh bút toán khấu hao

### Thiếu nhan_su:
- ❌ Không thể phân bổ chi phí theo đơn vị
- ❌ AI chatbot thiếu context nhân viên
- ❌ Không thể báo cáo chi phí theo phòng ban
- ❌ Thiếu thông tin người sử dụng tài sản

---

## 📋 Tóm Tắt Cần Thiết

| Từ Module | Model Cần Thiết | Mục Đích |
|-----------|------------------|----------|
| **quan_ly_tai_san** | `tai_san` | Dữ liệu tài sản cơ bản |
| | `khau_hao` | Sự kiện khấu hao |
| | `lich_su_bao_tri` | Chi phí bảo trì |
| **nhan_su** | `don_vi` | Phân bổ chi phí |
| | `nhan_vien` | AI context & thống kê |

**Kết luận:** Module `ke_toan_tai_san` **hoàn toàn phụ thuộc** vào `quan_ly_tai_san` để có dữ liệu và vào `nhan_su` để phân bổ chi phí và cung cấp context cho AI. Không thể hoạt động độc lập!