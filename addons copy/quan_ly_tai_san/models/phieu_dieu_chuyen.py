from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class PhieuDieuChuyen(models.Model):
    _name = 'phieu_dieu_chuyen'
    _description = 'Phiếu Điều Chuyển Tài Sản'
    _order = 'ten_phieu desc'

    _states = {
        'draft': 'Nháp',
        'approved': 'Đã duyệt',
        'done': 'Hoàn thành',
        'cancelled': 'Hủy',
    }


    ten_phieu = fields.Char(string='Tên phiếu', required=True, copy=False, readonly=True, default="Mới")
    tai_san = fields.Many2one('tai_san', string='Tài sản', required=True)
    vi_tri_hien_tai = fields.Many2one(
        'vi_tri',
        string='Vị trí hiện tại',
        related='tai_san.vi_tri_hien_tai_id',
        readonly=True
    )
    vi_tri_moi = fields.Many2one('vi_tri', string='Vị trí mới', required=True)
    ngay_dieu_chuyen = fields.Datetime(string='Ngày điều chuyển', required=True, default=fields.Date.context_today)
    trang_thai = fields.Selection([
        ('nhap', 'Nháp'),
        ('duyet', 'Duyệt'),
        ('hoan_thanh', 'Hoàn thành'),
        ('huy', 'Hủy')
    ], string='Trạng thái', default='nhap')
    ghi_chu = fields.Text(string='Ghi chú')

    @api.model
    def create(self, vals):
        if vals.get('ten_phieu', 'Mới') == 'Mới':
            last_record = self.search([], order='ten_phieu desc', limit=1)
            if last_record and last_record.ten_phieu.startswith('PDC-'):
                last_number = int(last_record.ten_phieu.split('-')[1])
                new_number = last_number + 1
            else:
                new_number = 1
            vals['ten_phieu'] = f'PDC-{new_number:05d}'
        return super(PhieuDieuChuyen, self).create(vals)

    def action_duyet(self):
        self.write({'trang_thai': 'duyet'})

    def action_hoan_thanh(self):
        if self.trang_thai != 'duyet':
            raise UserError(_('Chỉ có thể hoàn thành phiếu đã được duyệt.'))
        self.env['lich_su_di_chuyen'].create({
            'tai_san_id': self.tai_san.id,
            'vi_tri_chuyen_id': self.vi_tri_hien_tai.id,
            'vi_tri_den_id': self.vi_tri_moi.id,
            'ngay_di_chuyen': self.ngay_dieu_chuyen,
            'ghi_chu': self.ghi_chu,
        })
        self.tai_san.write({'vi_tri_hien_tai_id': self.vi_tri_moi.id})
        self.write({'trang_thai': 'hoan_thanh'})

    def action_huy(self):
        if self.trang_thai == 'hoan_thanh':
            raise UserError(_('Không thể hủy phiếu đã hoàn thành.'))
        self.write({'trang_thai': 'huy'})

    @api.constrains('vi_tri_moi')
    def _check_vi_tri(self):
        for record in self:
            if record.vi_tri_moi == record.vi_tri_hien_tai:
                raise ValidationError(_('Vị trí mới phải khác vị trí hiện tại.'))
