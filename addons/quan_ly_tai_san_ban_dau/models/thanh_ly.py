from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ThanhLy(models.Model):
    _name = 'thanh_ly'
    _description = 'Quản lý thanh lý tài sản'
    _order = 'ma_thanh_ly desc'
    _sql_constraints = [
        ('ma_thanh_ly_unique', 'unique(ma_thanh_ly)', 'Mã thanh lý phải là duy nhất!')
    ]

    ma_thanh_ly = fields.Char(
        string="Mã thanh lý",
        copy=False,
        readonly=True,
        default="New",
        help="Mã duy nhất của phiếu thanh lý, tự động tạo khi thêm mới"
    )

    ngay_thanh_ly = fields.Date(
        string="Ngày thanh lý",
        required=True,
        default=fields.Date.context_today,
        help="Ngày thực hiện thanh lý tài sản"
    )

    tai_san_id = fields.Many2one(
        comodel_name='tai_san',
        string="Tài sản",
        required=True,
        ondelete='restrict',
        help="Tài sản được thanh lý"
    )

    gia_tri_thanh_ly = fields.Float(
        string="Giá trị thanh lý",
        digits=(16, 2),
        required=True,
        help="Số tiền thu được từ việc thanh lý tài sản"
    )

    TRANG_THAI = [
        ('draft', 'Nháp'),
        ('confirmed', 'Đã xác nhận'),
        ('done', 'Hoàn thành'),
        ('cancelled', 'Đã hủy'),
    ]

    trang_thai = fields.Selection(
        selection=TRANG_THAI,
        string="Trạng thái",
        default='draft',
        required=True,
        tracking=True,
        help="Trạng thái của phiếu thanh lý:\n"
             "- Nháp: Chưa xác nhận\n"
             "- Đã xác nhận: Đã được phê duyệt\n"
             "- Hoàn thành: Đã thanh lý xong\n"
             "- Đã hủy: Phiếu bị hủy bỏ"
    )

    ly_do = fields.Text(
        string="Lý do thanh lý",
        help="Lý do tài sản được thanh lý (ví dụ: hỏng hóc, hết khấu hao...)"
    )

    nguoi_xu_ly_id = fields.Many2one(
        comodel_name='nhan_vien',
        string="Người xử lý",
        required=True,
        help="Người thực hiện hoặc chịu trách nhiệm thanh lý"
    )

    @api.model
    def create(self, vals):
        if vals.get('ma_thanh_ly', 'New') == 'New':
            last_record = self.search([], order='ma_thanh_ly desc', limit=1)
            if last_record and last_record.ma_thanh_ly.startswith('TL-'):
                last_number = int(last_record.ma_thanh_ly.split('-')[1])
                new_number = last_number + 1
            else:
                new_number = 1
            vals['ma_thanh_ly'] = f'TL-{new_number:05d}'


        tai_san_id = vals.get('tai_san_id')
        if tai_san_id:
            tai_san = self.env['tai_san'].browse(tai_san_id)
            if tai_san.thanh_ly_id:
                raise ValidationError(f"Tài sản {tai_san.ten_tai_san} đã được thanh lý trước đó!")

        record = super(ThanhLy, self).create(vals)

        record.tai_san_id.thanh_ly_id = record.id
        return record

    @api.constrains('tai_san_id')
    def _check_tai_san_thanh_ly(self):
        for record in self:
            if record.tai_san_id.thanh_ly_id and record.tai_san_id.thanh_ly_id != record:
                raise ValidationError(f"Tài sản {record.tai_san_id.ten_tai_san} đã có phiếu thanh lý khác!")

    def action_confirm(self):
        self.ensure_one()
        if self.trang_thai == 'draft':
            self.trang_thai = 'confirmed'
        else:
            raise ValidationError("Chỉ có thể xác nhận phiếu ở trạng thái Nháp!")

    def action_done(self):
        self.ensure_one()
        if self.trang_thai != 'confirmed':
            raise ValidationError("Phiếu cần được xác nhận trước khi hoàn thành!")
        self.tai_san_id.trang_thai = 'DaThanhLy'
        self.trang_thai = 'done'

    def action_cancel(self):
        self.ensure_one()
        if self.trang_thai in ('draft', 'confirmed'):
            self.trang_thai = 'cancelled'
            self.tai_san_id.thanh_ly_id = False
            self.tai_san_id.trang_thai = 'LuuTru'
        else:
            raise ValidationError("Không thể hủy phiếu đã hoàn thành!")

    @api.constrains('tai_san_id', 'trang_thai')
    def _check_tai_san_trang_thai(self):
        for record in self:
            if record.trang_thai == 'done' and record.tai_san_id.trang_thai not in ('Hong', 'LuuTru'):
                raise ValidationError("Chỉ có thể thanh lý tài sản ở trạng thái 'Hỏng' hoặc 'Lưu trữ'!")
            if record.trang_thai == 'confirmed' and record.tai_san_id.trang_thai in ('Muon', 'BaoTri'):
                raise ValidationError("Không thể thanh lý tài sản đang được mượn hoặc bảo trì!")