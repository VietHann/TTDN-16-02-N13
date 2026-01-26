# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class NangCapPhongHop(models.Model):
    _name = 'nang_cap_phong_hop'
    _description = 'Nâng cấp phòng họp'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'ma_nang_cap'
    _order = 'ngay_nang_cap desc'

    ma_nang_cap = fields.Char(
        "Mã nâng cấp",
        required=True,
        copy=False,
        readonly=True,
        default="New",
        help="Mã tự động"
    )

    phong_hop_id = fields.Many2one(
        'phong_hop',
        string="Phòng họp",
        required=True,
        tracking=True,
        help="Phòng được nâng cấp"
    )

    ngay_nang_cap = fields.Date(
        "Ngày nâng cấp",
        required=True,
        default=fields.Date.today,
        tracking=True,
        help="Ngày thực hiện nâng cấp"
    )

    ngay_hoan_thanh = fields.Date(
        "Ngày hoàn thành",
        tracking=True,
        help="Ngày hoàn thành nâng cấp"
    )

    LOAI_NANG_CAP = [
        ('thiet_bi', 'Thêm thiết bị'),
        ('sua_chua', 'Sửa chữa/Cải tạo'),
        ('mo_rong', 'Mở rộng không gian'),
        ('trang_tri', 'Trang trí/Nội thất'),
    ]

    loai_nang_cap = fields.Selection(
        LOAI_NANG_CAP,
        string="Loại nâng cấp",
        required=True,
        help="Loại công việc nâng cấp"
    )

    TRANG_THAI = [
        ('de_xuat', 'Đề xuất'),
        ('da_duyet', 'Đã duyệt'),
        ('dang_thuc_hien', 'Đang thực hiện'),
        ('hoan_thanh', 'Hoàn thành'),
        ('tu_choi', 'Từ chối'),
    ]

    trang_thai = fields.Selection(
        TRANG_THAI,
        string="Trạng thái",
        default='de_xuat',
        required=True,
        tracking=True,
        help="Trạng thái nâng cấp"
    )

    noi_dung = fields.Text(
        "Nội dung nâng cấp",
        required=True,
        help="Mô tả chi tiết công việc nâng cấp"
    )

    ly_do = fields.Text(
        "Lý do nâng cấp",
        help="Lý do cần nâng cấp phòng"
    )

    ket_qua = fields.Text(
        "Kết quả",
        help="Kết quả sau khi nâng cấp"
    )

    nguoi_de_xuat_id = fields.Many2one(
        'nhan_vien',
        string="Người đề xuất",
        required=True,
        help="Người đề xuất nâng cấp"
    )

    nguoi_duyet_id = fields.Many2one(
        'nhan_vien',
        string="Người duyệt",
        readonly=True,
        tracking=True,
        help="Người phê duyệt nâng cấp"
    )

    nguoi_thuc_hien_id = fields.Many2one(
        'nhan_vien',
        string="Người thực hiện",
        help="Người phụ trách thực hiện"
    )

    nha_cung_cap_id = fields.Many2one(
        'nha_cung_cap',
        string="Nhà cung cấp",
        help="Nhà cung cấp dịch vụ nâng cấp"
    )

    chi_phi_du_kien = fields.Float(
        "Chi phí dự kiến",
        digits=(16, 2),
        help="Chi phí ước tính"
    )

    chi_phi_thuc_te = fields.Float(
        "Chi phí thực tế",
        digits=(16, 2),
        help="Chi phí thực tế phát sinh"
    )

    thiet_bi_moi_ids = fields.Many2many(
        'tai_san',
        'nang_cap_phong_hop_tai_san_rel',
        'nang_cap_id',
        'tai_san_id',
        string="Thiết bị mới thêm",
        help="Các thiết bị được bổ sung vào phòng"
    )

    ghi_chu = fields.Text("Ghi chú")

    _sql_constraints = [
        ('ma_nang_cap_unique', 'unique(ma_nang_cap)', 'Mã nâng cấp phải là duy nhất!')
    ]

    @api.constrains('ngay_nang_cap', 'ngay_hoan_thanh')
    def _check_dates(self):
        for record in self:
            if record.ngay_hoan_thanh and record.ngay_nang_cap:
                if record.ngay_hoan_thanh < record.ngay_nang_cap:
                    raise ValidationError("Ngày hoàn thành phải sau ngày nâng cấp!")

    @api.model
    def create(self, vals):
        if vals.get('ma_nang_cap', 'New') == 'New':
            vals['ma_nang_cap'] = self.env['ir.sequence'].next_by_code('nang_cap_phong_hop') or 'NCPH-00001'
        return super(NangCapPhongHop, self).create(vals)

    def action_duyet(self):
        """Duyệt đề xuất nâng cấp"""
        for record in self:
            if record.trang_thai != 'de_xuat':
                raise UserError("Chỉ đề xuất mới có thể duyệt!")
            
            record.write({
                'trang_thai': 'da_duyet',
            })

    def action_tu_choi(self):
        """Từ chối đề xuất"""
        for record in self:
            if record.trang_thai != 'de_xuat':
                raise UserError("Chỉ đề xuất mới có thể từ chối!")
            
            record.write({
                'trang_thai': 'tu_choi',
            })

    def action_bat_dau(self):
        """Bắt đầu nâng cấp"""
        for record in self:
            if record.trang_thai != 'da_duyet':
                raise UserError("Chỉ đề xuất đã duyệt mới có thể bắt đầu!")
            
            # Chuyển phòng sang trạng thái bảo trì
            record.phong_hop_id.trang_thai = 'bao_tri'
            record.trang_thai = 'dang_thuc_hien'

    def action_hoan_thanh(self):
        """Hoàn thành nâng cấp"""
        for record in self:
            if record.trang_thai != 'dang_thuc_hien':
                raise UserError("Chỉ công việc đang thực hiện mới có thể hoàn thành!")
            
            # Thêm thiết bị mới vào phòng
            if record.thiet_bi_moi_ids:
                record.phong_hop_id.thiet_bi_ids = [(4, tb.id) for tb in record.thiet_bi_moi_ids]
            
            # Trả phòng về trạng thái sẵn sàng
            record.phong_hop_id.trang_thai = 'san_sang'
            record.ngay_hoan_thanh = fields.Date.today()
            record.trang_thai = 'hoan_thanh'
