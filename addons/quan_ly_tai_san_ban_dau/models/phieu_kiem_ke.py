from odoo import models, fields, api

class PhieuKiemKe(models.Model):
    _name = 'phieu_kiem_ke'
    _description = 'Phiếu kiểm kê tài sản'
    _order = 'ngay_kiem_ke desc'
    _sql_constraints = [
        ('ma_phieu_kiem_ke_unique', 'unique(ma_phieu_kiem_ke)', 'Mã phiếu kiểm kê phải là duy nhất!'),
    ]

    ma_phieu_kiem_ke = fields.Char(
        string="Mã phiếu kiểm kê",
        copy=False,
        readonly=True,
        default="New"
    )
    ngay_kiem_ke = fields.Date(
        string="Ngày kiểm kê",
        required=True,
        default=fields.Date.context_today
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Nháp'),
            ('confirmed', 'Đã xác nhận'),
            ('done', 'Hoàn thành'),
        ],
        string="Trạng thái",
        default='draft',
        required=True,
        copy=False
    )
    ghi_chu = fields.Text(string="Ghi chú")

    tai_san_ids = fields.Many2many(
        comodel_name="tai_san",
        relation="tai_san_phieu_kiem_ke_rel",
        column1="phieu_kiem_ke_id",
        column2="tai_san_id",
        string="Danh sách tài sản",
        required=True
    )

    trang_thai_thuc_te = fields.Selection(
        selection=[
            ('binh_thuong', 'Bình thường'),
            ('hong_hoc', 'Hỏng hóc'),
            ('mat', 'Mất'),
            ('sua_chua', 'Đang sửa chữa')
        ],
        string="Trạng thái thực tế",
        required=True
    )

    @api.model
    def create(self, vals):
        if vals.get('ma_phieu_kiem_ke', 'New') == 'New':
            last_record = self.search([], order='ma_phieu_kiem_ke desc', limit=1)
            if last_record and last_record.ma_phieu_kiem_ke.startswith('PKK-'):
                last_number = int(last_record.ma_phieu_kiem_ke.split('-')[1])
                new_number = last_number + 1
            else:
                new_number = 1
            vals['ma_phieu_kiem_ke'] = f'PKK-{new_number:05d}'
        return super(PhieuKiemKe, self).create(vals)

    def action_confirm(self):
        self.ensure_one()
        if self.state == 'draft':
            self.state = 'confirmed'
        else:
            raise models.UserError('Chỉ có thể xác nhận phiếu ở trạng thái Nháp!')

    def action_done(self):
        self.ensure_one()
        if self.state != 'confirmed':
            raise models.UserError('Phiếu cần được xác nhận trước khi hoàn thành!')
        for tai_san in self.tai_san_ids:
            self.env['lich_su_kiem_ke'].create({
                'phieu_kiem_ke_id': self.id,
                'tai_san_id': tai_san.id,
                'trang_thai_truoc': tai_san.trang_thai_kiem_ke,
                'trang_thai_sau': self.trang_thai_thuc_te,
                'ngay_kiem_ke': self.ngay_kiem_ke,
            })
            tai_san.trang_thai_kiem_ke = self.trang_thai_thuc_te
        self.state = 'done'