# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re


class TaiKhoan(models.Model):
    """Danh mục tài khoản kế toán (theo chuẩn Việt Nam)"""
    _name = 'ke_toan.tai_khoan'
    _description = 'Danh mục tài khoản kế toán'
    _order = 'ma_tai_khoan'
    _rec_name = 'ten_day_du'
    
    ma_tai_khoan = fields.Char(
        'Mã tài khoản',
        required=True,
        size=10,
        help='Mã tài khoản theo quy định (VD: 211, 214, 627)'
    )
    
    ten_tai_khoan = fields.Char(
        'Tên tài khoản',
        required=True,
        help='Tên đầy đủ của tài khoản kế toán'
    )
    
    ten_day_du = fields.Char(
        'Tên đầy đủ',
        compute='_compute_ten_day_du',
        store=True
    )
    
    loai_tai_khoan = fields.Selection([
        ('tai_san', 'Tài sản'),
        ('nguon_von', 'Nguồn vốn'),
        ('chi_phi', 'Chi phí'),
        ('doanh_thu', 'Doanh thu'),
        ('thu_nhap', 'Thu nhập khác'),
        ('chi_phi_khac', 'Chi phí khác'),
    ], string='Loại tài khoản', required=True, default='tai_san')
    
    tai_khoan_cap_tren_id = fields.Many2one(
        'ke_toan.tai_khoan',
        'Tài khoản cấp trên',
        ondelete='restrict',
        help='Tài khoản tổng hợp (cấp 1)'
    )
    
    tai_khoan_cap_duoi_ids = fields.One2many(
        'ke_toan.tai_khoan',
        'tai_khoan_cap_tren_id',
        'Tài khoản cấp dưới'
    )
    
    cap_tai_khoan = fields.Integer(
        'Cấp tài khoản',
        compute='_compute_cap_tai_khoan',
        store=True,
        help='Cấp 1: Tổng hợp, Cấp 2: Chi tiết, Cấp 3: Chi tiết cấp 2'
    )
    
    tinh_chat = fields.Selection([
        ('no', 'Bên Nợ'),
        ('co', 'Bên Có'),
        ('no_co', 'Lưỡng tính'),
    ], string='Tính chất', default='no', required=True)
    
    mo_ta = fields.Text('Mô tả')
    
    active = fields.Boolean('Đang sử dụng', default=True)
    
    # Số dư tài khoản (quản lý nội bộ)
    so_du = fields.Float(
        'Số dư',
        digits=(16, 2),
        default=0.0,
        help='Số dư hiện tại của tài khoản'
    )
    
    _sql_constraints = [
        ('ma_tai_khoan_unique', 'unique(ma_tai_khoan)', 
         'Mã tài khoản phải là duy nhất!')
    ]
    
    @api.depends('ma_tai_khoan', 'ten_tai_khoan')
    def _compute_ten_day_du(self):
        for record in self:
            if record.ma_tai_khoan and record.ten_tai_khoan:
                record.ten_day_du = f"{record.ma_tai_khoan} - {record.ten_tai_khoan}"
            else:
                record.ten_day_du = record.ten_tai_khoan or record.ma_tai_khoan or ''
    
    @api.depends('ma_tai_khoan')
    def _compute_cap_tai_khoan(self):
        for record in self:
            if record.ma_tai_khoan:
                record.cap_tai_khoan = len(record.ma_tai_khoan)
            else:
                record.cap_tai_khoan = 0
    
    @api.constrains('ma_tai_khoan')
    def _check_ma_tai_khoan(self):
        for record in self:
            if record.ma_tai_khoan:
                # Chỉ cho phép số
                if not record.ma_tai_khoan.isdigit():
                    raise ValidationError('Mã tài khoản chỉ được chứa các chữ số!')
                
                # Kiểm tra độ dài (1-4 số)
                if len(record.ma_tai_khoan) > 4:
                    raise ValidationError('Mã tài khoản không được quá 4 chữ số!')
    
    @api.constrains('tai_khoan_cap_tren_id')
    def _check_tai_khoan_cap_tren(self):
        """Kiểm tra không tạo vòng lặp"""
        for record in self:
            if record.tai_khoan_cap_tren_id:
                parent = record.tai_khoan_cap_tren_id
                while parent:
                    if parent == record:
                        raise ValidationError('Không thể tạo vòng lặp trong cấu trúc tài khoản!')
                    parent = parent.tai_khoan_cap_tren_id
    
    def name_get(self):
        result = []
        for record in self:
            name = f"{record.ma_tai_khoan} - {record.ten_tai_khoan}"
            result.append((record.id, name))
        return result
    
    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('ma_tai_khoan', operator, name), ('ten_tai_khoan', operator, name)]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)
    
    def action_view_but_toan(self):
        """Xem bút toán liên quan đến tài khoản này"""
        self.ensure_one()
        return {
            'name': f'Bút toán TK {self.ma_tai_khoan}',
            'type': 'ir.actions.act_window',
            'res_model': 'ke_toan.but_toan_khau_hao',
            'view_mode': 'tree,form',
            'domain': ['|', ('tk_no_id', '=', self.id), ('tk_co_id', '=', self.id)],
            'context': {'default_tk_no_id': self.id},
        }
