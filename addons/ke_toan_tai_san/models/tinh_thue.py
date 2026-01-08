# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class TinhThue(models.Model):
    _name = 'ke_toan.tinh_thue'
    _description = 'Tính thuế'
    _rec_name = 'ten_ke_hoach'
    _order = 'thang desc, nam desc'

    ten_ke_hoach = fields.Char(
        "Tên kế hoạch",
        required=True,
        help="Tên kế hoạch tính thuế"
    )

    thang = fields.Selection(
        [(str(i), str(i)) for i in range(1, 13)],
        string="Tháng",
        required=True,
        help="Tháng tính thuế"
    )

    nam = fields.Integer(
        "Năm",
        required=True,
        default=lambda self: fields.Date.today().year,
        help="Năm tính thuế"
    )

    LOAI_THUE = [
        ('vat', 'Thuế GTGT'),
        ('thu_nhap_dn', 'Thuế thu nhập DN'),
        ('thu_nhap_ca_nhan', 'Thuế TNCN'),
    ]

    loai_thue = fields.Selection(
        LOAI_THUE,
        string="Loại thuế",
        required=True,
        help="Loại thuế cần tính"
    )

    don_vi_id = fields.Many2one(
        'don_vi',
        string="Đơn vị",
        help="Đơn vị nộp thuế"
    )

    # Thuế GTGT
    doanh_thu = fields.Float(
        "Doanh thu",
        digits=(16, 2),
        help="Tổng doanh thu chịu thuế"
    )

    thue_suat_vat = fields.Float(
        "Thuế suất VAT (%)",
        default=10.0,
        help="Thuế suất GTGT"
    )

    thue_vat = fields.Float(
        "Thuế VAT phải nộp",
        compute='_compute_thue_vat',
        store=True,
        digits=(16, 2),
        help="Số thuế GTGT phải nộp"
    )

    # Thuế TNDN
    loi_nhuan_truoc_thue = fields.Float(
        "Lợi nhuận trước thuế",
        digits=(16, 2),
        help="Thu nhập chịu thuế"
    )

    thue_suat_tndn = fields.Float(
        "Thuế suất TNDN (%)",
        default=20.0,
        help="Thuế suất thu nhập doanh nghiệp"
    )

    thue_tndn = fields.Float(
        "Thuế TNDN phải nộp",
        compute='_compute_thue_tndn',
        store=True,
        digits=(16, 2),
        help="Số thuế TNDN phải nộp"
    )

    # Thuế TNCN
    tong_luong = fields.Float(
        "Tổng lương",
        digits=(16, 2),
        help="Tổng thu nhập từ lương"
    )

    giam_tru = fields.Float(
        "Giảm trừ",
        default=11000000,
        digits=(16, 2),
        help="Giảm trừ gia cảnh (11tr/tháng)"
    )

    thu_nhap_tinh_thue = fields.Float(
        "Thu nhập tính thuế",
        compute='_compute_thu_nhap_tinh_thue',
        store=True,
        digits=(16, 2),
        help="Thu nhập sau giảm trừ"
    )

    thue_tncn = fields.Float(
        "Thuế TNCN phải nộp",
        compute='_compute_thue_tncn',
        store=True,
        digits=(16, 2),
        help="Số thuế TNCN phải nộp"
    )

    # Chung
    tong_thue_phai_nop = fields.Float(
        "Tổng thuế phải nộp",
        compute='_compute_tong_thue',
        store=True,
        digits=(16, 2),
        help="Tổng số thuế phải nộp"
    )

    TRANG_THAI = [
        ('du_thao', 'Dự thảo'),
        ('da_tinh', 'Đã tính'),
        ('da_nop', 'Đã nộp'),
    ]

    trang_thai = fields.Selection(
        TRANG_THAI,
        string="Trạng thái",
        default='du_thao',
        required=True,
        help="Trạng thái"
    )

    ngay_nop = fields.Date(
        "Ngày nộp",
        help="Ngày nộp thuế"
    )

    nguoi_tinh_id = fields.Many2one(
        'nhan_vien',
        string="Người tính",
        help="Người lập bảng tính thuế"
    )

    ghi_chu = fields.Text("Ghi chú")

    @api.depends('doanh_thu', 'thue_suat_vat')
    def _compute_thue_vat(self):
        for record in self:
            if record.loai_thue == 'vat':
                record.thue_vat = record.doanh_thu * record.thue_suat_vat / 100
            else:
                record.thue_vat = 0

    @api.depends('loi_nhuan_truoc_thue', 'thue_suat_tndn')
    def _compute_thue_tndn(self):
        for record in self:
            if record.loai_thue == 'thu_nhap_dn':
                record.thue_tndn = record.loi_nhuan_truoc_thue * record.thue_suat_tndn / 100
            else:
                record.thue_tndn = 0

    @api.depends('tong_luong', 'giam_tru')
    def _compute_thu_nhap_tinh_thue(self):
        for record in self:
            if record.loai_thue == 'thu_nhap_ca_nhan':
                record.thu_nhap_tinh_thue = max(0, record.tong_luong - record.giam_tru)
            else:
                record.thu_nhap_tinh_thue = 0

    @api.depends('thu_nhap_tinh_thue')
    def _compute_thue_tncn(self):
        """Tính thuế TNCN theo biểu thuế lũy tiến từng phần"""
        for record in self:
            if record.loai_thue == 'thu_nhap_ca_nhan':
                thu_nhap = record.thu_nhap_tinh_thue
                thue = 0
                
                # Biểu thuế lũy tiến từng phần (tháng)
                if thu_nhap <= 5000000:
                    thue = thu_nhap * 0.05
                elif thu_nhap <= 10000000:
                    thue = 5000000 * 0.05 + (thu_nhap - 5000000) * 0.10
                elif thu_nhap <= 18000000:
                    thue = 5000000 * 0.05 + 5000000 * 0.10 + (thu_nhap - 10000000) * 0.15
                elif thu_nhap <= 32000000:
                    thue = 5000000 * 0.05 + 5000000 * 0.10 + 8000000 * 0.15 + (thu_nhap - 18000000) * 0.20
                elif thu_nhap <= 52000000:
                    thue = 5000000 * 0.05 + 5000000 * 0.10 + 8000000 * 0.15 + 14000000 * 0.20 + (thu_nhap - 32000000) * 0.25
                elif thu_nhap <= 80000000:
                    thue = 5000000 * 0.05 + 5000000 * 0.10 + 8000000 * 0.15 + 14000000 * 0.20 + 20000000 * 0.25 + (thu_nhap - 52000000) * 0.30
                else:
                    thue = 5000000 * 0.05 + 5000000 * 0.10 + 8000000 * 0.15 + 14000000 * 0.20 + 20000000 * 0.25 + 28000000 * 0.30 + (thu_nhap - 80000000) * 0.35
                
                record.thue_tncn = thue
            else:
                record.thue_tncn = 0

    @api.depends('thue_vat', 'thue_tndn', 'thue_tncn', 'loai_thue')
    def _compute_tong_thue(self):
        for record in self:
            if record.loai_thue == 'vat':
                record.tong_thue_phai_nop = record.thue_vat
            elif record.loai_thue == 'thu_nhap_dn':
                record.tong_thue_phai_nop = record.thue_tndn
            else:
                record.tong_thue_phai_nop = record.thue_tncn

    def action_tinh_thue(self):
        """Tính toán thuế"""
        for record in self:
            record.trang_thai = 'da_tinh'

    def action_nop_thue(self):
        """Đánh dấu đã nộp thuế"""
        for record in self:
            record.write({
                'trang_thai': 'da_nop',
                'ngay_nop': fields.Date.today(),
            })
