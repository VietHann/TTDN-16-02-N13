# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class ThuChi(models.Model):
    _name = 'ke_toan.thu_chi'
    _description = 'Quản lý thu chi'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'ma_phieu'
    _order = 'ngay_ghi_nhan desc'

    ma_phieu = fields.Char(
        "Mã phiếu",
        required=True,
        copy=False,
        readonly=True,
        default="New",
        help="Mã phiếu tự động"
    )

    LOAI_PHIEU = [
        ('thu', 'Phiếu Thu'),
        ('chi', 'Phiếu Chi'),
    ]

    loai_phieu = fields.Selection(
        LOAI_PHIEU,
        string="Loại phiếu",
        required=True,
        tracking=True,
        help="Loại thu hoặc chi"
    )

    ngay_ghi_nhan = fields.Date(
        "Ngày ghi nhận",
        required=True,
        default=fields.Date.today,
        tracking=True,
        help="Ngày phát sinh thu/chi"
    )

    so_tien = fields.Float(
        "Số tiền",
        required=True,
        digits=(16, 2),
        tracking=True,
        help="Số tiền thu/chi"
    )

    doi_tuong = fields.Char(
        "Đối tượng",
        required=True,
        help="Người nộp/nhận tiền"
    )

    noi_dung = fields.Text(
        "Nội dung",
        required=True,
        help="Diễn giải thu/chi"
    )

    PHUONG_THUC = [
        ('tien_mat', 'Tiền mặt'),
        ('chuyen_khoan', 'Chuyển khoản'),
        ('the', 'Thẻ'),
    ]

    phuong_thuc = fields.Selection(
        PHUONG_THUC,
        string="Phương thức",
        default='tien_mat',
        required=True,
        help="Hình thức thanh toán"
    )

    tai_khoan_id = fields.Many2one(
        'ke_toan.tai_khoan',
        string="Tài khoản",
        required=True,
        help="Tài khoản kế toán liên quan"
    )

    don_vi_id = fields.Many2one(
        'don_vi',
        string="Đơn vị",
        help="Đơn vị/phòng ban"
    )

    nguoi_lap_id = fields.Many2one(
        'nhan_vien',
        string="Người lập",
        required=True,
        help="Người lập phiếu"
    )

    TRANG_THAI = [
        ('nhap', 'Nháp'),
        ('da_duyet', 'Đã duyệt'),
        ('huy', 'Hủy'),
    ]

    trang_thai = fields.Selection(
        TRANG_THAI,
        string="Trạng thái",
        default='nhap',
        required=True,
        tracking=True,
        help="Trạng thái phiếu"
    )

    ghi_chu = fields.Text("Ghi chú")

    _sql_constraints = [
        ('ma_phieu_unique', 'unique(ma_phieu)', 'Mã phiếu phải là duy nhất!')
    ]

    @api.constrains('so_tien')
    def _check_so_tien(self):
        for record in self:
            if record.so_tien <= 0:
                raise ValidationError("Số tiền phải lớn hơn 0!")

    @api.model
    def create(self, vals):
        if vals.get('ma_phieu', 'New') == 'New':
            if vals.get('loai_phieu') == 'thu':
                seq = self.env['ir.sequence'].next_by_code('ke_toan.phieu_thu')
                if not seq:
                    # Fallback: tạo mã dựa trên timestamp
                    import time
                    seq = f"PT-{int(time.time())}"
                vals['ma_phieu'] = seq
            else:
                seq = self.env['ir.sequence'].next_by_code('ke_toan.phieu_chi')
                if not seq:
                    import time
                    seq = f"PC-{int(time.time())}"
                vals['ma_phieu'] = seq
        return super(ThuChi, self).create(vals)

    def action_duyet(self):
        """Duyệt phiếu thu chi"""
        for record in self:
            if record.trang_thai != 'nhap':
                raise UserError("Chỉ phiếu nháp mới có thể duyệt!")
            
            # Chỉ duyệt trạng thái (tạm bỏ sinh bút toán account.move)
            # TODO: Khi có module accounting đầy đủ, bổ sung sinh bút toán
            record.write({
                'trang_thai': 'da_duyet',
            })

    def action_huy(self):
        """Hủy phiếu"""
        for record in self:
            if record.trang_thai == 'da_duyet':
                raise UserError("Không thể hủy phiếu đã duyệt! Hãy hủy bút toán trước.")
            record.trang_thai = 'huy'

    def _get_tk_tien(self):
        """Lấy tài khoản tiền"""
        if self.phuong_thuc == 'tien_mat':
            return self.env['ke_toan.tai_khoan'].search([('ma_tai_khoan', '=', '111')], limit=1)
        else:
            return self.env['ke_toan.tai_khoan'].search([('ma_tai_khoan', '=', '112')], limit=1)

