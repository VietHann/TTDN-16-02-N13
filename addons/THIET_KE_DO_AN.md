# THIẾT KẾ ĐỒ ÁN: QUẢN LÝ TÀI SẢN - TÀI CHÍNH - NHÂN SỰ
## Odoo 15 - ERP Integration Project

---

## 1. PHÂN TÍCH NGHIỆP VỤ MỐI LIÊN KẾT

### 1.1. Mối quan hệ giữa 3 module

```
┌─────────────────────────────────────────────────────────────────┐
│                      HỆ THỐNG TỔNG THỂ                          │
├─────────────────┬───────────────────┬────────────────────────────┤
│   NHÂN SỰ       │   TÀI SẢN         │   TÀI CHÍNH/KẾ TOÁN        │
│   (nhan_su)     │(quan_ly_tai_san)  │   (ke_toan_tai_san)        │
└─────────────────┴───────────────────┴────────────────────────────┘
```

#### **A. NHÂN SỰ → TÀI SẢN**
- **Người sử dụng tài sản**: Nhân viên mượn/sử dụng tài sản
- **Người quản lý**: Nhân viên chịu trách nhiệm quản lý tài sản
- **Người thực hiện**: Bảo trì, kiểm kê, điều chuyển

**Quan hệ dữ liệu:**
```python
# Tài sản
tai_san.nguoi_quan_ly_id → nhan_vien (Quản lý chính)
tai_san.nguoi_su_dung_hien_tai_id → nhan_vien (Người đang sử dụng)

# Phiếu mượn
phieu_muon.nhan_vien_id → nhan_vien (Người mượn)
phieu_muon.nguoi_duyet_id → nhan_vien (Người phê duyệt)

# Lịch sử
lich_su_su_dung.nhan_vien_id → nhan_vien
lich_su_bao_tri.nguoi_thuc_hien_id → nhan_vien
lich_su_kiem_ke.nguoi_kiem_ke_id → nhan_vien
```

#### **B. TÀI SẢN → TÀI CHÍNH**
- **Giá trị tài sản**: Ghi nhận nguyên giá, giá trị hiện tại
- **Khấu hao**: Tính toán và phân bổ chi phí hàng tháng
- **Chi phí phát sinh**: Bảo trì, sửa chữa, nâng cấp
- **Thanh lý**: Ghi nhận lỗ/lãi thanh lý

**Quan hệ dữ liệu:**
```python
# Tài sản
tai_san.gia_tien_mua → ke_toan.ngay_gia (Tài khoản 211 - TSCĐ)
tai_san.gia_tri_hien_tai → ke_toan.gia_tri_con_lai

# Khấu hao
khau_hao.gia_tri_khau_hao → account.move.line (Bút toán hàng tháng)
  - Nợ TK 627 (Chi phí khấu hao)
  - Có TK 214 (Hao mòn TSCĐ lũy kế)

# Chi phí bảo trì
phieu_bao_tri.chi_phi → account.move.line
  - Nợ TK 627 (Chi phí sửa chữa)
  - Có TK 111/112 (Tiền mặt/Ngân hàng)

# Thanh lý
thanh_ly.gia_ban → account.move.line (Nhiều bút toán)
```

#### **C. TÀI CHÍNH → NHÂN SỰ**
- **Phân bổ chi phí theo bộ phận**: Chi phí khấu hao theo đơn vị sử dụng
- **Báo cáo**: Chi phí tài sản theo nhân viên/phòng ban

---

## 2. THIẾT KẾ CƠ CHẾ KHẤU HAO TỰ ĐỘNG

### 2.1. Luồng nghiệp vụ khấu hao hàng tháng

```
┌──────────────────────────────────────────────────────────────┐
│ CRON JOB (Chạy tự động ngày đầu tháng - 00:00)              │
└────────────────────┬─────────────────────────────────────────┘
                     ↓
┌────────────────────────────────────────────────────────────────┐
│ 1. Quét tất cả tài sản cần khấu hao (Đang sử dụng + Chưa TL) │
└────────────────────┬───────────────────────────────────────────┘
                     ↓
┌────────────────────────────────────────────────────────────────┐
│ 2. Tính giá trị khấu hao theo phương pháp:                    │
│    - Đường thẳng: (Nguyên giá - Giá trị thanh lý) / Thời gian │
│    - Số dư giảm dần: Giá trị còn lại × Tỷ lệ %                │
└────────────────────┬───────────────────────────────────────────┘
                     ↓
┌────────────────────────────────────────────────────────────────┐
│ 3. Tạo bản ghi khấu hao (khau_hao)                            │
│    - Lưu giá trị khấu hao                                      │
│    - Cập nhật giá trị hiện tại của tài sản                     │
└────────────────────┬───────────────────────────────────────────┘
                     ↓
┌────────────────────────────────────────────────────────────────┐
│ 4. Tự động sinh bút toán kế toán (account.move)               │
│    Nợ: TK 627 - Chi phí khấu hao TSCĐ                         │
│    Có: TK 214 - Hao mòn TSCĐ lũy kế                            │
└────────────────────┬───────────────────────────────────────────┘
                     ↓
┌────────────────────────────────────────────────────────────────┐
│ 5. Đăng bút toán tự động (state = 'posted')                   │
│    → Ghi nhận vào sổ cái                                       │
└────────────────────────────────────────────────────────────────┘
```

