from odoo import models, fields, api

class LichSuKiemKe(models.Model):
    _name = 'lich_su_kiem_ke'
    _description = 'Lịch sử kiểm kê tài sản'
    _order = 'ngay_kiem_ke desc'
    _sql_constraints = [
        ('ma_lich_su_kiem_ke_unique', 'unique(ma_lich_su_kiem_ke)', 'Mã lịch sử kiểm kê phải là duy nhất!'),
    ]

    ma_lich_su_kiem_ke = fields.Char(
        string="Mã lịch sử kiểm kê",
        copy=False,
        readonly=True,
        default="New"
    )
    ngay_kiem_ke = fields.Date(
        string="Ngày kiểm kê",
        required=True,
        default=fields.Date.context_today
    )
    phieu_kiem_ke_id = fields.Many2one(
        comodel_name="phieu_kiem_ke",
        string="Phiếu kiểm kê",
        required=True,
        ondelete="cascade"
    )
    tai_san_id = fields.Many2one(
        comodel_name="tai_san",
        string="Tài sản",
        required=True,
        ondelete="cascade"
    )
    trang_thai_truoc = fields.Selection(
        selection=[
            ('binh_thuong', 'Bình thường'),
            ('hong_hoc', 'Hỏng hóc'),
            ('mat', 'Mất'),
            ('sua_chua', 'Đang sửa chữa')
        ],
        string="Trạng thái trước",
        required=True
    )
    trang_thai_sau = fields.Selection(
        selection=[
            ('binh_thuong', 'Bình thường'),
            ('hong_hoc', 'Hỏng hóc'),
            ('mat', 'Mất'),
            ('sua_chua', 'Đang sửa chữa')
        ],
        string="Trạng thái sau",
        required=True
    )
    ghi_chu = fields.Text(string="Ghi chú")

    @api.model
    def create(self, vals):
        if vals.get('ma_lich_su_kiem_ke', 'New') == 'New':
            last_record = self.search([], order='ma_lich_su_kiem_ke desc', limit=1)
            if last_record and last_record.ma_lich_su_kiem_ke.startswith('LSKK-'):
                last_number = int(last_record.ma_lich_su_kiem_ke.split('-')[1])
                new_number = last_number + 1
            else:
                new_number = 1
            vals['ma_lich_su_kiem_ke'] = f'LSKK-{new_number:05d}'
        return super(LichSuKiemKe, self).create(vals)