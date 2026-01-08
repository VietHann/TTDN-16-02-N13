# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime


class DatPhong(models.Model):
    _name = 'dat_phong'
    _description = 'Đặt lịch phòng họp'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'tieu_de'
    _order = 'ngay_bat_dau desc'

    ma_dat_phong = fields.Char(
        "Mã đặt phòng",
        required=True,
        copy=False,
        readonly=True,
        default="New",
        help="Mã tự động"
    )

    tieu_de = fields.Char(
        "Tiêu đề cuộc họp",
        required=True,
        tracking=True,
        help="Tên cuộc họp/sự kiện"
    )

    phong_hop_id = fields.Many2one(
        'phong_hop',
        string="Phòng họp",
        required=True,
        tracking=True,
        help="Phòng họp được đặt"
    )

    nguoi_dat_id = fields.Many2one(
        'nhan_vien',
        string="Người đặt",
        required=True,
        tracking=True,
        help="Người đặt phòng"
    )

    ngay_bat_dau = fields.Datetime(
        "Thời gian bắt đầu",
        required=True,
        tracking=True,
        help="Thời điểm bắt đầu họp"
    )

    ngay_ket_thuc = fields.Datetime(
        "Thời gian kết thúc",
        required=True,
        tracking=True,
        help="Thời điểm kết thúc họp"
    )

    thoi_luong = fields.Float(
        "Thời lượng (giờ)",
        compute='_compute_thoi_luong',
        store=True,
        help="Tự động tính từ thời gian bắt đầu và kết thúc"
    )

    so_nguoi_tham_gia = fields.Integer(
        "Số người tham gia",
        help="Số người dự kiến tham gia"
    )

    TRANG_THAI = [
        ('cho_xac_nhan', 'Chờ xác nhận'),
        ('da_xac_nhan', 'Đã xác nhận'),
        ('dang_dien_ra', 'Đang diễn ra'),
        ('hoan_thanh', 'Hoàn thành'),
        ('huy', 'Hủy'),
    ]

    trang_thai = fields.Selection(
        TRANG_THAI,
        string="Trạng thái",
        default='cho_xac_nhan',
        required=True,
        tracking=True,
        help="Trạng thái đặt phòng"
    )

    thiet_bi_su_dung_ids = fields.Many2many(
        'tai_san',
        'dat_phong_tai_san_rel',
        'dat_phong_id',
        'tai_san_id',
        string="Thiết bị sử dụng",
        help="Thiết bị trong phòng sẽ được mượn cùng"
    )

    noi_dung = fields.Text("Nội dung cuộc họp")
    ghi_chu = fields.Text("Ghi chú")

    _sql_constraints = [
        ('ma_dat_phong_unique', 'unique(ma_dat_phong)', 'Mã đặt phòng phải là duy nhất!')
    ]

    @api.depends('ngay_bat_dau', 'ngay_ket_thuc')
    def _compute_thoi_luong(self):
        for record in self:
            if record.ngay_bat_dau and record.ngay_ket_thuc:
                delta = record.ngay_ket_thuc - record.ngay_bat_dau
                record.thoi_luong = delta.total_seconds() / 3600
            else:
                record.thoi_luong = 0

    @api.constrains('ngay_bat_dau', 'ngay_ket_thuc')
    def _check_dates(self):
        for record in self:
            if record.ngay_bat_dau and record.ngay_ket_thuc:
                if record.ngay_ket_thuc <= record.ngay_bat_dau:
                    raise ValidationError("Thời gian kết thúc phải sau thời gian bắt đầu!")

    @api.constrains('so_nguoi_tham_gia', 'phong_hop_id')
    def _check_suc_chua(self):
        for record in self:
            if record.so_nguoi_tham_gia and record.phong_hop_id:
                if record.so_nguoi_tham_gia > record.phong_hop_id.suc_chua:
                    raise ValidationError(
                        f"Số người tham gia ({record.so_nguoi_tham_gia}) vượt quá "
                        f"sức chứa phòng ({record.phong_hop_id.suc_chua})!"
                    )

    @api.constrains('phong_hop_id', 'ngay_bat_dau', 'ngay_ket_thuc', 'trang_thai')
    def _check_trung_lich(self):
        """Kiểm tra trùng lịch đặt phòng"""
        for record in self:
            if record.trang_thai not in ['cho_xac_nhan', 'da_xac_nhan', 'dang_dien_ra']:
                continue

            domain = [
                ('phong_hop_id', '=', record.phong_hop_id.id),
                ('id', '!=', record.id),
                ('trang_thai', 'in', ['cho_xac_nhan', 'da_xac_nhan', 'dang_dien_ra']),
                '|',
                '&', ('ngay_bat_dau', '<=', record.ngay_bat_dau), ('ngay_ket_thuc', '>', record.ngay_bat_dau),
                '&', ('ngay_bat_dau', '<', record.ngay_ket_thuc), ('ngay_ket_thuc', '>=', record.ngay_ket_thuc),
            ]

            trung_lich = self.search(domain, limit=1)
            if trung_lich:
                raise ValidationError(
                    f"Phòng {record.phong_hop_id.ten_phong} đã được đặt trong khoảng thời gian này!\n"
                    f"Lịch trùng: {trung_lich.tieu_de} ({trung_lich.ngay_bat_dau} - {trung_lich.ngay_ket_thuc})"
                )

    @api.model
    def create(self, vals):
        if vals.get('ma_dat_phong', 'New') == 'New':
            vals['ma_dat_phong'] = self.env['ir.sequence'].next_by_code('dat_phong') or 'DP-00001'
        return super(DatPhong, self).create(vals)

    @api.onchange('phong_hop_id')
    def _onchange_phong_hop(self):
        """Tự động load thiết bị của phòng"""
        if self.phong_hop_id:
            self.thiet_bi_su_dung_ids = self.phong_hop_id.thiet_bi_ids

    def action_xac_nhan(self):
        """Xác nhận đặt phòng"""
        for record in self:
            if record.trang_thai != 'cho_xac_nhan':
                raise UserError("Chỉ đơn chờ xác nhận mới có thể xác nhận!")
            
            # Cập nhật trạng thái phòng
            if record.phong_hop_id.trang_thai == 'san_sang':
                record.phong_hop_id.trang_thai = 'dang_su_dung'
            
            # Tạo phiếu mượn thiết bị (nếu có)
            if record.thiet_bi_su_dung_ids:
                for thiet_bi in record.thiet_bi_su_dung_ids:
                    self.env['phieu_muon'].create({
                        'tai_san_id': thiet_bi.id,
                        'nhan_vien_id': record.nguoi_dat_id.id,
                        'ngay_muon': record.ngay_bat_dau,
                        'ngay_tra_du_kien': record.ngay_ket_thuc,
                        'ly_do_muon': f'Sử dụng cho cuộc họp: {record.tieu_de}',
                    })
            
            record.trang_thai = 'da_xac_nhan'

    def action_bat_dau(self):
        """Bắt đầu cuộc họp"""
        for record in self:
            if record.trang_thai != 'da_xac_nhan':
                raise UserError("Chỉ đơn đã xác nhận mới có thể bắt đầu!")
            record.trang_thai = 'dang_dien_ra'

    def action_hoan_thanh(self):
        """Hoàn thành cuộc họp"""
        for record in self:
            if record.trang_thai != 'dang_dien_ra':
                raise UserError("Chỉ cuộc họp đang diễn ra mới có thể hoàn thành!")
            
            # Trả phòng về trạng thái sẵn sàng
            if record.phong_hop_id.trang_thai == 'dang_su_dung':
                record.phong_hop_id.trang_thai = 'san_sang'
            
            record.trang_thai = 'hoan_thanh'

    def action_huy(self):
        """Hủy đặt phòng"""
        for record in self:
            if record.trang_thai in ['hoan_thanh']:
                raise UserError("Không thể hủy cuộc họp đã hoàn thành!")
            
            # Trả phòng về trạng thái sẵn sàng
            if record.phong_hop_id.trang_thai == 'dang_su_dung':
                record.phong_hop_id.trang_thai = 'san_sang'
            
            record.trang_thai = 'huy'