### 2.2. Công thức khấu hao

#### **Phương pháp đường thẳng (Straight Line)**
```
Khấu hao tháng = (Nguyên giá - Giá trị thanh lý dự kiến) / Số tháng sử dụng

Ví dụ: 
- Nguyên giá: 120,000,000 VNĐ
- Thời gian khấu hao: 5 năm (60 tháng)
- Giá trị thanh lý: 0
→ Khấu hao/tháng = 120,000,000 / 60 = 2,000,000 VNĐ/tháng
```

#### **Phương pháp số dư giảm dần (Declining Balance)**
```
Khấu hao tháng = Giá trị còn lại × Tỷ lệ khấu hao

Ví dụ:
- Nguyên giá: 120,000,000 VNĐ
- Tỷ lệ khấu hao: 20%/năm = 1.67%/tháng
- Tháng 1: 120,000,000 × 1.67% = 2,000,000
- Tháng 2: 118,000,000 × 1.67% = 1,967,000
- ...
```

### 2.3. Bảng tham chiếu tài khoản kế toán

| Tài khoản | Tên tài khoản                          | Loại  |
|-----------|----------------------------------------|-------|
| 211       | Tài sản cố định hữu hình              | Nợ    |
| 214       | Hao mòn TSCĐ hữu hình                 | Có    |
| 627       | Chi phí sản xuất chung (Khấu hao)     | Nợ    |
| 642       | Chi phí quản lý doanh nghiệp          | Nợ    |
| 111       | Tiền mặt                              | Có    |
| 112       | Tiền gửi ngân hàng                    | Có    |

---

## 3. THIẾT KẾ MODULE TÀI CHÍNH/KẾ TOÁN

### 3.1. Cấu trúc module: `ke_toan_tai_san`

```
ke_toan_tai_san/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── tai_khoan.py              # Danh mục tài khoản
│   ├── but_toan_khau_hao.py      # Bút toán khấu hao
│   ├── but_toan_chi_phi.py       # Bút toán chi phí (bảo trì, mua sắm)
│   ├── but_toan_thanh_ly.py      # Bút toán thanh lý
│   ├── ke_toan_tai_san.py        # Liên kết tài sản - kế toán
│   ├── cau_hinh_khau_hao.py      # Cấu hình khấu hao theo loại TS
│   └── bao_cao_tai_chinh.py      # Báo cáo tổng hợp
├── data/
│   └── tai_khoan_data.xml        # Dữ liệu mẫu tài khoản
├── security/
│   └── ir.model.access.csv
└── views/
    ├── menu.xml
    ├── tai_khoan_view.xml
    ├── but_toan_view.xml
    └── bao_cao_view.xml
```

### 3.2. Các Model chính

#### **Model 1: tai_khoan (Danh mục tài khoản)**
```python
class TaiKhoan(models.Model):
    _name = 'ke_toan.tai_khoan'
    _description = 'Danh mục tài khoản kế toán'
    
    ma_tai_khoan = fields.Char('Mã TK', required=True)  # VD: 211, 214, 627
    ten_tai_khoan = fields.Char('Tên TK', required=True)
    loai_tai_khoan = fields.Selection([
        ('tai_san', 'Tài sản'),
        ('nguon_von', 'Nguồn vốn'),
        ('chi_phi', 'Chi phí'),
        ('doanh_thu', 'Doanh thu')
    ], string='Loại tài khoản')
    tai_khoan_cap_tren_id = fields.Many2one('ke_toan.tai_khoan', 'TK cấp trên')
    cap_tai_khoan = fields.Integer('Cấp', default=1)  # 1, 2, 3
    active = fields.Boolean(default=True)
```

