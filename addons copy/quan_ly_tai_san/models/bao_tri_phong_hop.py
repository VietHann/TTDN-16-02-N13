# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class BaoTriPhongHop(models.Model):
    _name = 'bao_tri_phong_hop'
    _description = 'Bảo trì phòng họp'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'ma_bao_tri'
    _order = 'ngay_bat_dau desc'

    ma_bao_tri = fields.Char(
        "Mã bảo trì",
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
        help="Phòng cần bảo trì"
    )

    ngay_bat_dau = fields.Date(
        "Ngày bắt đầu",
        required=True,
        default=fields.Date.today,
        tracking=True,
        help="Ngày bắt đầu bảo trì"
    )

    ngay_ket_thuc = fields.Date(
        "Ngày kết thúc",
        tracking=True,
        help="Ngày hoàn thành bảo trì"
    )

    LOAI_BAO_TRI = [
        ('dinh_ky', 'Định kỳ'),
        ('sua_chua', 'Sửa chữa'),
        ('bao_duong', 'Bảo dưỡng'),
    ]

    loai_bao_tri = fields.Selection(
        LOAI_BAO_TRI,
        string="Loại bảo trì",
        default='dinh_ky',
        required=True,
        help="Loại công việc bảo trì"
    )

    TRANG_THAI = [
        ('ke_hoach', 'Kế hoạch'),
        ('dang_thuc_hien', 'Đang thực hiện'),
        ('hoan_thanh', 'Hoàn thành'),
        ('huy', 'Hủy'),
    ]

    trang_thai = fields.Selection(
        TRANG_THAI,
        string="Trạng thái",
        default='ke_hoach',
        required=True,
        tracking=True,
        help="Trạng thái bảo trì"
    )

    nguoi_thuc_hien_id = fields.Many2one(
        'nhan_vien',
        string="Người thực hiện",
        help="Nhân viên phụ trách bảo trì"
    )

    noi_dung = fields.Text(
        "Nội dung bảo trì",
        required=True,
        help="Mô tả công việc cần làm"
    )

    ket_qua = fields.Text(
        "Kết quả",
        help="Kết quả sau khi bảo trì"
    )

    chi_phi = fields.Float(
        "Chi phí",
        digits=(16, 2),
        help="Chi phí bảo trì"
    )

    ghi_chu = fields.Text("Ghi chú")

    _sql_constraints = [
        ('ma_bao_tri_unique', 'unique(ma_bao_tri)', 'Mã bảo trì phải là duy nhất!')
    ]

    @api.constrains('ngay_bat_dau', 'ngay_ket_thuc')
    def _check_dates(self):
        for record in self:
            if record.ngay_ket_thuc and record.ngay_bat_dau:
                if record.ngay_ket_thuc < record.ngay_bat_dau:
                    raise ValidationError("Ngày kết thúc phải sau ngày bắt đầu!")

    @api.model
    def create(self, vals):
        if vals.get('ma_bao_tri', 'New') == 'New':
            vals['ma_bao_tri'] = self.env['ir.sequence'].next_by_code('bao_tri_phong_hop') or 'BTPH-00001'
        return super(BaoTriPhongHop, self).create(vals)

    def action_bat_dau(self):
        """Bắt đầu bảo trì"""
        for record in self:
            if record.trang_thai != 'ke_hoach':
                raise UserError("Chỉ kế hoạch mới có thể bắt đầu!")
            
            # Chuyển phòng sang trạng thái bảo trì
            record.phong_hop_id.trang_thai = 'bao_tri'
            record.trang_thai = 'dang_thuc_hien'

    def action_hoan_thanh(self):
        """Hoàn thành bảo trì"""
        for record in self:
            if record.trang_thai != 'dang_thuc_hien':
                raise UserError("Chỉ công việc đang thực hiện mới có thể hoàn thành!")
            
            # Trả phòng về trạng thái sẵn sàng
            record.phong_hop_id.trang_thai = 'san_sang'
            record.ngay_ket_thuc = fields.Date.today()
            record.trang_thai = 'hoan_thanh'

    def action_huy(self):
        """Hủy bảo trì"""
        for record in self:
            if record.trang_thai == 'hoan_thanh':
                raise UserError("Không thể hủy công việc đã hoàn thành!")
            
            # Trả phòng về trạng thái sẵn sàng nếu đang bảo trì
            if record.trang_thai == 'dang_thuc_hien':
                record.phong_hop_id.trang_thai = 'san_sang'
            
            record.trang_thai = 'huy'
