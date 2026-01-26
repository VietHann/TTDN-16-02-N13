from odoo import models, fields, api

class LichSuDiChuyen(models.Model):
    _name = 'lich_su_di_chuyen'
    _description = 'Lịch sử điều chuyển tài sản'
    _order = 'ngay_di_chuyen desc'

    tai_san_id = fields.Many2one(
        comodel_name='tai_san',
        string="Tài sản",
        required=True,
        ondelete='cascade'
    )

    vi_tri_chuyen_id = fields.Many2one(
        comodel_name='vi_tri',
        string="Ví trí chuyển",
        required=True,
    )

    vi_tri_den_id = fields.Many2one(
        comodel_name='vi_tri',
        string="Vị trí đến",
        required=True
    )
    ngay_di_chuyen = fields.Datetime(
        "Thời gian điều chuyển",
        default=fields.Date.context_today,
        required=True
    )
    ghi_chu = fields.Char("Ghi chú")

    is_current_location = fields.Boolean(
        string="Vị trí hiện tại",
        compute="_compute_is_current_location",
        store=True
    )

    @api.depends('tai_san_id.vi_tri_hien_tai_id', 'vi_tri_den_id')
    def _compute_is_current_location(self):
        for record in self:
            record.is_current_location = record.vi_tri_den_id == record.tai_san_id.vi_tri_hien_tai_id

    @api.model
    def create(self, vals):
        tai_san = self.env['tai_san'].browse(vals['tai_san_id'])
        tai_san.write({'vi_tri_hien_tai_id': vals['vi_tri_den_id']})
        return super(LichSuDiChuyen, self).create(vals)