#### **Model 2: but_toan_khau_hao (Bút toán khấu hao)**
```python
class ButToanKhauHao(models.Model):
    _name = 'ke_toan.but_toan_khau_hao'
    _description = 'Bút toán khấu hao tài sản'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    ma_but_toan = fields.Char('Mã bút toán', readonly=True)
    ngay_ghi_nhan = fields.Date('Ngày ghi nhận', required=True, default=fields.Date.today)
    khau_hao_id = fields.Many2one('khau_hao', 'Khấu hao', required=True)
    tai_san_id = fields.Many2one('tai_san', 'Tài sản', related='khau_hao_id.tai_san_id')
    
    # Chi tiết bút toán
    tk_no_id = fields.Many2one('ke_toan.tai_khoan', 'TK Nợ', required=True)  # 627
    tk_co_id = fields.Many2one('ke_toan.tai_khoan', 'TK Có', required=True)  # 214
    so_tien = fields.Float('Số tiền', required=True)
    
    # Liên kết với Odoo Accounting
    account_move_id = fields.Many2one('account.move', 'Bút toán hệ thống', readonly=True)
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('posted', 'Đã đăng'),
        ('cancelled', 'Hủy')
    ], default='draft', tracking=True)
    
    dien_giai = fields.Text('Diễn giải')
    don_vi_id = fields.Many2one('don_vi', 'Đơn vị sử dụng')  # Phân bổ chi phí
```

#### **Model 3: ke_toan_tai_san (Bridge Model)**
```python
class KeToanTaiSan(models.Model):
    _name = 'ke_toan.tai_san'
    _description = 'Liên kết Tài sản - Kế toán'
    
    tai_san_id = fields.Many2one('tai_san', 'Tài sản', required=True, ondelete='cascade')
    
    # Thông tin kế toán
    tk_nguyen_gia = fields.Many2one('ke_toan.tai_khoan', 'TK Nguyên giá', 
                                    default=lambda self: self._get_tk_211())
    tk_hao_mon = fields.Many2one('ke_toan.tai_khoan', 'TK Hao mòn',
                                 default=lambda self: self._get_tk_214())
    tk_chi_phi = fields.Many2one('ke_toan.tai_khoan', 'TK Chi phí khấu hao',
                                 default=lambda self: self._get_tk_627())
    
    # Giá trị
    nguyen_gia = fields.Float(related='tai_san_id.gia_tien_mua', store=True)
    hao_mon_luy_ke = fields.Float('Hao mòn lũy kế', compute='_compute_hao_mon_luy_ke')
    gia_tri_con_lai = fields.Float(related='tai_san_id.gia_tri_hien_tai', store=True)
    
    # Cấu hình khấu hao
    phuong_phap_khau_hao = fields.Selection([
        ('duong_thang', 'Đường thẳng'),
        ('so_du_giam_dan', 'Số dư giảm dần')
    ], default='duong_thang', required=True)
    thoi_gian_khau_hao = fields.Integer('Thời gian (tháng)', default=60)  # 5 năm
    gia_tri_thanh_ly = fields.Float('Giá trị thanh lý dự kiến', default=0)
    
    # Lịch sử bút toán
    but_toan_ids = fields.One2many('ke_toan.but_toan_khau_hao', 
                                   compute='_compute_but_toan_ids')
```

#### **Model 4: cau_hinh_khau_hao (Cấu hình theo loại TS)**
```python
class CauHinhKhauHao(models.Model):
    _name = 'ke_toan.cau_hinh_khau_hao'
    _description = 'Cấu hình khấu hao theo loại tài sản'
    
    loai_tai_san_id = fields.Many2one('loai_tai_san', 'Loại tài sản', required=True)
    phuong_phap_mac_dinh = fields.Selection([
        ('duong_thang', 'Đường thẳng'),
        ('so_du_giam_dan', 'Số dư giảm dần')
    ], default='duong_thang')
    thoi_gian_mac_dinh = fields.Integer('Thời gian khấu hao (tháng)', default=60)
    ty_le_khau_hao_nam = fields.Float('Tỷ lệ %/năm', default=20.0)
    tk_chi_phi_id = fields.Many2one('ke_toan.tai_khoan', 'TK Chi phí mặc định')
    don_vi_ap_dung_id = fields.Many2one('don_vi', 'Đơn vị áp dụng')  # Phân bổ
```

### 3.3. Luồng dữ liệu chi tiết

```
TÀI SẢN (tai_san)
    ↓ (Tạo tự động khi thêm tài sản mới)
KẾ TOÁN TÀI SẢN (ke_toan_tai_san)
    ↓ (Cron job chạy hàng tháng)
KHẤU HAO (khau_hao)
    ↓ (Trigger tự động sau khi tạo khấu hao)
BÚT TOÁN KHẤU HAO (ke_toan.but_toan_khau_hao)
    ↓ (Sinh account.move)
ACCOUNT MOVE (account.move + account.move.line)
    ↓ (Post tự động)
SỔ CÁI (Ghi nhận chính thức)
```

---

## 4. TÍCH HỢP AI CHO ĐỒ ÁN SINH VIÊN

### 4.1. Dự đoán thời điểm bảo trì/thanh lý (Machine Learning)

