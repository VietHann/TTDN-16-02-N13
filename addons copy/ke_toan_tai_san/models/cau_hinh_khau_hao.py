# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class CauHinhKhauHao(models.Model):
    """Cấu hình khấu hao theo loại tài sản"""
    _name = 'ke_toan.cau_hinh_khau_hao'
    _description = 'Cấu hình khấu hao theo loại tài sản'
    _rec_name = 'loai_tai_san_id'
    
    loai_tai_san_id = fields.Many2one(
        'loai_tai_san',
        'Loại tài sản',
        required=True,
        ondelete='cascade',
        help='Loại tài sản áp dụng cấu hình này'
    )
    
    phuong_phap_mac_dinh = fields.Selection([
        ('duong_thang', 'Đường thẳng'),
        ('so_du_giam_dan', 'Số dư giảm dần'),
    ], string='Phương pháp mặc định', default='duong_thang', required=True)
    
    thoi_gian_mac_dinh = fields.Integer(
        'Thời gian khấu hao (tháng)',
        default=60,
        required=True,
        help='Thời gian khấu hao mặc định (60 tháng = 5 năm)'
    )
    
    ty_le_khau_hao_nam = fields.Float(
        'Tỷ lệ khấu hao (%/năm)',
        default=20.0,
        help='Tỷ lệ % khấu hao hàng năm (dùng cho phương pháp số dư giảm dần)'
    )
    
    ty_le_khau_hao_thang = fields.Float(
        'Tỷ lệ khấu hao (%/tháng)',
        compute='_compute_ty_le_thang',
        store=True,
        help='Tự động tính = Tỷ lệ năm / 12'
    )
    
    tk_chi_phi_id = fields.Many2one(
        'ke_toan.tai_khoan',
        'TK Chi phí mặc định',
        domain=[('loai_tai_khoan', '=', 'chi_phi')],
        help='TK 627 hoặc 642'
    )
    
    don_vi_ap_dung_id = fields.Many2one(
        'don_vi',
        'Đơn vị áp dụng',
        help='Đơn vị/Phòng ban áp dụng cấu hình này'
    )
    
    gia_tri_thanh_ly_mac_dinh = fields.Float(
        'Giá trị thanh lý mặc định',
        default=0,
        digits=(16, 2),
        help='Giá trị thanh lý dự kiến mặc định'
    )
    
    mo_ta = fields.Text('Mô tả')
    
    active = fields.Boolean('Đang sử dụng', default=True)
    
    _sql_constraints = [
        ('loai_tai_san_unique', 'unique(loai_tai_san_id)', 
         'Mỗi loại tài sản chỉ có 1 cấu hình!')
    ]
    
    @api.depends('ty_le_khau_hao_nam')
    def _compute_ty_le_thang(self):
        for record in self:
            record.ty_le_khau_hao_thang = record.ty_le_khau_hao_nam / 12
    
    @api.constrains('thoi_gian_mac_dinh')
    def _check_thoi_gian(self):
        for record in self:
            if record.thoi_gian_mac_dinh <= 0:
                raise ValidationError('Thời gian khấu hao phải lớn hơn 0!')
    
    @api.constrains('ty_le_khau_hao_nam')
    def _check_ty_le(self):
        for record in self:
            if not (0 < record.ty_le_khau_hao_nam <= 100):
                raise ValidationError('Tỷ lệ khấu hao phải trong khoảng 0-100%!')
    
    def name_get(self):
        result = []
        for record in self:
            name = f"Cấu hình: {record.loai_tai_san_id.ten_loai_tai_san}"
            result.append((record.id, name))
        return result
