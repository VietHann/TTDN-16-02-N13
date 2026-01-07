import re
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class KhauHao(models.Model):
    _name = 'khau_hao'
    _description = 'Bảng chứa thông tin khấu hao tài sản'
    _order = 'ngay_khau_hao desc'

    ma_khau_hao = fields.Char(
        "Mã khấu hao",
        copy=False,
        readonly=True,
        default="New"
    )
    phuong_phap_khau_hao = fields.Selection(
        [
            ('duong_thang', 'Khấu hao đường thẳng'),
            ('so_du_giam_dan', 'Khấu hao số dư giảm dần')
        ],
        string="Phương pháp khấu hao",
        required=True
    )
    ngay_khau_hao = fields.Date("Ngày khấu hao", required=True, default=fields.Date.context_today)
    gia_tri_khau_hao = fields.Integer("Giá trị khấu hao", compute="_compute_gia_tri_khau_hao", store=True)
    gia_tri_con_lai = fields.Integer("Giá trị còn lại", compute="_compute_gia_tri_con_lai", store=True)
    ghi_chu = fields.Char("Ghi chú")
    tai_san_id = fields.Many2one(
        comodel_name="tai_san",
        string="Tài sản",
        required=True,
        ondelete="cascade"
    )

    @api.depends('tai_san_id', 'tai_san_id.gia_tien_mua', 'tai_san_id.gia_tri_hien_tai', 'phuong_phap_khau_hao')
    def _compute_gia_tri_khau_hao(self):
        for record in self:
            if not record.tai_san_id or not record.tai_san_id.gia_tien_mua:
                record.gia_tri_khau_hao = 0
                continue

            gia_tri_hien_tai = record.tai_san_id.gia_tri_hien_tai
            gia_tien_mua = record.tai_san_id.gia_tien_mua
            so_nam_khau_hao = 1
            tile_khau_hao = 0.05

            if record.phuong_phap_khau_hao == 'duong_thang':

                record.gia_tri_khau_hao = max(0, gia_tien_mua / so_nam_khau_hao)
            elif record.phuong_phap_khau_hao == 'so_du_giam_dan':

                record.gia_tri_khau_hao = max(0, gia_tri_hien_tai * tile_khau_hao)

    @api.depends('tai_san_id', 'tai_san_id.gia_tri_hien_tai', 'gia_tri_khau_hao')
    def _compute_gia_tri_con_lai(self):
        for record in self:
            if record.tai_san_id:
                record.gia_tri_con_lai = max(0, record.tai_san_id.gia_tri_hien_tai - record.gia_tri_khau_hao)

    @api.model
    def create(self, vals):
        if vals.get('ma_khau_hao', 'New') == 'New':
            last_record = self.search([], order='ma_khau_hao desc', limit=1)
            if last_record and last_record.ma_khau_hao.startswith('KH-'):
                try:
                    last_number = int(last_record.ma_khau_hao.split('-')[1])
                    new_number = last_number + 1
                except (ValueError, IndexError):
                    new_number = 1
            else:
                new_number = 1
            vals['ma_khau_hao'] = f'KH-{new_number:05d}'

        record = super(KhauHao, self).create(vals)

        if record.tai_san_id:
            record.tai_san_id.sudo().write({'gia_tri_hien_tai': record.gia_tri_con_lai})

        return record