#### **A. Thu thập dữ liệu lịch sử**
```python
class AITaiSanPredictor(models.Model):
    _name = 'ai.tai_san.predictor'
    _description = 'AI Dự đoán bảo trì và thanh lý tài sản'
    
    tai_san_id = fields.Many2one('tai_san', 'Tài sản')
    
    # Features (Đặc trưng đầu vào)
    tuoi_tai_san = fields.Integer('Tuổi tài sản (tháng)', compute='_compute_tuoi')
    so_lan_bao_tri = fields.Integer('Số lần bảo trì', compute='_compute_so_lan_bao_tri')
    tong_chi_phi_bao_tri = fields.Float('Tổng chi phí bảo trì', compute='_compute_chi_phi')
    ty_le_khau_hao = fields.Float('Tỷ lệ khấu hao (%)', compute='_compute_ty_le_khau_hao')
    tan_suat_su_dung = fields.Float('Tần suất sử dụng (lần/tháng)', compute='_compute_tan_suat')
    
    # Predictions (Dự đoán)
    ngay_bao_tri_du_kien = fields.Date('Dự kiến bảo trì tiếp theo')
    xac_suat_hong = fields.Float('Xác suất hỏng (%)', digits=(5, 2))
    de_xuat_thanh_ly = fields.Boolean('Đề xuất thanh lý')
    ly_do_de_xuat = fields.Text('Lý do đề xuất')
    
    # Model info
    model_version = fields.Char('Phiên bản model', default='v1.0')
    do_chinh_xac = fields.Float('Độ chính xác (%)', digits=(5, 2))
```

#### **B. Thuật toán đơn giản (Phù hợp SV)**

**Rule-based System (Hệ thống luật)**
```python
def predict_maintenance(self):
    """Dự đoán thời điểm bảo trì tiếp theo"""
    for record in self:
        tai_san = record.tai_san_id
        
        # Tính trung bình khoảng cách giữa các lần bảo trì
        lich_su_bao_tri = self.env['lich_su_bao_tri'].search([
            ('tai_san_id', '=', tai_san.id)
        ], order='ngay_bao_tri desc', limit=5)
        
        if len(lich_su_bao_tri) >= 2:
            # Tính khoảng cách trung bình (ngày)
            khoang_cach = []
            for i in range(len(lich_su_bao_tri) - 1):
                ngay_1 = lich_su_bao_tri[i].ngay_bao_tri
                ngay_2 = lich_su_bao_tri[i + 1].ngay_bao_tri
                khoang_cach.append((ngay_1 - ngay_2).days)
            
            trung_binh_ngay = sum(khoang_cach) / len(khoang_cach)
            
            # Dự đoán = Ngày bảo trì cuối + TB khoảng cách
            ngay_cuoi = lich_su_bao_tri[0].ngay_bao_tri
            record.ngay_bao_tri_du_kien = ngay_cuoi + timedelta(days=trung_binh_ngay)
        else:
            # Mặc định: 6 tháng/lần
            record.ngay_bao_tri_du_kien = fields.Date.today() + timedelta(days=180)

def calculate_failure_probability(self):
    """Tính xác suất hỏng (Rule-based)"""
    for record in self:
        score = 0
        
        # Quy tắc 1: Tuổi tài sản
        if record.tuoi_tai_san > 60:  # > 5 năm
            score += 30
        elif record.tuoi_tai_san > 36:  # > 3 năm
            score += 15
        
        # Quy tắc 2: Tần suất bảo trì
        if record.so_lan_bao_tri > 10:
            score += 25
        elif record.so_lan_bao_tri > 5:
            score += 10
        
        # Quy tắc 3: Chi phí bảo trì vs Giá trị
        ty_le_chi_phi = (record.tong_chi_phi_bao_tri / record.tai_san_id.gia_tien_mua) * 100
        if ty_le_chi_phi > 50:
            score += 30
        elif ty_le_chi_phi > 30:
            score += 15
        
        # Quy tắc 4: Khấu hao
        if record.ty_le_khau_hao > 80:
            score += 15
        
        record.xac_suat_hong = min(score, 100)
        
        # Đề xuất thanh lý nếu xác suất > 70%
        if score > 70:
            record.de_xuat_thanh_ly = True
            record.ly_do_de_xuat = f"""
            - Tuổi tài sản: {record.tuoi_tai_san} tháng
            - Số lần bảo trì: {record.so_lan_bao_tri}
            - Chi phí bảo trì: {ty_le_chi_phi:.1f}% giá trị
            - Khấu hao: {record.ty_le_khau_hao:.1f}%
            → Đề xuất thanh lý để tối ưu chi phí
            """
```

