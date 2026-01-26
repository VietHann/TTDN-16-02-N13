from odoo import models, fields, api


class ChungChiBangCap(models.Model):
    _name = 'chung_chi_bang_cap'
    _description = 'Bảng chứa thông tin chứng chỉ bằng cấp'
    _rec_name = 'ten_chung_chi_bang_cap'

    ma_chung_chi_bang_cap = fields.Char("Mã chức chỉ, bằng cấp", required=True)
    ten_chung_chi_bang_cap = fields.Char("Tên chức chỉ, bằng cấp", required=True)