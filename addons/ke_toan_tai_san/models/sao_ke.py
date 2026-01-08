# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SaoKe(models.Model):
    _name = 'ke_toan.sao_ke'
    _description = 'Sao kê tài khoản'
    _rec_name = 'ten_sao_ke'
    _order = 'ngay_tao desc'

    ten_sao_ke = fields.Char(
        "Tên sao kê",
        required=True,
        help="Tên báo cáo sao kê"
    )

    tai_khoan_id = fields.Many2one(
        'ke_toan.tai_khoan',
        string="Tài khoản",
        required=True,
        help="Tài khoản cần sao kê"
    )

    ngay_bat_dau = fields.Date(
        "Từ ngày",
        required=True,
        default=lambda self: fields.Date.today().replace(day=1),
        help="Ngày bắt đầu kỳ sao kê"
    )

    ngay_ket_thuc = fields.Date(
        "Đến ngày",
        required=True,
        default=fields.Date.today,
        help="Ngày kết thúc kỳ sao kê"
    )

    don_vi_id = fields.Many2one(
        'don_vi',
        string="Đơn vị",
        help="Lọc theo đơn vị (tùy chọn)"
    )

    so_du_dau_ky_no = fields.Float(
        "Số dư đầu kỳ Nợ",
        digits=(16, 2),
        help="Số dư nợ đầu kỳ"
    )

    so_du_dau_ky_co = fields.Float(
        "Số dư đầu kỳ Có",
        digits=(16, 2),
        help="Số dư có đầu kỳ"
    )

    tong_phat_sinh_no = fields.Float(
        "Tổng phát sinh Nợ",
        compute='_compute_tong',
        store=True,
        digits=(16, 2),
        help="Tổng số phát sinh bên Nợ"
    )

    tong_phat_sinh_co = fields.Float(
        "Tổng phát sinh Có",
        compute='_compute_tong',
        store=True,
        digits=(16, 2),
        help="Tổng số phát sinh bên Có"
    )

    so_du_cuoi_ky_no = fields.Float(
        "Số dư cuối kỳ Nợ",
        compute='_compute_tong',
        store=True,
        digits=(16, 2),
        help="Số dư nợ cuối kỳ"
    )

    so_du_cuoi_ky_co = fields.Float(
        "Số dư cuối kỳ Có",
        compute='_compute_tong',
        store=True,
        digits=(16, 2),
        help="Số dư có cuối kỳ"
    )

    chi_tiet_ids = fields.One2many(
        'ke_toan.sao_ke.chi_tiet',
        'sao_ke_id',
        string="Chi tiết giao dịch",
        help="Các giao dịch trong kỳ"
    )

    ngay_tao = fields.Datetime(
        "Ngày tạo",
        default=fields.Datetime.now,
        readonly=True,
        help="Thời điểm tạo sao kê"
    )

    nguoi_tao_id = fields.Many2one(
        'nhan_vien',
        string="Người tạo",
        readonly=True,
        help="Người tạo báo cáo"
    )

    ghi_chu = fields.Text("Ghi chú")

    @api.constrains('ngay_bat_dau', 'ngay_ket_thuc')
    def _check_dates(self):
        for record in self:
            if record.ngay_ket_thuc < record.ngay_bat_dau:
                raise ValidationError("Ngày kết thúc phải sau ngày bắt đầu!")

    @api.depends('chi_tiet_ids', 'chi_tiet_ids.so_tien_no', 'chi_tiet_ids.so_tien_co',
                 'so_du_dau_ky_no', 'so_du_dau_ky_co')
    def _compute_tong(self):
        for record in self:
            record.tong_phat_sinh_no = sum(record.chi_tiet_ids.mapped('so_tien_no'))
            record.tong_phat_sinh_co = sum(record.chi_tiet_ids.mapped('so_tien_co'))
            
            # Tính số dư cuối kỳ
            so_du_no = record.so_du_dau_ky_no + record.tong_phat_sinh_no
            so_du_co = record.so_du_dau_ky_co + record.tong_phat_sinh_co
            
            if so_du_no > so_du_co:
                record.so_du_cuoi_ky_no = so_du_no - so_du_co
                record.so_du_cuoi_ky_co = 0
            else:
                record.so_du_cuoi_ky_no = 0
                record.so_du_cuoi_ky_co = so_du_co - so_du_no

    def action_lay_du_lieu(self):
        """Lấy dữ liệu giao dịch từ bút toán"""
        self.ensure_one()
        
        # Xóa chi tiết cũ
        self.chi_tiet_ids.unlink()
        
        # Tìm các bút toán khấu hao
        domain = [
            ('ngay_ghi_nhan', '>=', self.ngay_bat_dau),
            ('ngay_ghi_nhan', '<=', self.ngay_ket_thuc),
            ('state', '=', 'posted'),
        ]
        
        if self.don_vi_id:
            domain.append(('don_vi_id', '=', self.don_vi_id.id))
        
        # Lấy bút toán khấu hao
        but_toans = self.env['ke_toan.but_toan_khau_hao'].search(domain)
        
        chi_tiet_vals = []
        for bt in but_toans:
            # Kiểm tra tài khoản liên quan
            if bt.tk_no_id.id == self.tai_khoan_id.id:
                chi_tiet_vals.append({
                    'sao_ke_id': self.id,
                    'ngay_giao_dich': bt.ngay_ghi_nhan,
                    'dien_giai': bt.dien_giai,
                    'so_tien_no': bt.so_tien,
                    'so_tien_co': 0,
                })
            elif bt.tk_co_id.id == self.tai_khoan_id.id:
                chi_tiet_vals.append({
                    'sao_ke_id': self.id,
                    'ngay_giao_dich': bt.ngay_ghi_nhan,
                    'dien_giai': bt.dien_giai,
                    'so_tien_no': 0,
                    'so_tien_co': bt.so_tien,
                })
        
        # Tạo chi tiết
        if chi_tiet_vals:
            self.env['ke_toan.sao_ke.chi_tiet'].create(chi_tiet_vals)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Thành công',
                'message': f'Đã lấy {len(chi_tiet_vals)} giao dịch',
                'type': 'success',
                'sticky': False,
            }
        }


class SaoKeChiTiet(models.Model):
    _name = 'ke_toan.sao_ke.chi_tiet'
    _description = 'Chi tiết sao kê'
    _order = 'ngay_giao_dich, id'

    sao_ke_id = fields.Many2one(
        'ke_toan.sao_ke',
        string="Sao kê",
        required=True,
        ondelete='cascade'
    )

    ngay_giao_dich = fields.Date(
        "Ngày giao dịch",
        required=True,
        help="Ngày phát sinh"
    )

    dien_giai = fields.Char(
        "Diễn giải",
        required=True,
        help="Nội dung giao dịch"
    )

    so_tien_no = fields.Float(
        "Nợ",
        digits=(16, 2),
        help="Số tiền bên Nợ"
    )

    so_tien_co = fields.Float(
        "Có",
        digits=(16, 2),
        help="Số tiền bên Có"
    )

    so_du_no = fields.Float(
        "Số dư Nợ",
        digits=(16, 2),
        help="Số dư nợ sau giao dịch"
    )

    so_du_co = fields.Float(
        "Số dư Có",
        digits=(16, 2),
        help="Số dư có sau giao dịch"
    )
