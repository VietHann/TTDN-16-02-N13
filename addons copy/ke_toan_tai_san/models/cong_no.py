# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class CongNo(models.Model):
    _name = 'ke_toan.cong_no'
    _description = 'Quản lý công nợ phải thu/phải trả'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'ma_cong_no'
    _order = 'ngay_phat_sinh desc'

    ma_cong_no = fields.Char(
        "Mã công nợ",
        required=True,
        copy=False,
        readonly=True,
        default="New",
        help="Mã tự động"
    )

    LOAI_CONG_NO = [
        ('phai_thu', 'Phải thu'),
        ('phai_tra', 'Phải trả'),
    ]

    loai_cong_no = fields.Selection(
        LOAI_CONG_NO,
        string="Loại công nợ",
        required=True,
        tracking=True,
        help="Loại công nợ"
    )

    doi_tuong = fields.Char(
        "Đối tượng",
        required=True,
        help="Tên khách hàng/nhà cung cấp"
    )

    nha_cung_cap_id = fields.Many2one(
        'nha_cung_cap',
        string="Nhà cung cấp",
        help="Liên kết với nhà cung cấp (nếu có)"
    )

    ngay_phat_sinh = fields.Date(
        "Ngày phát sinh",
        required=True,
        default=fields.Date.today,
        tracking=True,
        help="Ngày phát sinh công nợ"
    )

    ngay_den_han = fields.Date(
        "Ngày đến hạn",
        tracking=True,
        help="Hạn thanh toán"
    )

    so_tien_goc = fields.Float(
        "Số tiền gốc",
        required=True,
        digits=(16, 2),
        tracking=True,
        help="Tổng số tiền nợ"
    )

    so_tien_da_tra = fields.Float(
        "Đã thanh toán",
        digits=(16, 2),
        compute='_compute_da_tra',
        store=True,
        help="Số tiền đã trả"
    )

    so_tien_con_lai = fields.Float(
        "Còn lại",
        digits=(16, 2),
        compute='_compute_con_lai',
        store=True,
        tracking=True,
        help="Số tiền còn nợ"
    )

    TRANG_THAI = [
        ('chua_thanh_toan', 'Chưa thanh toán'),
        ('dang_thanh_toan', 'Đang thanh toán'),
        ('da_thanh_toan', 'Đã thanh toán'),
        ('qua_han', 'Quá hạn'),
    ]

    trang_thai = fields.Selection(
        TRANG_THAI,
        string="Trạng thái",
        default='chua_thanh_toan',
        required=True,
        compute='_compute_trang_thai',
        store=True,
        tracking=True,
        help="Trạng thái công nợ"
    )

    thanh_toan_ids = fields.One2many(
        'ke_toan.cong_no.thanh_toan',
        'cong_no_id',
        string="Lịch sử thanh toán",
        help="Các lần thanh toán"
    )

    noi_dung = fields.Text(
        "Nội dung",
        required=True,
        help="Diễn giải công nợ"
    )

    nguoi_phu_trach_id = fields.Many2one(
        'nhan_vien',
        string="Người phụ trách",
        help="Người theo dõi công nợ"
    )

    ghi_chu = fields.Text("Ghi chú")

    _sql_constraints = [
        ('ma_cong_no_unique', 'unique(ma_cong_no)', 'Mã công nợ phải là duy nhất!')
    ]

    @api.depends('thanh_toan_ids', 'thanh_toan_ids.so_tien')
    def _compute_da_tra(self):
        for record in self:
            record.so_tien_da_tra = sum(record.thanh_toan_ids.mapped('so_tien'))

    @api.depends('so_tien_goc', 'so_tien_da_tra')
    def _compute_con_lai(self):
        for record in self:
            record.so_tien_con_lai = record.so_tien_goc - record.so_tien_da_tra

    @api.depends('so_tien_con_lai', 'ngay_den_han')
    def _compute_trang_thai(self):
        today = fields.Date.today()
        for record in self:
            if record.so_tien_con_lai <= 0:
                record.trang_thai = 'da_thanh_toan'
            elif record.ngay_den_han and record.ngay_den_han < today:
                record.trang_thai = 'qua_han'
            elif 0 < record.so_tien_con_lai < record.so_tien_goc:
                record.trang_thai = 'dang_thanh_toan'
            else:
                record.trang_thai = 'chua_thanh_toan'

    @api.constrains('so_tien_goc')
    def _check_so_tien(self):
        for record in self:
            if record.so_tien_goc <= 0:
                raise ValidationError("Số tiền gốc phải lớn hơn 0!")

    @api.constrains('ngay_phat_sinh', 'ngay_den_han')
    def _check_dates(self):
        for record in self:
            if record.ngay_den_han and record.ngay_phat_sinh:
                if record.ngay_den_han < record.ngay_phat_sinh:
                    raise ValidationError("Ngày đến hạn phải sau ngày phát sinh!")

    @api.model
    def create(self, vals):
        if vals.get('ma_cong_no', 'New') == 'New':
            if vals.get('loai_cong_no') == 'phai_thu':
                vals['ma_cong_no'] = self.env['ir.sequence'].next_by_code('ke_toan.phai_thu') or 'PT-00001'
            else:
                vals['ma_cong_no'] = self.env['ir.sequence'].next_by_code('ke_toan.phai_tra') or 'PTR-00001'
        return super(CongNo, self).create(vals)

    def action_thanh_toan(self):
        """Tạo phiếu thanh toán"""
        return {
            'name': 'Thanh toán công nợ',
            'type': 'ir.actions.act_window',
            'res_model': 'ke_toan.cong_no.thanh_toan',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_cong_no_id': self.id,
                'default_so_tien': self.so_tien_con_lai,
                'default_ngay_thanh_toan': fields.Date.today(),
            },
        }


class CongNoThanhToan(models.Model):
    _name = 'ke_toan.cong_no.thanh_toan'
    _description = 'Lịch sử thanh toán công nợ'
    _order = 'ngay_thanh_toan desc'

    cong_no_id = fields.Many2one(
        'ke_toan.cong_no',
        string="Công nợ",
        required=True,
        ondelete='cascade'
    )

    ngay_thanh_toan = fields.Date(
        "Ngày thanh toán",
        required=True,
        default=fields.Date.today,
        help="Ngày thực hiện thanh toán"
    )

    so_tien = fields.Float(
        "Số tiền",
        required=True,
        digits=(16, 2),
        help="Số tiền thanh toán"
    )

    PHUONG_THUC = [
        ('tien_mat', 'Tiền mặt'),
        ('chuyen_khoan', 'Chuyển khoản'),
        ('the', 'Thẻ'),
    ]

    phuong_thuc = fields.Selection(
        PHUONG_THUC,
        string="Phương thức",
        default='tien_mat',
        required=True,
        help="Hình thức thanh toán"
    )

    nguoi_thanh_toan_id = fields.Many2one(
        'nhan_vien',
        string="Người thanh toán",
        help="Người thực hiện thanh toán"
    )

    ghi_chu = fields.Text("Ghi chú")

    @api.constrains('so_tien', 'cong_no_id')
    def _check_so_tien(self):
        for record in self:
            if record.so_tien <= 0:
                raise ValidationError("Số tiền thanh toán phải lớn hơn 0!")
            if record.so_tien > record.cong_no_id.so_tien_con_lai:
                raise ValidationError(
                    f"Số tiền thanh toán ({record.so_tien:,.0f}) "
                    f"vượt quá số nợ còn lại ({record.cong_no_id.so_tien_con_lai:,.0f})!"
                )
