from odoo import models, fields, api


class LoaiTaiSan(models.Model):
    _name = 'loai_tai_san'
    _description = 'Bảng chứa thông tin tài sản'
    _rec_name = "ten_loai_tai_san"
    _order = 'ma_loai_tai_san'
    _sql_constraints = [
        ('ma_loai_tai_san_unique', 'unique(ma_loai_tai_san)', 'Mã loại tài sản phải là duy nhất!')
    ]

    ma_loai_tai_san = fields.Char("Mã Loại Tài sản")
    ten_loai_tai_san = fields.Char("Tên Loại Tài sản", required=True)
    mo_ta = fields.Text("Mô tả")
    tai_san_ids = fields.One2many(
        comodel_name='tai_san',
        inverse_name='loai_tai_san_id', string="Tài sản", required=True)

    tong_so_luong = fields.Integer("Tổng số lượng", compute='_compute_thong_ke_trang_thai')
    luu_tru_count = fields.Integer("Số lượng Lưu trữ", compute='_compute_thong_ke_trang_thai')
    muon_count = fields.Integer("Số lượng Mượn", compute='_compute_thong_ke_trang_thai')
    bao_tri_count = fields.Integer("Số lượng Bảo trì", compute='_compute_thong_ke_trang_thai')
    hong_count = fields.Integer("Số lượng Hỏng", compute='_compute_thong_ke_trang_thai')

    @api.model
    def create(self, vals):
        if not vals.get('ma_loai_tai_san'):
            last_record = self.search([('ma_loai_tai_san', '=like', 'LTS-%')], order='ma_loai_tai_san desc', limit=1)
            if last_record:
                last_number = int(last_record.ma_loai_tai_san.split('-')[1])
                new_number = last_number + 1
            else:
                new_number = 1
            vals['ma_loai_tai_san'] = f'LTS-{new_number:05d}'
        return super(LoaiTaiSan, self).create(vals)

    @api.depends('tai_san_ids', 'tai_san_ids.trang_thai')
    def _compute_thong_ke_trang_thai(self):
        for record in self:
            tai_sans = record.tai_san_ids
            record.tong_so_luong = len(tai_sans)
            record.luu_tru_count = len(tai_sans.filtered(lambda t: t.trang_thai == 'LuuTru'))
            record.muon_count = len(tai_sans.filtered(lambda t: t.trang_thai == 'Muon'))
            record.bao_tri_count = len(tai_sans.filtered(lambda t: t.trang_thai == 'BaoTri'))
            record.hong_count = len(tai_sans.filtered(lambda t: t.trang_thai == 'Hong'))
