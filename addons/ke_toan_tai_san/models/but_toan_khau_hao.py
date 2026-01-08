# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class ButToanKhauHao(models.Model):
    """Bút toán khấu hao tài sản"""
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
    
    # Đơn vị (phân bổ chi phí)
    don_vi_id = fields.Many2one(
        'don_vi',
        'Đơn vị sử dụng',
        help='Đơn vị/Phòng ban chịu chi phí khấu hao'
    )
    
    # Liên kết với Odoo Accounting
    account_move_id = fields.Many2one(
        'account.move',
        'Bút toán hệ thống',
        readonly=True,
        copy=False,
        help='Bút toán tương ứng trong module Account'
    )
    
    journal_id = fields.Many2one(
        'account.journal',
        'Sổ nhật ký',
        domain=[('type', '=', 'general')],
        help='Sổ nhật ký ghi nhận khấu hao'
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
        
        # Tự động lấy journal nếu chưa có
        if not vals.get('journal_id'):
            journal = self.env['account.journal'].search([
                ('type', '=', 'general'),
                ('company_id', '=', vals.get('company_id', self.env.company.id))
            ], limit=1)
            if journal:
                vals['journal_id'] = journal.id
        
        return super(ButToanKhauHao, self).create(vals)
    
    def action_post(self):
        """Đăng bút toán (sinh account.move và post)"""
        for record in self:
            if record.state != 'draft':
                raise UserError('Chỉ có thể đăng bút toán ở trạng thái Nháp!')
            
            if record.so_tien <= 0:
                raise UserError('Số tiền khấu hao phải lớn hơn 0!')
            
            # Sinh account.move
            account_move = record._create_account_move()
            
            # Đăng account.move
            account_move.action_post()
            
            # Cập nhật trạng thái
            record.write({
                'account_move_id': account_move.id,
                'state': 'posted'
            })
            
            # Cập nhật giá trị tài sản
            record._update_gia_tri_tai_san()
            
            _logger.info(f"Đã đăng bút toán {record.ma_but_toan} - Số tiền: {record.so_tien:,.0f}")
        
        return True
    
    def _create_account_move(self):
        """Tạo account.move từ bút toán"""
        self.ensure_one()
        
        # Ánh xạ tài khoản nội bộ sang account.account
        acc_no = self._map_to_account_account(self.tk_no_id)
        acc_co = self._map_to_account_account(self.tk_co_id)
        
        if not acc_no or not acc_co:
            raise UserError('Không tìm thấy tài khoản Odoo tương ứng! Vui lòng cấu hình trong Danh mục Tài khoản.')
        
        # Tạo account.move
        move_vals = {
            'move_type': 'entry',
            'date': self.ngay_ghi_nhan,
            'journal_id': self.journal_id.id,
            'ref': self.ma_but_toan,
            'company_id': self.company_id.id,
            'line_ids': [
                # Dòng Nợ (Chi phí khấu hao)
                (0, 0, {
                    'name': self.dien_giai or f'Khấu hao {self.tai_san_id.ten_tai_san}',
                    'account_id': acc_no.id,
                    'debit': self.so_tien,
                    'credit': 0,
                    'partner_id': False,
                }),
                # Dòng Có (Hao mòn lũy kế)
                (0, 0, {
                    'name': self.dien_giai or f'Hao mòn {self.tai_san_id.ten_tai_san}',
                    'account_id': acc_co.id,
                    'debit': 0,
                    'credit': self.so_tien,
                    'partner_id': False,
                }),
            ]
        }
        
        account_move = self.env['account.move'].create(move_vals)
        
        return account_move
    
    def _map_to_account_account(self, ke_toan_tai_khoan):
        """Ánh xạ từ ke_toan.tai_khoan sang account.account"""
        if not ke_toan_tai_khoan:
            return None
        
        # Nếu đã có liên kết
        if ke_toan_tai_khoan.account_account_id:
            return ke_toan_tai_khoan.account_account_id
        
        # Tìm theo mã tài khoản
        account = self.env['account.account'].search([
            ('code', '=', ke_toan_tai_khoan.ma_tai_khoan),
            ('company_id', '=', self.company_id.id)
        ], limit=1)
        
        if account:
            # Lưu liên kết
            ke_toan_tai_khoan.sudo().write({'account_account_id': account.id})
            return account
        
        # Tạo mới nếu chưa có
        account_type = self._get_account_type(ke_toan_tai_khoan)
        if not account_type:
            raise UserError(f'Không xác định được loại tài khoản cho TK {ke_toan_tai_khoan.ma_tai_khoan}')
        
        account = self.env['account.account'].create({
            'code': ke_toan_tai_khoan.ma_tai_khoan,
            'name': ke_toan_tai_khoan.ten_tai_khoan,
            'user_type_id': account_type.id,
            'company_id': self.company_id.id,
            'reconcile': False,
        })
        
        # Lưu liên kết
        ke_toan_tai_khoan.sudo().write({'account_account_id': account.id})
        
        return account
    
    def _get_account_type(self, ke_toan_tai_khoan):
        """Lấy account.account.type phù hợp"""
        # Mapping loại tài khoản
        type_mapping = {
            'tai_san': 'asset_fixed',  # Tài sản cố định
            'chi_phi': 'expense',  # Chi phí
        }
        
        type_xml_id = type_mapping.get(ke_toan_tai_khoan.loai_tai_khoan)
        if not type_xml_id:
            return None
        
        # Tìm account.account.type
        account_type = self.env.ref(f'account.data_account_type_{type_xml_id}', raise_if_not_found=False)
        
        if not account_type:
            # Fallback: Tìm theo tên
            account_type = self.env['account.account.type'].search([
                ('type', '=', type_xml_id)
            ], limit=1)
        
        return account_type
    
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
            
            if record.account_move_id:
                # Hủy account.move (nếu có thể)
                if record.account_move_id.state == 'posted':
                    record.account_move_id.button_draft()
                record.account_move_id.button_cancel()
            
            record.write({'state': 'cancelled'})
        
        return True
    
    def action_draft(self):
        """Chuyển về nháp"""
        for record in self:
            if record.state == 'draft':
                raise UserError('Bút toán đã ở trạng thái Nháp!')
            
            record.write({'state': 'draft'})
        
        return True
    
    def action_view_account_move(self):
        """Xem account.move"""
        self.ensure_one()
        
        if not self.account_move_id:
            raise UserError('Chưa có bút toán hệ thống!')
        
        return {
            'name': 'Bút toán kế toán',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': self.account_move_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def unlink(self):
        for record in self:
            if record.state == 'posted':
                raise UserError('Không thể xóa bút toán đã đăng! Vui lòng hủy trước.')
        return super(ButToanKhauHao, self).unlink()