**Nâng cao: Linear Regression (Dùng thư viện sklearn)**
```python
from sklearn.linear_model import LinearRegression
import numpy as np

def train_cost_prediction_model(self):
    """Huấn luyện model dự đoán chi phí bảo trì"""
    # 1. Lấy dữ liệu lịch sử
    data = []
    tai_san_records = self.env['tai_san'].search([])
    
    for ts in tai_san_records:
        bao_tri_records = self.env['lich_su_bao_tri'].search([
            ('tai_san_id', '=', ts.id)
        ])
        
        if bao_tri_records:
            tuoi = (fields.Date.today() - ts.ngay_mua).days / 30  # Tháng
            so_lan = len(bao_tri_records)
            tong_chi_phi = sum(bao_tri_records.mapped('chi_phi'))
            
            data.append([tuoi, so_lan, tong_chi_phi])
    
    if len(data) < 10:
        return False  # Chưa đủ dữ liệu
    
    # 2. Chuẩn bị dữ liệu
    X = np.array(data)[:, :2]  # Features: tuổi, số lần
    y = np.array(data)[:, 2]   # Target: chi phí
    
    # 3. Huấn luyện model
    model = LinearRegression()
    model.fit(X, y)
    
    # 4. Lưu model (đơn giản: lưu coefficients)
    self.env['ir.config_parameter'].sudo().set_param(
        'ai.maintenance.model.coef', 
        ','.join(map(str, model.coef_))
    )
    
    return True
```

### 4.2. Phân tích chi phí - hiệu quả sử dụng

#### **Dashboard AI Insights**
```python
class AITaiSanAnalytics(models.Model):
    _name = 'ai.tai_san.analytics'
    _description = 'Phân tích AI cho tài sản'
    
    name = fields.Char('Tên báo cáo')
    ngay_phan_tich = fields.Date('Ngày phân tích', default=fields.Date.today)
    
    # Phân tích tổng thể
    tong_tai_san = fields.Integer('Tổng số tài sản', compute='_compute_metrics')
    tong_gia_tri = fields.Float('Tổng giá trị', compute='_compute_metrics')
    tong_chi_phi_bao_tri = fields.Float('Tổng chi phí bảo trì', compute='_compute_metrics')
    
    # AI Insights
    tai_san_hieu_qua_cao_ids = fields.Many2many(
        'tai_san', 'ai_analytics_efficient_rel', 
        string='Top 10 tài sản hiệu quả'
    )
    tai_san_ton_kem_ids = fields.Many2many(
        'tai_san', 'ai_analytics_inefficient_rel',
        string='Tài sản tốn kém (Đề xuất thanh lý)'
    )
    
    # Biểu đồ phân tích
    phan_tich_json = fields.Text('Dữ liệu biểu đồ (JSON)')
    
    def compute_efficiency_score(self, tai_san):
        """
        Tính điểm hiệu quả sử dụng (0-100)
        
        Công thức:
        Score = w1 × Tần_suất_sử_dụng 
              + w2 × (1 - Tỷ_lệ_chi_phí_bảo_trì)
              + w3 × Tỷ_lệ_khả_dụng
              + w4 × (1 - Tỷ_lệ_hỏng_hóc)
        """
        # Tính các chỉ số
        so_lan_muon = self.env['phieu_muon'].search_count([
            ('tai_san_id', '=', tai_san.id),
            ('state', '=', 'done')
        ])
        
        tuoi_thang = (fields.Date.today() - tai_san.ngay_mua).days / 30
        tan_suat = so_lan_muon / max(tuoi_thang, 1)  # Lần/tháng
        
        chi_phi_bao_tri = sum(self.env['lich_su_bao_tri'].search([
            ('tai_san_id', '=', tai_san.id)
        ]).mapped('chi_phi'))
        ty_le_chi_phi = chi_phi_bao_tri / max(tai_san.gia_tien_mua, 1)
        
        # Tỷ lệ khả dụng
        ngay_bao_tri = sum([
            (bt.ngay_ket_thuc - bt.ngay_bat_dau).days 
            for bt in self.env['lich_su_bao_tri'].search([
                ('tai_san_id', '=', tai_san.id),
                ('ngay_ket_thuc', '!=', False)
            ])
        ])
        ty_le_kha_dung = 1 - (ngay_bao_tri / max(tuoi_thang * 30, 1))
        
        # Tỷ lệ hỏng hóc
        so_lan_hong = self.env['lich_su_kiem_ke'].search_count([
            ('tai_san_id', '=', tai_san.id),
            ('trang_thai_kiem_ke', 'in', ['hong_hoc', 'sua_chua'])
        ])
        ty_le_hong = so_lan_hong / max(so_lan_muon, 1)
        
        # Tính điểm (weights)
        w1, w2, w3, w4 = 0.3, 0.3, 0.2, 0.2
        score = (
            w1 * min(tan_suat * 10, 100) +
            w2 * max((1 - ty_le_chi_phi) * 100, 0) +
            w3 * ty_le_kha_dung * 100 +
            w4 * max((1 - ty_le_hong) * 100, 0)
        )
        
        return min(score, 100)
    
    def action_analyze_all_assets(self):
        """Phân tích tất cả tài sản và tạo báo cáo"""
        tai_san_records = self.env['tai_san'].search([
            ('trang_thai', '!=', 'DaThanhLy')
        ])
        
        results = []
        for ts in tai_san_records:
            score = self.compute_efficiency_score(ts)
            results.append({
                'tai_san': ts,
                'score': score
            })
        
        # Sắp xếp theo điểm
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # Top 10 hiệu quả
        self.tai_san_hieu_qua_cao_ids = [r['tai_san'].id for r in results[:10]]
        
        # Bottom 10 (đề xuất thanh lý)
        self.tai_san_ton_kem_ids = [
            r['tai_san'].id for r in results[-10:] if r['score'] < 40
        ]
        
        # Tạo dữ liệu JSON cho biểu đồ
        import json
        self.phan_tich_json = json.dumps({
            'labels': [r['tai_san'].ten_tai_san for r in results[:20]],
            'scores': [r['score'] for r in results[:20]],
            'chart_type': 'bar'
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Kết quả phân tích AI',
            'res_model': 'ai.tai_san.analytics',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }
```

