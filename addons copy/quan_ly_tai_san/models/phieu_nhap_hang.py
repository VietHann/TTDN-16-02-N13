# -*- coding: utf-8 -*-
import re
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class PhieuNhapHang(models.Model):
    _name = 'phieu_nhap_hang'
    _description = 'Phiếu nhập hàng/mua hàng tài sản'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'ma_phieu'
    _order = 'ngay_nhap desc'

    ma_phieu = fields.Char(
        "Mã phiếu",
        required=True,
        copy=False,
        readonly=True,
        default="New",
        help="Mã phiếu nhập hàng tự động"
    )

    ngay_nhap = fields.Date(
        "Ngày nhập",
        default=fields.Date.today,
        required=True,
        tracking=True,
        help="Ngày thực hiện nhập hàng"
    )

    nha_cung_cap_id = fields.Many2one(
        'nha_cung_cap',
        string="Nhà cung cấp",
        required=True,
        tracking=True,
        help="Nhà cung cấp tài sản"
    )

    TRANG_THAI = [
        ('nhap', 'Nháp'),
        ('cho_duyet', 'Chờ duyệt'),
        ('da_duyet', 'Đã duyệt'),
        ('hoan_thanh', 'Hoàn thành'),
        ('huy', 'Hủy'),
    ]

    trang_thai = fields.Selection(
        TRANG_THAI,
        string="Trạng thái",
        default='nhap',
        required=True,
        tracking=True,
        help="Trạng thái phiếu nhập"
    )

    nguoi_lap_id = fields.Many2one(
        'nhan_vien',
        string="Người lập phiếu",
        required=True,
        help="Nhân viên lập phiếu nhập"
    )

    nguoi_duyet_id = fields.Many2one(
        'nhan_vien',
        string="Người duyệt",
        readonly=True,
        tracking=True,
        help="Người duyệt phiếu nhập"
    )

    ngay_duyet = fields.Datetime(
        "Ngày duyệt",
        readonly=True,
        tracking=True,
        help="Thời gian duyệt phiếu"
    )

    chi_tiet_ids = fields.One2many(
        'phieu_nhap_hang.chi_tiet',
        'phieu_nhap_id',
        string="Chi tiết nhập hàng",
        help="Danh sách tài sản nhập"
    )

    tong_so_luong = fields.Integer(
        "Tổng số lượng",
        compute='_compute_tong',
        store=True,
        help="Tổng số tài sản nhập"
    )

    tong_tien = fields.Float(
        "Tổng tiền",
        compute='_compute_tong',
        store=True,
        digits=(16, 2),
        help="Tổng giá trị đơn hàng"
    )

    ghi_chu = fields.Text("Ghi chú")

    _sql_constraints = [
        ('ma_phieu_unique', 'unique(ma_phieu)', 'Mã phiếu nhập phải là duy nhất!')
    ]

    @api.depends('chi_tiet_ids', 'chi_tiet_ids.so_luong', 'chi_tiet_ids.thanh_tien')
    def _compute_tong(self):
        for record in self:
            record.tong_so_luong = sum(record.chi_tiet_ids.mapped('so_luong'))
            record.tong_tien = sum(record.chi_tiet_ids.mapped('thanh_tien'))

    @api.model
    def create(self, vals):
        if vals.get('ma_phieu', 'New') == 'New':
            vals['ma_phieu'] = self.env['ir.sequence'].next_by_code('phieu_nhap_hang') or 'PN-00001'
        return super(PhieuNhapHang, self).create(vals)

    def action_gui_duyet(self):
        """Gửi phiếu để duyệt"""
        for record in self:
            if record.trang_thai != 'nhap':
                raise UserError("Chỉ phiếu nháp mới có thể gửi duyệt!")
            if not record.chi_tiet_ids:
                raise UserError("Phiếu nhập phải có ít nhất 1 tài sản!")
            record.trang_thai = 'cho_duyet'

    def action_duyet(self):
        """Duyệt phiếu nhập"""
        for record in self:
            if record.trang_thai != 'cho_duyet':
                raise UserError("Chỉ phiếu chờ duyệt mới có thể duyệt!")
            record.write({
                'trang_thai': 'da_duyet',
                'ngay_duyet': fields.Datetime.now(),
            })

    def action_nhap_kho(self):
        """Nhập kho - Tạo tài sản từ chi tiết"""
        for record in self:
            if record.trang_thai != 'da_duyet':
                raise UserError("Chỉ phiếu đã duyệt mới có thể nhập kho!")
            
            # Tạo tài sản từ chi tiết
            for chi_tiet in record.chi_tiet_ids:
                for i in range(chi_tiet.so_luong):
                    self.env['tai_san'].create({
                        'ten_tai_san': chi_tiet.ten_tai_san,
                        'loai_tai_san_id': chi_tiet.loai_tai_san_id.id,
                        'nha_cung_cap_id': record.nha_cung_cap_id.id,
                        'so_serial': f"{chi_tiet.so_serial_bat_dau}-{i+1:03d}",
                        'ngay_mua': record.ngay_nhap,
                        'gia_tien_mua': chi_tiet.don_gia,
                        'trang_thai': 'LuuTru',
                    })
            
            record.trang_thai = 'hoan_thanh'

    def action_huy(self):
        """Hủy phiếu"""
        for record in self:
            if record.trang_thai == 'hoan_thanh':
                raise UserError("Không thể hủy phiếu đã hoàn thành!")
            record.trang_thai = 'huy'

    def action_dat_lai(self):
        """Đặt lại về nháp"""
        for record in self:
            if record.trang_thai in ['hoan_thanh', 'huy']:
                raise UserError("Không thể đặt lại phiếu đã hoàn thành hoặc đã hủy!")
            record.trang_thai = 'nhap'


class PhieuNhapHangChiTiet(models.Model):
    _name = 'phieu_nhap_hang.chi_tiet'
    _description = 'Chi tiết phiếu nhập hàng'

    phieu_nhap_id = fields.Many2one(
        'phieu_nhap_hang',
        string="Phiếu nhập",
        required=True,
        ondelete='cascade'
    )

    loai_tai_san_id = fields.Many2one(
        'loai_tai_san',
        string="Loại tài sản",
        required=True,
        help="Loại tài sản cần nhập"
    )

    ten_tai_san = fields.Char(
        "Tên tài sản",
        required=True,
        help="Tên cụ thể của tài sản"
    )

    so_serial_bat_dau = fields.Char(
        "Serial bắt đầu",
        required=True,
        help="Serial sẽ tự động tăng theo số lượng"
    )

    so_luong = fields.Integer(
        "Số lượng",
        default=1,
        required=True,
        help="Số lượng tài sản nhập"
    )

    don_gia = fields.Float(
        "Đơn giá",
        required=True,
        digits=(16, 2),
        help="Giá mua mỗi đơn vị"
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
