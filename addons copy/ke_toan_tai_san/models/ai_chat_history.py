# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class AIChatHistory(models.Model):
    """Lịch sử chat với AI Assistant"""
    _name = 'ai.chat.history'
    _description = 'Lịch sử trò chuyện với AI'
    _order = 'create_date asc'
    _rec_name = 'conversation_id'

    conversation_id = fields.Char(
        'ID cuộc trò chuyện',
        required=True,
        default='default',
        help='ID để nhóm các tin nhắn trong cùng cuộc trò chuyện'
    )

    message = fields.Text('Nội dung tin nhắn', required=True)
    message_type = fields.Selection([
        ('user', 'User'),
        ('assistant', 'AI Assistant'),
        ('system', 'System'),
    ], string='Loại tin nhắn', required=True, default='user')

    user_id = fields.Many2one('res.users', string='Người dùng', default=lambda self: self.env.uid)

    # Metadata
    create_date = fields.Datetime('Thời gian', readonly=True, default=fields.Datetime.now)
    ip_address = fields.Char('IP Address', help='IP của người gửi tin nhắn')

    # Thống kê
    message_length = fields.Integer('Độ dài tin nhắn', compute='_compute_message_length', store=True)
    response_time = fields.Float('Thời gian phản hồi (giây)', digits=(4, 2), help='Thời gian AI phản hồi')

    # Liên kết với tài sản nếu AI đề cập đến
    related_tai_san_ids = fields.Many2many(
        'tai_san',
        'ai_chat_history_tai_san_rel',
        string='Tài sản liên quan'
    )

    related_nhan_vien_ids = fields.Many2many(
        'nhan_vien',
        'ai_chat_history_nhan_vien_rel',
        string='Nhân viên liên quan'
    )

    # Cảm xúc/đánh giá (tương lai)
    user_rating = fields.Selection([
        ('1', '😞'),
        ('2', '😐'),
        ('3', '🙂'),
        ('4', '😊'),
        ('5', '🤩'),
    ], string='Đánh giá')

    @api.depends('message')
    def _compute_message_length(self):
        """Tính độ dài tin nhắn"""
        for record in self:
            record.message_length = len(record.message or '') if record.message else 0

    @api.model
    def create(self, vals):
        """Override create để lưu IP address"""
        if 'ip_address' not in vals:
            vals['ip_address'] = self._get_client_ip()

        return super(AIChatHistory, self).create(vals)

    def _get_client_ip(self):
        """Lấy IP address của client"""
        try:
            from odoo.http import request
            if request and hasattr(request, 'httprequest'):
                return request.httprequest.remote_addr
        except:
            pass
        return False

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================

    def action_view_related_assets(self):
        """Xem tài sản liên quan"""
        self.ensure_one()
        if not self.related_tai_san_ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Không có tài sản liên quan'),
                    'message': 'AI không đề cập đến tài sản nào trong tin nhắn này',
                    'type': 'warning',
                }
            }

        return {
            'name': _('Tài sản liên quan'),
            'type': 'ir.actions.act_window',
            'res_model': 'tai_san',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.related_tai_san_ids.ids)],
            'context': {'create': False},
        }

    def action_view_related_employees(self):
        """Xem nhân viên liên quan"""
        self.ensure_one()
        if not self.related_nhan_vien_ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Không có nhân viên liên quan'),
                    'message': 'AI không đề cập đến nhân viên nào trong tin nhắn này',
                    'type': 'warning',
                }
            }

        return {
            'name': _('Nhân viên liên quan'),
            'type': 'ir.actions.act_window',
            'res_model': 'nhan_vien',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.related_nhan_vien_ids.ids)],
            'context': {'create': False},
        }

    # ============================================================================
    # CLEANUP METHODS
    # ============================================================================

    @api.model
    def cleanup_old_history(self, days=30):
        """Xóa lịch sử chat cũ (quá 30 ngày)"""
        from datetime import datetime, timedelta

        cutoff_date = datetime.now() - timedelta(days=days)
        old_records = self.search([
            ('create_date', '<', cutoff_date.strftime('%Y-%m-%d %H:%M:%S'))
        ])

        count = len(old_records)
        old_records.unlink()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Dọn dẹp hoàn tất'),
                'message': f'Đã xóa {count} tin nhắn chat cũ',
                'type': 'success',
            }
        }

    # ============================================================================
    # ANALYTICS METHODS
    # ============================================================================

    @api.model
    def get_chat_statistics(self):
        """Thống kê chat trong tháng này"""
        from datetime import datetime

        # Lấy ngày đầu tháng
        now = datetime.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Thống kê
        total_messages = self.search_count([
            ('create_date', '>=', start_of_month)
        ])

        user_messages = self.search_count([
            ('create_date', '>=', start_of_month),
            ('message_type', '=', 'user')
        ])

        ai_messages = self.search_count([
            ('create_date', '>=', start_of_month),
            ('message_type', '=', 'assistant')
        ])

        # Top users
        top_users = self.env['res.users'].search([])
        user_stats = []

        for user in top_users:
            count = self.search_count([
                ('create_date', '>=', start_of_month),
                ('user_id', '=', user.id)
            ])
            if count > 0:
                user_stats.append({
                    'user': user.name,
                    'messages': count,
                })

        user_stats.sort(key=lambda x: x['messages'], reverse=True)

        return {
            'total_messages': total_messages,
            'user_messages': user_messages,
            'ai_messages': ai_messages,
            'top_users': user_stats[:5],  # Top 5 users
            'period': f"{start_of_month.strftime('%Y-%m-%d')} đến {now.strftime('%Y-%m-%d')}",
        }