#### **Widget hiển thị insights (JavaScript)**
```javascript
// static/src/js/ai_dashboard_widget.js
odoo.define('ke_toan_tai_san.AIWidget', function (require) {
    "use strict";
    
    var AbstractField = require('web.AbstractField');
    var fieldRegistry = require('web.field_registry');
    
    var AIInsightWidget = AbstractField.extend({
        template: 'AIInsightWidgetTemplate',
        
        _render: function () {
            var data = JSON.parse(this.value || '{}');
            this.$el.html(QWeb.render('AIInsightWidgetTemplate', {
                labels: data.labels,
                scores: data.scores
            }));
            
            // Vẽ biểu đồ với Chart.js
            var ctx = this.$el.find('canvas')[0].getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Điểm hiệu quả',
                        data: data.scores,
                        backgroundColor: 'rgba(75, 192, 192, 0.6)'
                    }]
                },
                options: {
                    scales: {
                        y: { beginAtZero: true, max: 100 }
                    }
                }
            });
        }
    });
    
    fieldRegistry.add('ai_insight_chart', AIInsightWidget);
});
```

---

## 5. KIẾN TRÚC TỔNG THỂ

### 5.1. Dependency Graph
```
┌─────────────────────────────────────────────────────────┐
│                        base                              │
└──────────────────┬──────────────────────────────────────┘
                   │
        ┌──────────┴──────────┬─────────────┐
        │                     │             │
┌───────▼─────────┐  ┌───────▼────────┐   │
│    nhan_su      │  │    account     │   │
└───────┬─────────┘  └───────┬────────┘   │
        │                     │            │
        └──────────┬──────────┘            │
                   │                       │
         ┌─────────▼──────────┐            │
         │  quan_ly_tai_san   │◄───────────┘
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │ ke_toan_tai_san    │
         │ (Module mới)       │
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │  ai_tai_san        │
         │ (AI Integration)   │
         └────────────────────┘
```

### 5.2. Database Schema (ERD quan trọng)

```
┌─────────────────┐         ┌─────────────────┐
│   nhan_vien     │         │    tai_san      │
│─────────────────│         │─────────────────│
│ id (PK)         │◄───────┤│ nguoi_quan_ly_id│
│ ma_dinh_danh    │         │ id (PK)         │
│ ho_va_ten       │         │ ma_tai_san      │
│ ...             │         │ gia_tien_mua    │
└─────────────────┘         │ gia_tri_hien_tai│
        ▲                   └────────┬────────┘
        │                            │
        │                            │
┌───────┴─────────┐         ┌────────▼────────┐
│  phieu_muon     │         │   khau_hao      │
│─────────────────│         │─────────────────│
│ nhan_vien_id(FK)│         │ tai_san_id (FK) │
│ tai_san_id (FK) │         │ gia_tri_khau_hao│
│ ...             │         │ ngay_khau_hao   │
└─────────────────┘         └────────┬────────┘
                                     │
                            ┌────────▼─────────────┐
                            │ ke_toan.but_toan_kh  │
                            │──────────────────────│
                            │ khau_hao_id (FK)     │
                            │ tk_no_id (FK)        │
                            │ tk_co_id (FK)        │
                            │ account_move_id (FK) │
                            └──────────┬───────────┘
                                       │
                            ┌──────────▼───────────┐
                            │   account.move       │
                            │──────────────────────│
                            │ id (PK)              │
                            │ date                 │
                            │ state                │
                            └──────────┬───────────┘
                                       │
                            ┌──────────▼───────────┐
                            │  account.move.line   │
                            │──────────────────────│
                            │ move_id (FK)         │
                            │ account_id (FK)      │
                            │ debit/credit         │
                            └──────────────────────┘
```

---

## 6. ROADMAP TRIỂN KHAI

