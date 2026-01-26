from odoo import models, fields, api
from datetime import date

from odoo.exceptions import ValidationError

class LoaiVanBan(models.Model):
    _name = 'loai_van_ban'
    _description = 'Bảng chứa thông tin loại văn bản'
    _rec_name = 'ten_loai_van_ban'

    ma_loai_van_ban = fields.Char("Số hiệu văn bản", required=True)
    ten_loai_van_ban = fields.Char("Tên văn bản", required=True)

