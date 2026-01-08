# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class AIConfig(models.Model):
    """Cấu hình AI Chatbot"""
    _name = 'ai.config'
    _description = 'Cấu hình AI Chatbot'
    _rec_name = 'name'

    name = fields.Char('Tên cấu hình', required=True, default='AI Chatbot Config')
    is_active = fields.Boolean('Kích hoạt', default=True)

    # OpenRouter API Configuration
    openrouter_api_key = fields.Char(
        'OpenRouter API Key',
        help='API Key từ OpenRouter để truy cập các AI models'
    )
    openrouter_model = fields.Char(
        'Model Name',
        default='xiaomi/mimo-v2-flash:free',
        help='Tên model AI sử dụng (vd: xiaomi/mimo-v2-flash:free)'
    )

    # Chat Settings
    max_conversation_length = fields.Integer(
        'Độ dài tối đa cuộc trò chuyện',
        default=50,
        help='Số tin nhắn tối đa lưu trong lịch sử'
    )
    max_response_tokens = fields.Integer(
        'Số tokens tối đa phản hồi',
        default=1000,
        help='Giới hạn độ dài phản hồi của AI'
    )

    temperature = fields.Float(
        'Temperature',
        default=0.7,
        help='Độ sáng tạo của AI (0.0 = nhất quán, 2.0 = sáng tạo)'
    )

    # System Prompt
    system_prompt = fields.Text(
        'System Prompt',
        default="""
Bạn là trợ lý AI thông minh cho hệ thống Quản lý Tài sản và Nhân sự.

Nhiệm vụ của bạn:
1. Trả lời các câu hỏi về dữ liệu trong hệ thống
2. Giúp tra cứu thông tin tài sản, nhân viên, phòng họp
3. Đưa ra gợi ý về quản lý tài sản hiệu quả
4. Hỗ trợ phân tích dữ liệu và thống kê
5. Tư vấn về bảo trì, khấu hao tài sản

Hướng dẫn:
- Luôn trả lời bằng tiếng Việt
- Nếu cần thông tin cụ thể, hãy yêu cầu làm rõ
- Sử dụng dữ liệu thực tế từ hệ thống khi trả lời
- Giữ giọng điệu thân thiện, chuyên nghiệp
        """.strip()
    )

    # Features
    enable_asset_search = fields.Boolean('Cho phép tìm kiếm tài sản', default=True)
    enable_employee_search = fields.Boolean('Cho phép tìm kiếm nhân viên', default=True)
    enable_room_booking = fields.Boolean('Cho phép đặt phòng', default=True)
    enable_analytics = fields.Boolean('Cho phép phân tích dữ liệu', default=True)

    # Security
    allowed_user_groups = fields.Many2many(
        'res.groups',
        string='Nhóm người dùng được phép',
        help='Các nhóm người dùng được phép sử dụng AI Chatbot'
    )

    # Statistics
    total_conversations = fields.Integer(
        'Tổng số cuộc trò chuyện',
        compute='_compute_statistics',
        store=False
    )
    total_messages = fields.Integer(
        'Tổng số tin nhắn',
        compute='_compute_statistics',
        store=False
    )
    avg_response_time = fields.Float(
        'Thời gian phản hồi TB (giây)',
        compute='_compute_statistics',
        store=False,
        digits=(4, 2)
    )

    @api.depends('is_active')
    def _compute_statistics(self):
        """Tính toán thống kê"""
        for record in self:
            if not record.is_active:
                record.total_conversations = 0
                record.total_messages = 0
                record.avg_response_time = 0.0
                continue

            # Đếm conversations unique
            conversations = self.env['ai.chat.history'].search([]).mapped('conversation_id')
            record.total_conversations = len(set(conversations))

            # Tổng messages
            record.total_messages = self.env['ai.chat.history'].search_count([])

            # Trung bình response time
            response_times = self.env['ai.chat.history'].search([
                ('message_type', '=', 'assistant'),
                ('response_time', '>', 0)
            ]).mapped('response_time')

            if response_times:
                record.avg_response_time = sum(response_times) / len(response_times)
            else:
                record.avg_response_time = 0.0

    @api.model
    def get_active_config(self):
        """Lấy cấu hình AI đang active"""
        config = self.search([('is_active', '=', True)], limit=1)
        if not config:
            # Tạo config mặc định nếu chưa có
            config = self.create({
                'name': 'Default AI Config',
                'is_active': True,
            })
        return config

    def action_test_connection(self):
        """Test kết nối với OpenRouter API"""
        self.ensure_one()

        if not self.openrouter_api_key:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Thiếu API Key'),
                    'message': 'Vui lòng cấu hình OpenRouter API Key trước',
                    'type': 'warning',
                }
            }

        try:
            import requests

            headers = {
                'Authorization': f'Bearer {self.openrouter_api_key}',
                'Content-Type': 'application/json',
            }

            # Test với model list endpoint
            response = requests.get(
                'https://openrouter.ai/api/v1/models',
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Kết nối thành công'),
                        'message': f'API hoạt động bình thường. Model: {self.openrouter_model}',
                        'type': 'success',
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Kết nối thất bại'),
                        'message': f'Lỗi {response.status_code}: {response.text[:100]}',
                        'type': 'danger',
                    }
                }

        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Lỗi kết nối'),
                    'message': f'Không thể kết nối: {str(e)}',
                    'type': 'danger',
                }
            }

    def action_view_chat_history(self):
        """Xem lịch sử chat"""
        self.ensure_one()

        return {
            'name': _('Lịch sử Chat AI'),
            'type': 'ir.actions.act_window',
            'res_model': 'ai.chat.history',
            'view_mode': 'tree,form',
            'context': {'create': False},
        }

    def action_cleanup_history(self):
        """Dọn dẹp lịch sử chat cũ"""
        self.ensure_one()

        return self.env['ai.chat.history'].cleanup_old_history(30)