# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class HoaDon(models.Model):
    _name = 'ke_toan.hoa_don'
    _description = 'Quản lý hóa đơn'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'so_hoa_don'
    _order = 'ngay_lap desc'

    so_hoa_don = fields.Char(
        "Số hóa đơn",
        required=True,
        copy=False,
        readonly=True,
        default="New",
        help="Số hóa đơn tự động"
    )

    LOAI_HOA_DON = [
        ('ban_hang', 'Bán hàng'),
        ('mua_hang', 'Mua hàng'),
        ('dich_vu', 'Dịch vụ'),
    ]

    loai_hoa_don = fields.Selection(
        LOAI_HOA_DON,
        string="Loại hóa đơn",
        required=True,
        tracking=True,
        help="Loại hóa đơn"
    )

    ngay_lap = fields.Date(
        "Ngày lập",
        required=True,
        default=fields.Date.today,
        tracking=True,
        help="Ngày lập hóa đơn"
    )

    khach_hang = fields.Char(
        "Khách hàng/NCC",
        required=True,
        help="Tên khách hàng hoặc nhà cung cấp"
    )

    ma_so_thue = fields.Char(
        "Mã số thuế",
        help="Mã số thuế của khách hàng/NCC"
    )

    dia_chi = fields.Text(
        "Địa chỉ",
        help="Địa chỉ khách hàng/NCC"
    )

    chi_tiet_ids = fields.One2many(
        'ke_toan.hoa_don.chi_tiet',
        'hoa_don_id',
        string="Chi tiết hóa đơn",
        help="Danh sách hàng hóa/dịch vụ"
    )

    tong_tien_hang = fields.Float(
        "Tổng tiền hàng",
        compute='_compute_tong',
        store=True,
        digits=(16, 2),
        help="Tổng tiền chưa VAT"
    )

    ty_le_thue = fields.Float(
        "Thuế GTGT (%)",
        default=10.0,
        help="Tỷ lệ thuế giá trị gia tăng"
    )

    tien_thue = fields.Float(
        "Tiền thuế",
        compute='_compute_tong',
        store=True,
        digits=(16, 2),
        help="Tiền thuế GTGT"
    )

    tong_thanh_toan = fields.Float(
        "Tổng thanh toán",
        compute='_compute_tong',
        store=True,
        digits=(16, 2),
        tracking=True,
        help="Tổng cộng tiền thanh toán"
    )

    TRANG_THAI = [
        ('nhap', 'Nháp'),
        ('da_xac_nhan', 'Đã xác nhận'),
        ('da_thanh_toan', 'Đã thanh toán'),
        ('huy', 'Hủy'),
    ]

    trang_thai = fields.Selection(
        TRANG_THAI,
        string="Trạng thái",
        default='nhap',
        required=True,
        tracking=True,
        help="Trạng thái hóa đơn"
    )

    nguoi_lap_id = fields.Many2one(
        'nhan_vien',
        string="Người lập",
        required=True,
        help="Người lập hóa đơn"
    )

    cong_no_id = fields.Many2one(
        'ke_toan.cong_no',
        string="Công nợ",
        readonly=True,
        help="Công nợ liên quan"
    )

    ghi_chu = fields.Text("Ghi chú")

    _sql_constraints = [
        ('so_hoa_don_unique', 'unique(so_hoa_don)', 'Số hóa đơn phải là duy nhất!')
    ]

    @api.depends('chi_tiet_ids', 'chi_tiet_ids.thanh_tien', 'ty_le_thue')
    def _compute_tong(self):
        for record in self:
            record.tong_tien_hang = sum(record.chi_tiet_ids.mapped('thanh_tien'))
            record.tien_thue = record.tong_tien_hang * record.ty_le_thue / 100
            record.tong_thanh_toan = record.tong_tien_hang + record.tien_thue

    @api.model
    def create(self, vals):
        if vals.get('so_hoa_don', 'New') == 'New':
            vals['so_hoa_don'] = self.env['ir.sequence'].next_by_code('ke_toan.hoa_don') or 'HD-00001'
        return super(HoaDon, self).create(vals)

    def action_xac_nhan(self):
        """Xác nhận hóa đơn"""
        for record in self:
            if record.trang_thai != 'nhap':
                raise UserError("Chỉ hóa đơn nháp mới có thể xác nhận!")
            if not record.chi_tiet_ids:
                raise UserError("Hóa đơn phải có ít nhất 1 dòng chi tiết!")
            
            # Tạo công nợ
            loai_cong_no = 'phai_thu' if record.loai_hoa_don == 'ban_hang' else 'phai_tra'
            cong_no = self.env['ke_toan.cong_no'].create({
                'loai_cong_no': loai_cong_no,
                'doi_tuong': record.khach_hang,
                'ngay_phat_sinh': record.ngay_lap,
                'so_tien_goc': record.tong_thanh_toan,
                'noi_dung': f'Hóa đơn {record.so_hoa_don}',
            })
            
            record.write({
                'trang_thai': 'da_xac_nhan',
                'cong_no_id': cong_no.id,
            })

    def action_thanh_toan(self):
        """Thanh toán hóa đơn"""
        for record in self:
            if record.trang_thai != 'da_xac_nhan':
                raise UserError("Chỉ hóa đơn đã xác nhận mới có thể thanh toán!")
            
            # Thanh toán công nợ
            if record.cong_no_id:
                self.env['ke_toan.cong_no.thanh_toan'].create({
                    'cong_no_id': record.cong_no_id.id,
                    'ngay_thanh_toan': fields.Date.today(),
                    'so_tien': record.cong_no_id.so_tien_con_lai,
                    'phuong_thuc': 'chuyen_khoan',
                })
            
            record.trang_thai = 'da_thanh_toan'

    def action_huy(self):
        """Hủy hóa đơn"""
        for record in self:
            if record.trang_thai == 'da_thanh_toan':
                raise UserError("Không thể hủy hóa đơn đã thanh toán!")
            record.trang_thai = 'huy'


class HoaDonChiTiet(models.Model):
    _name = 'ke_toan.hoa_don.chi_tiet'
    _description = 'Chi tiết hóa đơn'

    hoa_don_id = fields.Many2one(
        'ke_toan.hoa_don',
        string="Hóa đơn",
        required=True,
        ondelete='cascade'
    )

    ten_hang_hoa = fields.Char(
        "Tên hàng hóa/dịch vụ",
        required=True,
        help="Tên mặt hàng"
    )

    don_vi_tinh = fields.Char(
        "Đơn vị tính",
        default="Cái",
        help="Đơn vị tính (cái, chiếc, kg...)"
    )

    so_luong = fields.Float(
        "Số lượng",
        default=1,
        required=True,
        help="Số lượng"
    )

    don_gia = fields.Float(
        "Đơn giá",
        required=True,
        digits=(16, 2),
        help="Đơn giá chưa VAT"
    )

    thanh_tien = fields.Float(
        "Thành tiền",
        compute='_compute_thanh_tien',
        store=True,
        digits=(16, 2),
        help="Số lượng × Đơn giá"
    )

    ghi_chu = fields.Text("Ghi chú")

    @api.depends('so_luong', 'don_gia')
    def _compute_thanh_tien(self):
        for record in self:
            record.thanh_tien = record.so_luong * record.don_gia

    @api.constrains('so_luong')
    def _check_so_luong(self):
        for record in self:
            if record.so_luong <= 0:
                raise ValidationError("Số lượng phải lớn hơn 0!")

    @api.constrains('don_gia')
    def _check_don_gia(self):
        for record in self:
            if record.don_gia <= 0:
                raise ValidationError("Đơn giá phải lớn hơn 0!")
