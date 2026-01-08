# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class KeToanTaiSan(models.Model):
    """Bridge Model: Liên kết Tài sản với Kế toán"""
    _name = 'ke_toan.tai_san'
    _description = 'Liên kết Tài sản - Kế toán'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'tai_san_id'
    _order = 'tai_san_id'
    
    tai_san_id = fields.Many2one(
        'tai_san',
        'Tài sản',
        required=True,
        ondelete='cascade',
        help='Tài sản được quản lý kế toán'
    )
    
    # Thông tin cơ bản từ tài sản
    ma_tai_san = fields.Char(related='tai_san_id.ma_tai_san', string='Mã TS', store=True)
    ten_tai_san = fields.Char(related='tai_san_id.ten_tai_san', string='Tên TS', store=True)
    loai_tai_san_id = fields.Many2one(related='tai_san_id.loai_tai_san_id', string='Loại TS', store=True)
    
    # Tài khoản kế toán
    tk_nguyen_gia = fields.Many2one(
        'ke_toan.tai_khoan',
        'TK Nguyên giá',
        domain=[('ma_tai_khoan', '=like', '21%')],
        default=lambda self: self._get_default_tk_211(),
        help='TK 211: Tài sản cố định hữu hình'
    )
    
    tk_hao_mon = fields.Many2one(
        'ke_toan.tai_khoan',
        'TK Hao mòn',
        domain=[('ma_tai_khoan', '=like', '214%')],
        default=lambda self: self._get_default_tk_214(),
        help='TK 214: Hao mòn TSCĐ hữu hình'
    )
    
    tk_chi_phi = fields.Many2one(
        'ke_toan.tai_khoan',
        'TK Chi phí khấu hao',
        domain=[('ma_tai_khoan', 'in', ['627', '642'])],
        default=lambda self: self._get_default_tk_627(),
        help='TK 627: Chi phí sản xuất chung hoặc TK 642: Chi phí quản lý DN'
    )
    
    # Giá trị tài sản
    nguyen_gia = fields.Float(
        'Nguyên giá',
        related='tai_san_id.gia_tien_mua',
        store=True,
        digits=(16, 2),
        help='Giá mua ban đầu của tài sản'
    )
    
    hao_mon_luy_ke = fields.Float(
        'Hao mòn lũy kế',
        compute='_compute_hao_mon_luy_ke',
        store=True,
        digits=(16, 2),
        help='Tổng giá trị đã khấu hao'
    )
    
    gia_tri_con_lai = fields.Float(
        'Giá trị còn lại',
        related='tai_san_id.gia_tri_hien_tai',
        store=True,
        digits=(16, 2),
        help='Nguyên giá - Hao mòn lũy kế'
    )
    
    # Cấu hình khấu hao
    phuong_phap_khau_hao = fields.Selection([
        ('duong_thang', 'Đường thẳng'),
        ('so_du_giam_dan', 'Số dư giảm dần'),
    ], string='Phương pháp khấu hao', default='duong_thang', required=True)
    
    thoi_gian_khau_hao = fields.Integer(
        'Thời gian khấu hao (tháng)',
        default=60,
        help='Số tháng khấu hao (Mặc định: 60 tháng = 5 năm)'
    )
    
    ty_le_khau_hao_nam = fields.Float(
        'Tỷ lệ khấu hao (%/năm)',
        default=20.0,
        help='Tỷ lệ % khấu hao hàng năm (cho phương pháp số dư giảm dần)'
    )
    
    gia_tri_thanh_ly = fields.Float(
        'Giá trị thanh lý dự kiến',
        default=0,
        digits=(16, 2),
        help='Giá trị còn lại sau khi khấu hao hết'
    )
    
    ngay_bat_dau_khau_hao = fields.Date(
        'Ngày bắt đầu khấu hao',
        default=fields.Date.today,
        help='Ngày bắt đầu tính khấu hao (thường là ngày đưa vào sử dụng)'
    )
    
    # Đơn vị sử dụng (phân bổ chi phí)
    don_vi_id = fields.Many2one(
        'don_vi',
        'Đơn vị sử dụng',
        help='Đơn vị/Phòng ban sử dụng tài sản (để phân bổ chi phí)'
    )
    
    # Lịch sử bút toán
    but_toan_ids = fields.One2many(
        'ke_toan.but_toan_khau_hao',
        'ke_toan_tai_san_id',
        'Bút toán khấu hao',
        readonly=True
    )
    
    so_but_toan = fields.Integer(
        'Số bút toán',
        compute='_compute_so_but_toan'
    )
    
    # Trạng thái
    co_khau_hao = fields.Boolean(
        'Có khấu hao',
        default=True,
        help='Tài sản này có được khấu hao tự động không'
    )
    
    active = fields.Boolean('Đang sử dụng', default=True)
    
    ghi_chu = fields.Text('Ghi chú')
    
    _sql_constraints = [
        ('tai_san_unique', 'unique(tai_san_id)', 
         'Tài sản này đã được liên kết với kế toán!')
    ]
    
    @api.model
    def _get_default_tk_211(self):
        """Lấy tài khoản 211 mặc định"""
        return self.env['ke_toan.tai_khoan'].search([('ma_tai_khoan', '=', '211')], limit=1)
    
    @api.model
    def _get_default_tk_214(self):
        """Lấy tài khoản 214 mặc định"""
        return self.env['ke_toan.tai_khoan'].search([('ma_tai_khoan', '=', '214')], limit=1)
    
    @api.model
    def _get_default_tk_627(self):
        """Lấy tài khoản 627 mặc định"""
        return self.env['ke_toan.tai_khoan'].search([('ma_tai_khoan', '=', '627')], limit=1)
    
    @api.depends('but_toan_ids', 'but_toan_ids.so_tien', 'but_toan_ids.state')
    def _compute_hao_mon_luy_ke(self):
        for record in self:
            # Tổng các bút toán đã đăng
            but_toan_posted = record.but_toan_ids.filtered(lambda x: x.state == 'posted')
            record.hao_mon_luy_ke = sum(but_toan_posted.mapped('so_tien'))
    
    @api.depends('but_toan_ids')
    def _compute_so_but_toan(self):
        for record in self:
            record.so_but_toan = len(record.but_toan_ids)
    
    @api.constrains('thoi_gian_khau_hao')
    def _check_thoi_gian_khau_hao(self):
        for record in self:
            if record.thoi_gian_khau_hao <= 0:
                raise ValidationError('Thời gian khấu hao phải lớn hơn 0!')
    
    @api.constrains('ty_le_khau_hao_nam')
    def _check_ty_le_khau_hao(self):
        for record in self:
            if not (0 < record.ty_le_khau_hao_nam <= 100):
                raise ValidationError('Tỷ lệ khấu hao phải trong khoảng 0-100%!')
    
    @api.model
    def create(self, vals):
        """Tự động lấy cấu hình từ loại tài sản"""
        if vals.get('tai_san_id'):
            tai_san = self.env['tai_san'].browse(vals['tai_san_id'])
            if tai_san.loai_tai_san_id:
                cau_hinh = self.env['ke_toan.cau_hinh_khau_hao'].search([
                    ('loai_tai_san_id', '=', tai_san.loai_tai_san_id.id)
                ], limit=1)
                
                if cau_hinh:
                    vals.update({
                        'phuong_phap_khau_hao': cau_hinh.phuong_phap_mac_dinh,
                        'thoi_gian_khau_hao': cau_hinh.thoi_gian_mac_dinh,
                        'ty_le_khau_hao_nam': cau_hinh.ty_le_khau_hao_nam,
                        'tk_chi_phi': cau_hinh.tk_chi_phi_id.id if cau_hinh.tk_chi_phi_id else vals.get('tk_chi_phi'),
                    })
        
        return super(KeToanTaiSan, self).create(vals)
    
    def tinh_khau_hao_thang(self):
        """
        Tính giá trị khấu hao cho tháng hiện tại
        Returns: float - Giá trị khấu hao
        """
        self.ensure_one()
        
        if not self.co_khau_hao:
            return 0
        
        if self.gia_tri_con_lai <= 0:
            return 0
        
        if self.phuong_phap_khau_hao == 'duong_thang':
            # Khấu hao đường thẳng
            gia_tri_co_the_khau_hao = self.nguyen_gia - self.gia_tri_thanh_ly
            khau_hao_thang = gia_tri_co_the_khau_hao / self.thoi_gian_khau_hao
        else:
            # Khấu hao số dư giảm dần
            ty_le_thang = self.ty_le_khau_hao_nam / 12 / 100
            khau_hao_thang = self.gia_tri_con_lai * ty_le_thang
        
        # Đảm bảo không khấu hao quá giá trị còn lại
        return min(khau_hao_thang, self.gia_tri_con_lai)
    
    def sinh_but_toan_khau_hao(self):
        """
        Sinh bút toán khấu hao cho tháng hiện tại (thủ công)
        """
        self.ensure_one()
        
        gia_tri_khau_hao = self.tinh_khau_hao_thang()
        
        if gia_tri_khau_hao <= 0:
            raise UserError('Không thể tạo bút toán khấu hao: Giá trị khấu hao = 0')
        
        # Tạo bản ghi khấu hao
        khau_hao = self.env['khau_hao'].create({
            'tai_san_id': self.tai_san_id.id,
            'phuong_phap_khau_hao': self.phuong_phap_khau_hao,
            'ngay_khau_hao': fields.Date.today(),
            'ghi_chu': 'Khấu hao thủ công',
        })
        
        # Sinh bút toán
        but_toan = self._create_but_toan_khau_hao(khau_hao, gia_tri_khau_hao)
        
        return {
            'name': 'Bút toán khấu hao',
            'type': 'ir.actions.act_window',
            'res_model': 'ke_toan.but_toan_khau_hao',
            'res_id': but_toan.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def _create_but_toan_khau_hao(self, khau_hao, gia_tri):
        """
        Tạo bút toán khấu hao (internal method)
        """
        but_toan = self.env['ke_toan.but_toan_khau_hao'].create({
            'ke_toan_tai_san_id': self.id,
            'khau_hao_id': khau_hao.id,
            'tk_no_id': self.tk_chi_phi.id,
            'tk_co_id': self.tk_hao_mon.id,
            'so_tien': gia_tri,
            'ngay_ghi_nhan': fields.Date.today(),
            'dien_giai': f'Khấu hao tài sản {self.ten_tai_san} - Tháng {fields.Date.today().strftime("%m/%Y")}',
            'don_vi_id': self.don_vi_id.id if self.don_vi_id else False,
        })
        
        return but_toan
    
    @api.model
    def cron_khau_hao_tu_dong(self):
        """
        Cron Job: Tự động khấu hao tài sản hàng tháng
        Chạy vào ngày 1 hàng tháng lúc 00:00
        """
        _logger.info("=" * 60)
        _logger.info("BẮT ĐẦU KHẤU HAO TỰ ĐỘNG - %s", fields.Date.today())
        _logger.info("=" * 60)
        
        # Lấy tất cả tài sản cần khấu hao
        ke_toan_tai_san = self.search([
            ('co_khau_hao', '=', True),
            ('tai_san_id.trang_thai', 'not in', ['DaThanhLy']),
            ('gia_tri_con_lai', '>', 0),
            ('active', '=', True),
        ])
        
        thanh_cong = 0
        loi = 0
        tong_gia_tri = 0
        
        for kt_ts in ke_toan_tai_san:
            try:
                # Tính khấu hao
                gia_tri_khau_hao = kt_ts.tinh_khau_hao_thang()
                
                if gia_tri_khau_hao <= 0:
                    _logger.info(f"Bỏ qua {kt_ts.ma_tai_san}: Giá trị khấu hao = 0")
                    continue
                
                # Tạo bản ghi khấu hao
                khau_hao = self.env['khau_hao'].create({
                    'tai_san_id': kt_ts.tai_san_id.id,
                    'phuong_phap_khau_hao': kt_ts.phuong_phap_khau_hao,
                    'ngay_khau_hao': fields.Date.today(),
                    'ghi_chu': 'Khấu hao tự động (Cron)',
                })
                
                # Sinh bút toán
                but_toan = kt_ts._create_but_toan_khau_hao(khau_hao, gia_tri_khau_hao)
                
                # Tự động đăng bút toán
                but_toan.action_post()
                
                thanh_cong += 1
                tong_gia_tri += gia_tri_khau_hao
                
                _logger.info(f"✓ {kt_ts.ma_tai_san}: Khấu hao {gia_tri_khau_hao:,.0f} VNĐ")
                
            except Exception as e:
                loi += 1
                _logger.error(f"✗ Lỗi khấu hao {kt_ts.ma_tai_san}: {str(e)}")
        
        _logger.info("=" * 60)
        _logger.info(f"KẾT QUẢ: {thanh_cong} thành công | {loi} lỗi")
        _logger.info(f"TỔNG GIÁ TRỊ KHẤU HAO: {tong_gia_tri:,.0f} VNĐ")
        _logger.info("=" * 60)
        
        return True
    
    def action_view_but_toan(self):
        """Xem danh sách bút toán khấu hao"""
        self.ensure_one()
        return {
            'name': f'Bút toán khấu hao - {self.ten_tai_san}',
            'type': 'ir.actions.act_window',
            'res_model': 'ke_toan.but_toan_khau_hao',
            'view_mode': 'tree,form',
            'domain': [('ke_toan_tai_san_id', '=', self.id)],
            'context': {'default_ke_toan_tai_san_id': self.id},
        }
