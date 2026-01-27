# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class ButToanKhauHao(models.Model):
    """Bút toán khấu hao tài sản - Hệ thống nội bộ (không dùng account.move)"""
    _name = 'ke_toan.but_toan_khau_hao'
    _description = 'Bút toán khấu hao tài sản'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'ngay_ghi_nhan desc, ma_but_toan desc'
    _rec_name = 'ma_but_toan'
    
    ma_but_toan = fields.Char(
        'Mã bút toán',
        readonly=True,
        copy=False,
        default='New',
        help='Mã bút toán tự động tạo'
    )
    
    ngay_ghi_nhan = fields.Date(
        'Ngày ghi nhận',
        required=True,
        default=fields.Date.today,
        tracking=True,
        help='Ngày ghi nhận bút toán khấu hao'
    )
    
    # Liên kết
    ke_toan_tai_san_id = fields.Many2one(
        'ke_toan.tai_san',
        'Kế toán tài sản',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    
    khau_hao_id = fields.Many2one(
        'khau_hao',
        'Khấu hao',
        required=True,
        ondelete='restrict',
        help='Bản ghi khấu hao tương ứng'
    )
    
    tai_san_id = fields.Many2one(
        'tai_san',
        'Tài sản',
        related='khau_hao_id.tai_san_id',
        store=True,
        readonly=True
    )
    
    # Chi tiết bút toán
    tk_no_id = fields.Many2one(
        'ke_toan.tai_khoan',
        'Tài khoản Nợ',
        required=True,
        domain=[('loai_tai_khoan', '=', 'chi_phi')],
        help='TK 627 hoặc TK 642'
    )
    
    tk_co_id = fields.Many2one(
        'ke_toan.tai_khoan',
        'Tài khoản Có',
        required=True,
        domain=[('ma_tai_khoan', '=like', '214%')],
        help='TK 214: Hao mòn TSCĐ'
    )
    
    so_tien = fields.Float(
        'Số tiền',
        required=True,
        digits=(16, 2),
        tracking=True,
        help='Giá trị khấu hao trong kỳ'
    )
    
    dien_giai = fields.Text(
        'Diễn giải',
        help='Nội dung bút toán'
    )
    
    # Đơn vị (phân bổ chi phí) - liên kết module nhan_su
    don_vi_id = fields.Many2one(
        'don_vi',
        'Đơn vị sử dụng',
        help='Đơn vị/Phòng ban chịu chi phí khấu hao'
    )
    
    # Trạng thái
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('posted', 'Đã đăng'),
        ('cancelled', 'Hủy'),
    ], string='Trạng thái', default='draft', tracking=True, copy=False)
    
    company_id = fields.Many2one(
        'res.company',
        'Công ty',
        default=lambda self: self.env.company,
        required=True
    )
    
    ghi_chu = fields.Text('Ghi chú')
    
    _sql_constraints = [
        ('so_tien_positive', 'CHECK(so_tien >= 0)', 
         'Số tiền khấu hao phải lớn hơn hoặc bằng 0!')
    ]
    
    @api.model
    def create(self, vals):
        if vals.get('ma_but_toan', 'New') == 'New':
            vals['ma_but_toan'] = self.env['ir.sequence'].next_by_code('ke_toan.but_toan_khau_hao') or 'New'
        
        return super(ButToanKhauHao, self).create(vals)
    
    def action_post(self):
        """Đăng bút toán - Hệ thống nội bộ"""
        for record in self:
            if record.state != 'draft':
                raise UserError('Chỉ có thể đăng bút toán ở trạng thái Nháp!')
            
            if record.so_tien <= 0:
                raise UserError('Số tiền khấu hao phải lớn hơn 0!')
            
            # Cập nhật trạng thái
            record.write({'state': 'posted'})
            
            # Cập nhật giá trị tài sản
            record._update_gia_tri_tai_san()
            
            # Cập nhật số dư tài khoản
            record._cap_nhat_so_du_tai_khoan()
            
            _logger.info(f"Đã đăng bút toán {record.ma_but_toan} - Số tiền: {record.so_tien:,.0f}")
        
        return True
    
    def _cap_nhat_so_du_tai_khoan(self):
        """Cập nhật số dư tài khoản nội bộ"""
        self.ensure_one()
        
        # Tăng số dư bên Nợ của TK chi phí
        if self.tk_no_id:
            self.tk_no_id.sudo().write({
                'so_du': self.tk_no_id.so_du + self.so_tien
            })
        
        # Tăng số dư bên Có của TK hao mòn
        if self.tk_co_id:
            self.tk_co_id.sudo().write({
                'so_du': self.tk_co_id.so_du + self.so_tien
            })
    
    def _update_gia_tri_tai_san(self):
        """Cập nhật giá trị hiện tại của tài sản"""
        self.ensure_one()
        
        tai_san = self.tai_san_id
        if tai_san:
            # Tính giá trị mới
            gia_tri_moi = max(tai_san.gia_tri_hien_tai - self.so_tien, 0)
            tai_san.sudo().write({'gia_tri_hien_tai': gia_tri_moi})
            
            _logger.info(f"Cập nhật giá trị tài sản {tai_san.ma_tai_san}: {gia_tri_moi:,.0f} VNĐ")
    
    def action_cancel(self):
        """Hủy bút toán"""
        for record in self:
            if record.state == 'cancelled':
                raise UserError('Bút toán đã bị hủy!')
            
            # Hoàn trả số dư tài khoản nếu đã đăng
            if record.state == 'posted':
                record._hoan_tra_so_du_tai_khoan()
            
            record.write({'state': 'cancelled'})
        
        return True
    
    def _hoan_tra_so_du_tai_khoan(self):
        """Hoàn trả số dư khi hủy bút toán"""
        self.ensure_one()
        
        if self.tk_no_id:
            self.tk_no_id.sudo().write({
                'so_du': self.tk_no_id.so_du - self.so_tien
            })
        
        if self.tk_co_id:
            self.tk_co_id.sudo().write({
                'so_du': self.tk_co_id.so_du - self.so_tien
            })
    
    def action_draft(self):
        """Chuyển về nháp"""
        for record in self:
            if record.state == 'draft':
                raise UserError('Bút toán đã ở trạng thái Nháp!')
            
            record.write({'state': 'draft'})
        
        return True
    
    def unlink(self):
        for record in self:
            if record.state == 'posted':
                raise UserError('Không thể xóa bút toán đã đăng! Vui lòng hủy trước.')
        return super(ButToanKhauHao, self).unlink()