### Phase 1: Module Kế toán (Tuần 1-2)
- [ ] Tạo module `ke_toan_tai_san`
- [ ] Implement models: tai_khoan, ke_toan_tai_san, cau_hinh_khau_hao
- [ ] Data tài khoản kế toán mặc định (211, 214, 627)
- [ ] Views cơ bản

### Phase 2: Khấu hao tự động (Tuần 3)
- [ ] Model but_toan_khau_hao
- [ ] Function tính khấu hao (2 phương pháp)
- [ ] Cron job tự động chạy hàng tháng
- [ ] Tích hợp account.move sinh bút toán

### Phase 3: Liên kết đầy đủ (Tuần 4)
- [ ] Bút toán chi phí bảo trì
- [ ] Bút toán thanh lý
- [ ] Cập nhật model tai_san (thêm fields liên kết)
- [ ] Security & access rights

### Phase 4: AI Integration (Tuần 5-6)
- [ ] Model ai.tai_san.predictor
- [ ] Rule-based prediction
- [ ] (Optional) ML model với sklearn
- [ ] Model ai.tai_san.analytics
- [ ] Dashboard & Widget

### Phase 5: Testing & Documentation (Tuần 7)
- [ ] Test cases
- [ ] Demo data
- [ ] User manual
- [ ] Video demo

---

## 7. CODE SAMPLES CHO SINH VIÊN

### 7.1. Cron Job Khấu hao tự động
```python
# data/cron_khau_hao.xml
<odoo>
    <data noupdate="1">
        <record id="ir_cron_khau_hao_hang_thang" model="ir.cron">
            <field name="name">Khấu hao tài sản hàng tháng</field>
            <field name="model_id" ref="model_ke_toan_tai_san"/>
            <field name="state">code</field>
            <field name="code">model.cron_khau_hao_tu_dong()</field>
            <field name="interval_number">1</field>
            <field name="interval_type">months</field>
            <field name="numbercall">-1</field>
            <field name="doall" eval="False"/>
            <field name="active" eval="True"/>
            <field name="nextcall" eval="(DateTime.now() + relativedelta(months=1, day=1, hour=0, minute=0, second=0)).strftime('%Y-%m-%d %H:%M:%S')"/>
        </record>
    </data>
</odoo>
```

```python
# models/ke_toan_tai_san.py
def cron_khau_hao_tu_dong(self):
    """Chạy tự động vào ngày 1 hàng tháng"""
    _logger.info("=== BẮT ĐẦU KHẤU HAO TỰ ĐỘNG ===")
    
    # 1. Lấy tất cả tài sản cần khấu hao
    tai_san_can_khau_hao = self.search([
        ('tai_san_id.trang_thai', 'not in', ['DaThanhLy']),
        ('tai_san_id.gia_tri_hien_tai', '>', 0)
    ])
    
    so_luong_thanh_cong = 0
    so_luong_loi = 0
    
    for kt_ts in tai_san_can_khau_hao:
        try:
            # 2. Tạo bản ghi khấu hao
            khau_hao = self.env['khau_hao'].create({
                'tai_san_id': kt_ts.tai_san_id.id,
                'phuong_phap_khau_hao': kt_ts.phuong_phap_khau_hao,
                'ngay_khau_hao': fields.Date.today(),
            })
            
            # 3. Tự động sinh bút toán
            kt_ts._sinh_but_toan_khau_hao(khau_hao)
            
            so_luong_thanh_cong += 1
            
        except Exception as e:
            _logger.error(f"Lỗi khấu hao tài sản {kt_ts.tai_san_id.ma_tai_san}: {str(e)}")
            so_luong_loi += 1
    
    _logger.info(f"=== KẾT THÚC: {so_luong_thanh_cong} thành công, {so_luong_loi} lỗi ===")
```

