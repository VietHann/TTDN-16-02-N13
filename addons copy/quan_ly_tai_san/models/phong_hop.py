# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PhongHop(models.Model):
    _name = 'phong_hop'
    _description = 'Quản lý phòng họp'
    _rec_name = 'ten_phong'
    _order = 'ma_phong'

    ma_phong = fields.Char(
        "Mã phòng",
        required=True,
        copy=False,
        help="Mã định danh phòng họp"
    )

    ten_phong = fields.Char(
        "Tên phòng",
        required=True,
        help="Tên phòng họp"
    )

    vi_tri_id = fields.Many2one(
        'vi_tri',
        string="Vị trí",
        required=True,
        help="Vị trí của phòng họp"
    )

    suc_chua = fields.Integer(
        "Sức chứa",
        default=10,
        help="Số người tối đa"
    )

    dien_tich = fields.Float(
        "Diện tích (m²)",
        digits=(10, 2),
        help="Diện tích phòng họp"
    )

    TRANG_THAI = [
        ('san_sang', 'Sẵn sàng'),
        ('dang_su_dung', 'Đang sử dụng'),
        ('bao_tri', 'Bảo trì'),
        ('khong_kha_dung', 'Không khả dụng'),
    ]

    trang_thai = fields.Selection(
        TRANG_THAI,
        string="Trạng thái",
        default='san_sang',
        required=True,
        help="Trạng thái hiện tại của phòng"
    )

    thiet_bi_ids = fields.Many2many(
        'tai_san',
        'phong_hop_tai_san_rel',
        'phong_hop_id',
        'tai_san_id',
        string="Thiết bị trong phòng",
        domain=[('trang_thai', '=', 'LuuTru')],
        help="Các thiết bị gắn liền với phòng họp"
    )

    dat_phong_ids = fields.One2many(
        'dat_phong',
        'phong_hop_id',
        string="Lịch đặt phòng",
        help="Lịch sử đặt phòng"
    )

    bao_tri_ids = fields.One2many(
        'bao_tri_phong_hop',
        'phong_hop_id',
        string="Lịch sử bảo trì",
        help="Các lần bảo trì phòng"
    )

    nang_cap_ids = fields.One2many(
        'nang_cap_phong_hop',
        'phong_hop_id',
        string="Lịch sử nâng cấp",
        help="Các lần nâng cấp phòng"
    )

    mo_ta = fields.Text("Mô tả")
    hinh_anh = fields.Binary("Hình ảnh", attachment=True)

    _sql_constraints = [
        ('ma_phong_unique', 'unique(ma_phong)', 'Mã phòng phải là duy nhất!')
    ]

    @api.constrains('suc_chua')
    def _check_suc_chua(self):
        for record in self:
            if record.suc_chua <= 0:
                raise ValidationError("Sức chứa phải lớn hơn 0!")

    @api.constrains('dien_tich')
    def _check_dien_tich(self):
        for record in self:
            if record.dien_tich and record.dien_tich <= 0:
                raise ValidationError("Diện tích phải lớn hơn 0!")

    def action_bao_tri(self):
        """Chuyển trạng thái sang bảo trì"""
        return {
            'name': 'Bảo trì phòng họp',
            'type': 'ir.actions.act_window',
            'res_model': 'bao_tri_phong_hop',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_phong_hop_id': self.id,
                'default_ngay_bat_dau': fields.Date.today(),
            },
        }

    def action_nang_cap(self):
        """Nâng cấp phòng họp"""
        return {
            'name': 'Nâng cấp phòng họp',
            'type': 'ir.actions.act_window',
            'res_model': 'nang_cap_phong_hop',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_phong_hop_id': self.id,
                'default_ngay_nang_cap': fields.Date.today(),
            },
        }

    def action_xem_lich_dat_phong(self):
        """Xem lịch đặt phòng"""
        return {
            'name': f'Lịch đặt - {self.ten_phong}',
            'type': 'ir.actions.act_window',
            'res_model': 'dat_phong',
            'view_mode': 'calendar,tree,form',
            'domain': [('phong_hop_id', '=', self.id)],
            'context': {'default_phong_hop_id': self.id},
        }
