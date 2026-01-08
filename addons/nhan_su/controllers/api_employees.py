# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class EmployeeAPIController(http.Controller):
    """API endpoints for nhan_su (employees)"""

    def _check_api_key(self, api_key):
        valid_keys = ['demo-api-key-12345', 'test-key', 'ai-chat-key']
        return api_key in valid_keys

    @http.route('/api/employees', type='json', auth='public', methods=['GET', 'POST'], csrf=False, cors='*')
    def employees(self, **kwargs):
        try:
            api_key = request.httprequest.headers.get('X-API-Key')
            if api_key and not self._check_api_key(api_key) and not request.env.uid:
                return {'success': False, 'status': 401, 'message': 'Unauthorized'}

            q = (kwargs.get('q') or '').strip()
            limit = int(kwargs.get('limit', 50))

            domain = []
            if q:
                domain = ['|', ('ho_va_ten', 'ilike', q), ('ma_dinh_danh', 'ilike', q)]

            employees = request.env['nhan_vien'].sudo().search(domain, limit=limit)
            results = []
            for e in employees:
                results.append({
                    'id': e.id,
                    'ma_dinh_danh': e.ma_dinh_danh,
                    'ho_va_ten': e.ho_va_ten,
                    'email': e.email or '',
                    'so_dien_thoai': e.so_dien_thoai or '',
                    'tuoi': e.tuoi or 0,
                    'chuc_vu': e.lich_su_cong_tac_ids and (e.lich_su_cong_tac_ids[:1].chuc_vu_id.ten_chuc_vu) or 'N/A',
                })

            return {'success': True, 'status': 200, 'data': {'count': len(results), 'employees': results}}

        except Exception as e:
            _logger.exception('Employee API error')
            return {'success': False, 'status': 500, 'message': str(e)}

