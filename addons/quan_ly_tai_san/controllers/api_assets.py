# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


class AssetAPIController(http.Controller):
    """API endpoints for asset search and stats"""

    def _check_api_key(self, api_key):
        valid_keys = ['demo-api-key-12345', 'test-key', 'ai-chat-key']
        return api_key in valid_keys

    @http.route('/api/assets', type='json', auth='public', methods=['GET', 'POST'], csrf=False, cors='*')
    def assets(self, **kwargs):
        try:
            api_key = request.httprequest.headers.get('X-API-Key')
            if api_key and not self._check_api_key(api_key) and not request.env.uid:
                return {'success': False, 'status': 401, 'message': 'Unauthorized'}

            q = (kwargs.get('q') or '').strip()
            loai_id = kwargs.get('loai_id')
            trang_thai = kwargs.get('trang_thai')
            limit = int(kwargs.get('limit', 200))

            domain = []
            if q:
                domain += ['|', ('ten_tai_san', 'ilike', q), ('ma_tai_san', 'ilike', q)]
            if loai_id:
                domain += [('loai_tai_san_id', '=', int(loai_id))]
            if trang_thai:
                domain += [('trang_thai', '=', trang_thai)]

            assets = request.env['tai_san'].sudo().search(domain, limit=limit)
            results = []
            for a in assets:
                results.append({
                    'id': a.id,
                    'ma_tai_san': a.ma_tai_san,
                    'ten_tai_san': a.ten_tai_san,
                    'so_serial': getattr(a, 'so_serial', '') or '',
                    'ngay_mua': getattr(a, 'ngay_mua', None),
                    'ngay_het_han_bao_hanh': getattr(a, 'ngay_het_han_bao_hanh', None),
                    'gia_tien_mua': getattr(a, 'gia_tien_mua', 0),
                    'gia_tri_hien_tai': getattr(a, 'gia_tri_hien_tai', 0),
                    'trang_thai': getattr(a, 'trang_thai', ''),
                    'vi_tri': getattr(a.vi_tri_hien_tai_id, 'ten_vi_tri', '') if getattr(a, 'vi_tri_hien_tai_id', None) else '',
                    'loai_tai_san': getattr(a.loai_tai_san_id, 'ten_loai_tai_san', '') if getattr(a, 'loai_tai_san_id', None) else '',
                    'nha_cung_cap': getattr(a.nha_cung_cap_id, 'name', '') if getattr(a, 'nha_cung_cap_id', None) else '',
                })

            return {'success': True, 'status': 200, 'data': {'count': len(results), 'assets': results}}

        except Exception as e:
            _logger.exception('Asset API error')
            return {'success': False, 'status': 500, 'message': str(e)}

