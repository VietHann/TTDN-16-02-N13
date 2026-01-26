import re

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class NhaCungCap(models.Model):
    _name = 'nha_cung_cap'
    _description = 'Bảng chứa thông tin tài sản'
    _rec_name = "ten_nha_cung_cap"
    _order = 'ma_nha_cung_cap'
    _sql_constraints = [
        ('ma_nha_cung_cap_unique', 'unique(ma_nha_cung_cap)', 'Mã nhà cung cấp phải là duy nhất!'),
    ]

    ma_nha_cung_cap = fields.Char("Mã nhà cung cấp")
    ten_nha_cung_cap = fields.Char("Tên nhà cung cấp", required=True)
    ten_nguoi_dai_dien = fields.Char("Tên người đại diện", required=True)
    so_dien_thoai = fields.Char("Số điện thoại", required=True)
    email = fields.Char("Email", required=True)
    tai_san_ids = fields.One2many(
        comodel_name='tai_san',
        inverse_name='nha_cung_cap_id', string="Tài sản", required=True)

    @api.constrains('ma_nha_cung_cap')
    def _check_ma_nha_cung_cap_format(self):
        for record in self:
            if not re.fullmatch(r'NCC-\d{5}', record.ma_nha_cung_cap):
                raise ValidationError("Mã nhà cung cấp phải có định dạng NCC-XXXXX (ví dụ: NCC-12345)")


    @api.model
    def create(self, vals):
        if vals.get('ma_nha_cung_cap', 'New') == 'New':
            last_record = self.search([], order='ma_nha_cung_cap desc', limit=1)
            if last_record and last_record.ma_nha_cung_cap.startswith('NCC-'):
                last_number = int(last_record.ma_nha_cung_cap.split('-')[1])
                new_number = last_number + 1
            else:
                new_number = 1
            vals['ma_nha_cung_cap'] = f'NCC-{new_number:05d}'
        return super(NhaCungCap, self).create(vals)
