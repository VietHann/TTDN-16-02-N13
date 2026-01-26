from odoo import models, fields, api
from datetime import date

from odoo.exceptions import ValidationError

class VanBanDi(models.Model):
    _name = 'van_ban_di'
    _description = 'Bảng chứa thông tin văn bản đi'
    _rec_name = 'ten_van_ban'

    so_van_ban_di = fields.Char("Số hiệu văn bản", required=True)
    ten_van_ban = fields.Char("Tên văn bản", required=True)
    so_hieu_van_ban = fields.Char("Số hiệu văn bản", required=True)
    noi_nhan = fields.Char("Nơi nhận")