### 7.2. Sinh bút toán kế toán
```python
def _sinh_but_toan_khau_hao(self, khau_hao):
    """Sinh bút toán kế toán từ khấu hao"""
    # 1. Tạo bản ghi bút toán nội bộ
    but_toan = self.env['ke_toan.but_toan_khau_hao'].create({
        'khau_hao_id': khau_hao.id,
        'tk_no_id': self.tk_chi_phi.id,  # 627
        'tk_co_id': self.tk_hao_mon.id,  # 214
        'so_tien': khau_hao.gia_tri_khau_hao,
        'ngay_ghi_nhan': khau_hao.ngay_khau_hao,
        'dien_giai': f'Khấu hao tài sản {self.tai_san_id.ten_tai_san} tháng {khau_hao.ngay_khau_hao.strftime("%m/%Y")}',
        'don_vi_id': self._get_don_vi_su_dung().id,
    })
    
    # 2. Sinh account.move (Bút toán Odoo)
    account_move = self.env['account.move'].create({
        'move_type': 'entry',
        'date': khau_hao.ngay_khau_hao,
        'journal_id': self._get_journal_khau_hao().id,
        'ref': khau_hao.ma_khau_hao,
        'line_ids': [
            # Dòng Nợ
            (0, 0, {
                'name': f'Chi phí khấu hao - {self.tai_san_id.ten_tai_san}',
                'account_id': self._map_to_account_account(self.tk_chi_phi).id,
                'debit': khau_hao.gia_tri_khau_hao,
                'credit': 0,
            }),
            # Dòng Có
            (0, 0, {
                'name': f'Hao mòn TSCĐ - {self.tai_san_id.ten_tai_san}',
                'account_id': self._map_to_account_account(self.tk_hao_mon).id,
                'debit': 0,
                'credit': khau_hao.gia_tri_khau_hao,
            }),
        ]
    })
    
    # 3. Đăng bút toán tự động
    account_move.action_post()
    
    # 4. Liên kết
    but_toan.write({
        'account_move_id': account_move.id,
        'state': 'posted'
    })
    
    return but_toan

def _map_to_account_account(self, ke_toan_tai_khoan):
    """Ánh xạ từ tài khoản nội bộ sang account.account của Odoo"""
    # Tìm hoặc tạo account.account tương ứng
    account = self.env['account.account'].search([
        ('code', '=', ke_toan_tai_khoan.ma_tai_khoan),
        ('company_id', '=', self.env.company.id)
    ], limit=1)
    
    if not account:
        # Tạo mới nếu chưa có
        account = self.env['account.account'].create({
            'code': ke_toan_tai_khoan.ma_tai_khoan,
            'name': ke_toan_tai_khoan.ten_tai_khoan,
            'user_type_id': self._get_account_type(ke_toan_tai_khoan).id,
            'company_id': self.env.company.id,
        })
    
    return account
```

---

## 8. ĐÁNH GIÁ VÀ KẾT LUẬN

### 8.1. Điểm mạnh của thiết kế
✅ **Tuân thủ chuẩn Odoo 15**: Sử dụng account.move, cron job, inheritance
✅ **Kiến trúc module hóa**: Dễ mở rộng và bảo trì
✅ **Tích hợp AI đơn giản**: Phù hợp trình độ sinh viên (rule-based + optional ML)
✅ **Liên kết 3 module rõ ràng**: Nhân sự - Tài sản - Tài chính
✅ **Nghiệp vụ thực tế**: Khấu hao tự động, bút toán, phân tích

### 8.2. Hướng phát triển
🚀 Deep Learning cho dự đoán chính xác hơn
🚀 Dashboard realtime với WebSocket
🚀 Mobile app quản lý tài sản (Odoo Mobile)
🚀 Tích hợp IoT (quét QR code, RFID)
🚀 Blockchain cho audit trail tài sản

### 8.3. Tài liệu tham khảo
- Odoo Official Documentation: https://www.odoo.com/documentation/15.0/
- Odoo Accounting Module: https://github.com/odoo/odoo/tree/15.0/addons/account
- Python ML: https://scikit-learn.org/
- Chart.js: https://www.chartjs.org/

---

## PHỤ LỤC: CHECKLIST HOÀN THÀNH ĐỒ ÁN

### A. Phần Backend (Python)
- [ ] Module ke_toan_tai_san hoàn chỉnh (4 models chính)
- [ ] Cron job khấu hao tự động
- [ ] Sinh bút toán kế toán (account.move)
- [ ] AI predictor (rule-based tối thiểu)
- [ ] AI analytics dashboard

### B. Phần Frontend (XML/JS)
- [ ] Views: form, tree, pivot cho mỗi model
- [ ] Menu structure rõ ràng
- [ ] Dashboard AI (widget chart)
- [ ] Report PDF (báo cáo khấu hao)

### C. Phần Security
- [ ] ir.model.access.csv đầy đủ
- [ ] Record rules phân quyền
- [ ] Workflow states (draft → posted)

### D. Phần Demo/Testing
- [ ] Demo data (10+ tài sản, 5+ nhân viên)
- [ ] Test cases cơ bản
- [ ] Video demo 5-10 phút

### E. Báo cáo đồ án
- [ ] Giới thiệu đề tài
- [ ] Phân tích nghiệp vụ (có sơ đồ)
- [ ] Thiết kế hệ thống (ERD, Use case)
- [ ] Kết quả triển khai (screenshots)
- [ ] Kết luận & hướng phát triển

---

**LƯU Ý QUAN TRỌNG:**
1. Ưu tiên hoàn thành **Phase 1-3** trước (core functionality)
2. AI có thể đơn giản hóa (rule-based) nếu thiếu thời gian
3. Tập trung vào **luồng nghiệp vụ rõ ràng** hơn là công nghệ phức tạp
4. Demo thực tế quan trọng hơn code hoàn hảo

**Chúc bạn thành công với đồ án! 🎓**
