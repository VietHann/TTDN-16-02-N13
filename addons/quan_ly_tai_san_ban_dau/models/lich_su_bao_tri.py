import re
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class LichSuBaoTri(models.Model):
    _name = 'lich_su_bao_tri'
    _description = 'Bảng chứa thông tin lịch sử bảo trì'
    _order = 'ngay_bao_tri desc'

    ma_lich_su_bao_tri = fields.Char(
        "Mã lịch sử bảo trì",
        copy=False,
        readonly=True,
        default="New"
    )

    ngay_bao_tri = fields.Date("Thời gian bảo trì", required=True)
    ngay_tra = fields.Date("Thời gian trả", required=True)
    chi_phi = fields.Integer("Chi phí", required=True, default=0)
    ghi_chu = fields.Char("Ghi chú")
    tai_san_id = fields.Many2one(
        comodel_name="tai_san",
        string="Tài sản",
        required=True,
        ondelete="cascade"
    )

    @api.constrains('ngay_bao_tri', 'ngay_tra')
    def _check_valid_dates(self):
        for record in self:
            if record.ngay_bao_tri > record.ngay_tra:
                raise ValidationError("Ngày bảo trì không thể lớn hơn ngày trả!")

    @api.constrains('chi_phi')
    def _check_valid_cost(self):
        for record in self:
            if record.chi_phi < 0:
                raise ValidationError("Chi phí bảo trì không thể là số âm!")

    @api.model
    def create(self, vals):
        if vals.get('ma_lich_su_bao_tri', 'New') == 'New':
            last_record = self.search([], order='ma_lich_su_bao_tri desc', limit=1)
            if last_record and last_record.ma_lich_su_bao_tri.startswith('LSBT-'):
                last_number = int(last_record.ma_lich_su_bao_tri.split('-')[1])
                new_number = last_number + 1
            else:
                new_number = 1
            vals['ma_lich_su_bao_tri'] = f'LSBT-{new_number:05d}'

        return super(LichSuBaoTri, self).create(vals)
