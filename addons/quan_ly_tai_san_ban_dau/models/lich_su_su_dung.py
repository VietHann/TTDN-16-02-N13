import re
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class LichSuSuDung(models.Model):
    _name = 'lich_su_su_dung'
    _description = 'Bảng chứa thông tin lịch sử sử dụng'
    _order = 'ma_lich_su_su_dung'
    _sql_constraints = [
        ('ma_lich_su_su_dung_unique', 'unique(ma_lich_su_su_dung)', 'Mã lịch sử sử dụng phải là duy nhất!'),
    ]

    ma_lich_su_su_dung = fields.Char("Mã lịch sử sử dụng",  copy=False, readonly=True, default="New")
    ngay_muon = fields.Datetime("Thời gian mượn", required=True)
    ngay_tra = fields.Datetime("Thời gian trả", required=True)
    ghi_chu = fields.Char("Ghi chú")
    nhan_vien_id = fields.Many2one(comodel_name="nhan_vien", string="Nhân sự", store=True)
    tai_san_id = fields.Many2one(comodel_name="tai_san", string="Tài sản", store=True)

    @api.constrains('ma_lich_su_su_dung')
    def _check_ma_lich_su_su_dung_format(self):
        for record in self:
            if not re.fullmatch(r'LS-\d{4}', record.ma_lich_su_su_dung):
                raise ValidationError("Mã phải có định dạng LS-XXXXX (ví dụ: LS-12345)")

    @api.model
    def create(self, vals):
        if vals.get('ma_lich_su_su_dung', 'New') == 'New':
            last_record = self.search([], order='ma_lich_su_su_dung desc', limit=1)
            if last_record and last_record.ma_lich_su_su_dung.startswith('LS-'):
                last_number = int(last_record.ma_lich_su_su_dung.split('-')[1])
                new_number = last_number + 1
            else:
                new_number = 1
            vals['ma_lich_su_su_dung'] = f'LS-{new_number:05d}'
        return super(LichSuSuDung, self).create(vals)
