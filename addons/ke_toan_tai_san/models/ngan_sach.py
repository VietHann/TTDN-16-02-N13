# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class NganSach(models.Model):
    _name = 'ke_toan.ngan_sach'
    _description = 'Quản lý ngân sách'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'ten_ngan_sach'
    _order = 'nam desc, don_vi_id'

    ten_ngan_sach = fields.Char(
        "Tên ngân sách",
        required=True,
        help="Tên kế hoạch ngân sách"
    )

    nam = fields.Integer(
        "Năm",
        required=True,
        default=lambda self: fields.Date.today().year,
        tracking=True,
        help="Năm áp dụng ngân sách"
    )

    QUY = [
        ('q1', 'Quý 1'),
        ('q2', 'Quý 2'),
        ('q3', 'Quý 3'),
        ('q4', 'Quý 4'),
        ('ca_nam', 'Cả năm'),
    ]

    quy = fields.Selection(
        QUY,
        string="Quý",
        default='ca_nam',
        required=True,
        help="Quý áp dụng"
    )

    don_vi_id = fields.Many2one(
        'don_vi',
        string="Đơn vị",
        required=True,
        tracking=True,
        help="Đơn vị/Phòng ban được cấp ngân sách"
    )

    ngan_sach_du_kien = fields.Float(
        "Ngân sách dự kiến",
        required=True,
        digits=(16, 2),
        tracking=True,
        help="Số tiền ngân sách được phê duyệt"
    )

    ngan_sach_da_su_dung = fields.Float(
        "Đã sử dụng",
        compute='_compute_da_su_dung',
        store=True,
        digits=(16, 2),
        help="Số tiền đã chi"
    )

    ngan_sach_con_lai = fields.Float(
        "Còn lại",
        compute='_compute_con_lai',
        store=True,
        digits=(16, 2),
        help="Ngân sách còn lại"
    )

    ty_le_su_dung = fields.Float(
        "Tỷ lệ sử dụng (%)",
        compute='_compute_ty_le',
        store=True,
        help="% ngân sách đã sử dụng"
    )

    TRANG_THAI = [
        ('du_thao', 'Dự thảo'),
        ('da_duyet', 'Đã duyệt'),
        ('dang_thuc_hien', 'Đang thực hiện'),
        ('hoan_thanh', 'Hoàn thành'),
        ('vuot_ngan_sach', 'Vượt ngân sách'),
    ]

    trang_thai = fields.Selection(
        TRANG_THAI,
        string="Trạng thái",
        default='du_thao',
        required=True,
        tracking=True,
        help="Trạng thái ngân sách"
    )

    chi_tiet_ids = fields.One2many(
        'ke_toan.ngan_sach.chi_tiet',
        'ngan_sach_id',
        string="Chi tiết ngân sách",
        help="Phân bổ chi tiết theo mục"
    )

    nguoi_phu_trach_id = fields.Many2one(
        'nhan_vien',
        string="Người phụ trách",
        required=True,
        help="Người quản lý ngân sách"
    )

    ghi_chu = fields.Text("Ghi chú")

    _sql_constraints = [
        ('unique_ngan_sach', 'unique(nam, quy, don_vi_id)',
         'Đơn vị đã có ngân sách cho năm và quý này!')
    ]

    @api.depends('chi_tiet_ids', 'chi_tiet_ids.da_su_dung')
    def _compute_da_su_dung(self):
        for record in self:
            record.ngan_sach_da_su_dung = sum(record.chi_tiet_ids.mapped('da_su_dung'))

    @api.depends('ngan_sach_du_kien', 'ngan_sach_da_su_dung')
    def _compute_con_lai(self):
        for record in self:
            record.ngan_sach_con_lai = record.ngan_sach_du_kien - record.ngan_sach_da_su_dung
            
            # Tự động cập nhật trạng thái
            if record.trang_thai == 'dang_thuc_hien':
                if record.ngan_sach_con_lai < 0:
                    record.trang_thai = 'vuot_ngan_sach'

    @api.depends('ngan_sach_du_kien', 'ngan_sach_da_su_dung')
    def _compute_ty_le(self):
        for record in self:
            if record.ngan_sach_du_kien > 0:
                record.ty_le_su_dung = (record.ngan_sach_da_su_dung / record.ngan_sach_du_kien) * 100
            else:
                record.ty_le_su_dung = 0

    @api.constrains('ngan_sach_du_kien')
    def _check_ngan_sach(self):
        for record in self:
            if record.ngan_sach_du_kien <= 0:
                raise ValidationError("Ngân sách dự kiến phải lớn hơn 0!")


class NganSachChiTiet(models.Model):
    _name = 'ke_toan.ngan_sach.chi_tiet'
    _description = 'Chi tiết ngân sách theo mục'

    ngan_sach_id = fields.Many2one(
        'ke_toan.ngan_sach',
        string="Ngân sách",
        required=True,
        ondelete='cascade'
    )

    MUC_CHI = [
        ('nhan_su', 'Nhân sự'),
        ('van_phong', 'Văn phòng'),
        ('tai_san', 'Tài sản'),
        ('marketing', 'Marketing'),
        ('dao_tao', 'Đào tạo'),
        ('khac', 'Khác'),
    ]

    muc_chi = fields.Selection(
        MUC_CHI,
        string="Mục chi",
        required=True,
        help="Loại chi phí"
    )

    ten_muc = fields.Char(
        "Tên mục",
        help="Mô tả cụ thể"
    )

    ngan_sach_phan_bo = fields.Float(
        "Ngân sách phân bổ",
        required=True,
        digits=(16, 2),
        help="Số tiền phân bổ cho mục này"
    )

    da_su_dung = fields.Float(
        "Đã sử dụng",
        digits=(16, 2),
        help="Số tiền đã chi cho mục này"
    )

    con_lai = fields.Float(
        "Còn lại",
        compute='_compute_con_lai',
        store=True,
        digits=(16, 2),
        help="Số tiền còn lại"
    )

    ghi_chu = fields.Text("Ghi chú")

    @api.depends('ngan_sach_phan_bo', 'da_su_dung')
    def _compute_con_lai(self):
        for record in self:
            record.con_lai = record.ngan_sach_phan_bo - record.da_su_dung

    @api.constrains('ngan_sach_phan_bo')
    def _check_ngan_sach_phan_bo(self):
        for record in self:
            if record.ngan_sach_phan_bo <= 0:
                raise ValidationError("Ngân sách phân bổ phải lớn hơn 0!")
