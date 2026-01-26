from odoo import models, fields, api
from datetime import date

from odoo.exceptions import ValidationError

class VanBanDen(models.Model):
    _name = 'van_ban_den'
    _description = 'Bảng chứa thông tin văn bản đến'
    _rec_name = 'ten_van_ban'

    so_van_ban_den = fields.Char("Số hiệu văn bản", required=True)
    ten_van_ban = fields.Char("Tên văn bản", required=True)
    so_hieu_van_ban = fields.Char("Số hiệu văn bản", required=True)
    noi_gui_den = fields.Char("Nơi gửi đến")

