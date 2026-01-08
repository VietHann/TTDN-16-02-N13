# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta, datetime
import logging

_logger = logging.getLogger(__name__)


class AITaiSanPredictor(models.Model):
    """AI Dự đoán bảo trì và thanh lý tài sản"""
    _name = 'ai.tai_san.predictor'
    _description = 'AI Dự đoán bảo trì và thanh lý'
    _rec_name = 'tai_san_id'
    _order = 'xac_suat_hong desc'
    
    tai_san_id = fields.Many2one(
        'tai_san',
        'Tài sản',
        required=True,
        ondelete='cascade'
    )
    
    ma_tai_san = fields.Char(related='tai_san_id.ma_tai_san', string='Mã TS', store=True)
    ten_tai_san = fields.Char(related='tai_san_id.ten_tai_san', string='Tên TS', store=True)
    
    # ===== FEATURES (Đặc trưng đầu vào) =====
    tuoi_tai_san = fields.Integer(
        'Tuổi tài sản (tháng)',
        compute='_compute_features',
        store=True,
        help='Số tháng từ khi mua đến nay'
    )
    
    so_lan_bao_tri = fields.Integer(
        'Số lần bảo trì',
        compute='_compute_features',
        store=True
    )
    
    tong_chi_phi_bao_tri = fields.Float(
        'Tổng chi phí bảo trì',
        compute='_compute_features',
        store=True,
        digits=(16, 2)
    )
    
    ty_le_chi_phi_bao_tri = fields.Float(
        'Tỷ lệ chi phí/Giá mua (%)',
        compute='_compute_features',
        store=True,
        help='(Tổng chi phí bảo trì / Giá mua) × 100'
    )
    
    ty_le_khau_hao = fields.Float(
        'Tỷ lệ khấu hao (%)',
        compute='_compute_features',
        store=True,
        help='(Giá đã khấu hao / Giá mua) × 100'
    )
    
    tan_suat_su_dung = fields.Float(
        'Tần suất sử dụng (lần/tháng)',
        compute='_compute_features',
        store=True,
        help='Số lần mượn / Tuổi tài sản'
    )
    
    so_lan_hong = fields.Integer(
        'Số lần hỏng',
        compute='_compute_features',
        store=True
    )
    
    khoang_cach_bao_tri_tb = fields.Float(
        'Khoảng cách bảo trì TB (ngày)',
        compute='_compute_features',
        store=True,
        help='Trung bình số ngày giữa các lần bảo trì'
    )
    
    # ===== PREDICTIONS (Dự đoán) =====
    ngay_bao_tri_du_kien = fields.Date(
        'Dự kiến bảo trì tiếp theo',
        compute='_compute_predictions',
        store=True
    )
    
    ngay_cap_nhat = fields.Datetime(
        'Ngày cập nhật dự đoán',
        default=fields.Datetime.now,
        readonly=True
    )
    
    xac_suat_hong = fields.Float(
        'Xác suất hỏng (%)',
        compute='_compute_predictions',
        store=True,
        digits=(5, 2),
        help='Xác suất tài sản bị hỏng trong 6 tháng tới'
    )
    
    de_xuat_thanh_ly = fields.Boolean(
        'Đề xuất thanh lý',
        compute='_compute_predictions',
        store=True
    )
    
    ly_do_de_xuat = fields.Text(
        'Lý do đề xuất',
        compute='_compute_predictions',
        store=True
    )
    
    do_uu_tien = fields.Selection([
        ('thap', 'Thấp'),
        ('trung_binh', 'Trung bình'),
        ('cao', 'Cao'),
        ('khan_cap', 'Khẩn cấp'),
    ], string='Độ ưu tiên', compute='_compute_predictions', store=True)
    
    # Model info
    model_version = fields.Char('Phiên bản model', default='v1.0 - Rule Based')
    phuong_phap = fields.Char('Phương pháp', default='Rule-based AI')
    
    active = fields.Boolean('Đang hoạt động', default=True)
    
    @api.depends('tai_san_id', 'tai_san_id.ngay_mua', 'tai_san_id.gia_tien_mua', 
                 'tai_san_id.gia_tri_hien_tai')
    def _compute_features(self):
        """Tính toán các đặc trưng (features)"""
        for record in self:
            tai_san = record.tai_san_id
            
            if not tai_san:
                continue
            
            # 1. Tuổi tài sản
            if tai_san.ngay_mua:
                ngay_mua = fields.Date.from_string(tai_san.ngay_mua)
                ngay_hien_tai = fields.Date.today()
                record.tuoi_tai_san = ((ngay_hien_tai.year - ngay_mua.year) * 12 + 
                                      (ngay_hien_tai.month - ngay_mua.month))
            else:
                record.tuoi_tai_san = 0
            
            # 2. Bảo trì
            lich_su_bao_tri = self.env['lich_su_bao_tri'].search([
                ('tai_san_id', '=', tai_san.id)
            ])
            record.so_lan_bao_tri = len(lich_su_bao_tri)
            record.tong_chi_phi_bao_tri = sum(lich_su_bao_tri.mapped('chi_phi'))
            
            # 3. Tỷ lệ chi phí
            if tai_san.gia_tien_mua > 0:
                record.ty_le_chi_phi_bao_tri = (record.tong_chi_phi_bao_tri / tai_san.gia_tien_mua) * 100
            else:
                record.ty_le_chi_phi_bao_tri = 0
            
            # 4. Tỷ lệ khấu hao
            if tai_san.gia_tien_mua > 0:
                da_khau_hao = tai_san.gia_tien_mua - tai_san.gia_tri_hien_tai
                record.ty_le_khau_hao = (da_khau_hao / tai_san.gia_tien_mua) * 100
            else:
                record.ty_le_khau_hao = 0
            
            # 5. Tần suất sử dụng
            so_lan_muon = self.env['phieu_muon'].search_count([
                ('tai_san_id', '=', tai_san.id),
                ('state', '=', 'done')
            ])
            if record.tuoi_tai_san > 0:
                record.tan_suat_su_dung = so_lan_muon / record.tuoi_tai_san
            else:
                record.tan_suat_su_dung = 0
            
            # 6. Số lần hỏng
            record.so_lan_hong = self.env['lich_su_kiem_ke'].search_count([
                ('tai_san_id', '=', tai_san.id),
                ('trang_thai_kiem_ke', 'in', ['hong_hoc', 'sua_chua'])
            ])
            
            # 7. Khoảng cách bảo trì trung bình
            if len(lich_su_bao_tri) >= 2:
                lich_su_sorted = lich_su_bao_tri.sorted('ngay_bao_tri', reverse=True)
                khoang_cach = []
                for i in range(len(lich_su_sorted) - 1):
                    ngay_1 = lich_su_sorted[i].ngay_bao_tri
                    ngay_2 = lich_su_sorted[i + 1].ngay_bao_tri
                    if ngay_1 and ngay_2:
                        delta = (ngay_1 - ngay_2).days
                        if delta > 0:
                            khoang_cach.append(delta)
                
                if khoang_cach:
                    record.khoang_cach_bao_tri_tb = sum(khoang_cach) / len(khoang_cach)
                else:
                    record.khoang_cach_bao_tri_tb = 0
            else:
                record.khoang_cach_bao_tri_tb = 0
    
    @api.depends('tuoi_tai_san', 'so_lan_bao_tri', 'ty_le_chi_phi_bao_tri', 
                 'ty_le_khau_hao', 'so_lan_hong', 'khoang_cach_bao_tri_tb')
    def _compute_predictions(self):
        """Dự đoán sử dụng Rule-based AI"""
        for record in self:
            # 1. Dự đoán ngày bảo trì tiếp theo
            record.ngay_bao_tri_du_kien = record._predict_maintenance_date()
            
            # 2. Tính xác suất hỏng
            record.xac_suat_hong = record._calculate_failure_probability()
            
            # 3. Đề xuất thanh lý
            record.de_xuat_thanh_ly, record.ly_do_de_xuat = record._recommend_liquidation()
            
            # 4. Độ ưu tiên
            record.do_uu_tien = record._calculate_priority()
    
    def _predict_maintenance_date(self):
        """Dự đoán ngày bảo trì tiếp theo (Rule-based)"""
        self.ensure_one()
        
        lich_su_bao_tri = self.env['lich_su_bao_tri'].search([
            ('tai_san_id', '=', self.tai_san_id.id)
        ], order='ngay_bao_tri desc', limit=1)
        
        if not lich_su_bao_tri:
            # Chưa có lịch sử → Dự kiến 6 tháng
            return fields.Date.today() + timedelta(days=180)
        
        ngay_bao_tri_cuoi = lich_su_bao_tri.ngay_bao_tri
        
        if self.khoang_cach_bao_tri_tb > 0:
            # Có dữ liệu lịch sử → Dự đoán theo pattern
            ngay_du_kien = ngay_bao_tri_cuoi + timedelta(days=self.khoang_cach_bao_tri_tb)
        else:
            # Mặc định: 6 tháng
            ngay_du_kien = ngay_bao_tri_cuoi + timedelta(days=180)
        
        return ngay_du_kien
    
    def _calculate_failure_probability(self):
        """
        Tính xác suất hỏng (Rule-based scoring)
        
        Điểm = w1 × Điểm_tuổi 
             + w2 × Điểm_bảo_trì 
             + w3 × Điểm_chi_phí 
             + w4 × Điểm_khấu_hao
             + w5 × Điểm_hỏng
        """
        self.ensure_one()
        
        score = 0
        
        # 1. Tuổi tài sản (max 30 điểm)
        if self.tuoi_tai_san > 60:  # > 5 năm
            score += 30
        elif self.tuoi_tai_san > 36:  # > 3 năm
            score += 20
        elif self.tuoi_tai_san > 24:  # > 2 năm
            score += 10
        
        # 2. Tần suất bảo trì (max 25 điểm)
        if self.so_lan_bao_tri > 15:
            score += 25
        elif self.so_lan_bao_tri > 10:
            score += 20
        elif self.so_lan_bao_tri > 5:
            score += 10
        
        # 3. Chi phí bảo trì vs Giá trị (max 25 điểm)
        if self.ty_le_chi_phi_bao_tri > 60:
            score += 25
        elif self.ty_le_chi_phi_bao_tri > 40:
            score += 20
        elif self.ty_le_chi_phi_bao_tri > 20:
            score += 10
        
        # 4. Khấu hao (max 15 điểm)
        if self.ty_le_khau_hao > 90:
            score += 15
        elif self.ty_le_khau_hao > 70:
            score += 10
        elif self.ty_le_khau_hao > 50:
            score += 5
        
        # 5. Số lần hỏng (max 20 điểm)
        if self.so_lan_hong >= 5:
            score += 20
        elif self.so_lan_hong >= 3:
            score += 15
        elif self.so_lan_hong >= 1:
            score += 10
        
        # Bonus: Nếu bảo trì gần đây (tăng rủi ro)
        if self.khoang_cach_bao_tri_tb > 0:
            ngay_bao_tri_cuoi = self.env['lich_su_bao_tri'].search([
                ('tai_san_id', '=', self.tai_san_id.id)
            ], order='ngay_bao_tri desc', limit=1).ngay_bao_tri
            
            if ngay_bao_tri_cuoi:
                ngay_qua = (fields.Date.today() - ngay_bao_tri_cuoi).days
                if ngay_qua > self.khoang_cach_bao_tri_tb * 1.5:
                    score += 15  # Quá hạn bảo trì
        
        return min(score, 100)
    
    def _recommend_liquidation(self):
        """Đề xuất thanh lý (Rule-based decision tree)"""
        self.ensure_one()
        
        reasons = []
        should_liquidate = False
        
        # Quy tắc 1: Xác suất hỏng cao
        if self.xac_suat_hong > 75:
            reasons.append(f"• Xác suất hỏng rất cao ({self.xac_suat_hong:.1f}%)")
            should_liquidate = True
        
        # Quy tắc 2: Chi phí bảo trì quá cao
        if self.ty_le_chi_phi_bao_tri > 70:
            reasons.append(f"• Chi phí bảo trì = {self.ty_le_chi_phi_bao_tri:.1f}% giá mua (quá cao)")
            should_liquidate = True
        
        # Quy tắc 3: Khấu hao gần hết + nhiều lần hỏng
        if self.ty_le_khau_hao > 90 and self.so_lan_hong >= 3:
            reasons.append(f"• Đã khấu hao {self.ty_le_khau_hao:.1f}% + hỏng {self.so_lan_hong} lần")
            should_liquidate = True
        
        # Quy tắc 4: Tuổi cao + ít sử dụng
        if self.tuoi_tai_san > 60 and self.tan_suat_su_dung < 0.5:
            reasons.append(f"• Tuổi cao ({self.tuoi_tai_san} tháng) + ít sử dụng ({self.tan_suat_su_dung:.2f} lần/tháng)")
            should_liquidate = True
        
        # Quy tắc 5: Giá trị còn lại quá thấp
        if self.tai_san_id.gia_tri_hien_tai < self.tai_san_id.gia_tien_mua * 0.05:
            reasons.append(f"• Giá trị còn lại < 5% nguyên giá")
            should_liquidate = True
        
        if reasons:
            ly_do = "\n".join(reasons)
            ly_do += f"\n\n📊 Thống kê:\n"
            ly_do += f"  - Tuổi: {self.tuoi_tai_san} tháng\n"
            ly_do += f"  - Bảo trì: {self.so_lan_bao_tri} lần ({self.tong_chi_phi_bao_tri:,.0f} VNĐ)\n"
            ly_do += f"  - Khấu hao: {self.ty_le_khau_hao:.1f}%\n"
            ly_do += f"  - Xác suất hỏng: {self.xac_suat_hong:.1f}%\n"
            ly_do += f"\n💡 Đề xuất: {'THANH LÝ' if should_liquidate else 'Theo dõi'}"
        else:
            ly_do = "Tài sản hoạt động tốt, không cần thanh lý."
        
        return should_liquidate, ly_do
    
    def _calculate_priority(self):
        """Tính độ ưu tiên theo dõi"""
        self.ensure_one()
        
        if self.de_xuat_thanh_ly:
            return 'khan_cap'
        elif self.xac_suat_hong > 60:
            return 'cao'
        elif self.xac_suat_hong > 30:
            return 'trung_binh'
        else:
            return 'thap'
    
    def action_update_predictions(self):
        """Cập nhật lại dự đoán (thủ công)"""
        self._compute_features()
        self._compute_predictions()
        self.write({'ngay_cap_nhat': fields.Datetime.now()})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Cập nhật thành công'),
                'message': f'Đã cập nhật dự đoán cho tài sản {self.ten_tai_san}',
                'type': 'success',
                'sticky': False,
            }
        }
    
    @api.model
    def cron_update_all_predictions(self):
        """Cron job: Cập nhật dự đoán cho tất cả tài sản"""
        _logger.info("=" * 60)
        _logger.info("BẮT ĐẦU CẬP NHẬT DỰ ĐOÁN AI")
        _logger.info("=" * 60)
        
        # Lấy hoặc tạo mới predictor cho tất cả tài sản
        tai_san_records = self.env['tai_san'].search([
            ('trang_thai', '!=', 'DaThanhLy')
        ])
        
        for tai_san in tai_san_records:
            predictor = self.search([('tai_san_id', '=', tai_san.id)], limit=1)
            
            if not predictor:
                predictor = self.create({'tai_san_id': tai_san.id})
            else:
                predictor._compute_features()
                predictor._compute_predictions()
                predictor.write({'ngay_cap_nhat': fields.Datetime.now()})
        
        _logger.info(f"Đã cập nhật dự đoán cho {len(tai_san_records)} tài sản")
        _logger.info("=" * 60)
        
        return True
