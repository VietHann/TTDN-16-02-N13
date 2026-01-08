# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import logging
import json
from datetime import datetime

_logger = logging.getLogger(__name__)


class KeToanAPIHelper(http.Controller):
    """Helper APIs for AI to call across modules"""

    def _check_api_key(self, api_key):
        valid_keys = ['demo-api-key-12345', 'test-key', 'ai-chat-key']
        return api_key in valid_keys

    def _collect_system_data(self):
        """Thu thập dữ liệu tổng hợp từ tất cả các API trong hệ thống"""
        try:
            env = request.env.sudo()
            data = {
                'timestamp': datetime.now().isoformat(),
                'nhan_su': {},
                'quan_ly_tai_san': {},
                'ke_toan_tai_san': {},
                'thong_ke_tong_quan': {}
            }

            # 1. Thu thập dữ liệu nhân sự
            try:
                nhan_vien_records = env['nhan_vien'].search([], limit=100)
                nhan_vien_data = []
                for nv in nhan_vien_records:
                    # Lấy chức vụ từ lịch sử công tác gần nhất
                    chuc_vu = 'N/A'
                    try:
                        latest_cong_tac = nv.lich_su_cong_tac_ids.sorted(key=lambda x: x.ngay_bat_dau, reverse=True)[:1]
                        if latest_cong_tac and latest_cong_tac.chuc_vu_id:
                            chuc_vu = latest_cong_tac.chuc_vu_id.ten_chuc_vu
                    except:
                        pass

                    nhan_vien_data.append({
                        'id': nv.id,
                        'ma_dinh_danh': nv.ma_dinh_danh,
                        'ho_va_ten': nv.ho_va_ten,
                        'email': nv.email or '',
                        'so_dien_thoai': nv.so_dien_thoai or '',
                        'tuoi': nv.tuoi or 0,
                        'chuc_vu': chuc_vu,
                    })

                data['nhan_su'] = {
                    'count': len(nhan_vien_data),
                    'nhan_vien': nhan_vien_data
                }
            except Exception as e:
                _logger.warning(f"Lỗi thu thập dữ liệu nhân sự: {e}")
                data['nhan_su'] = {'error': str(e)}

            # 2. Thu thập dữ liệu quản lý tài sản
            try:
                tai_san_records = env['tai_san'].search([], limit=200)
                tai_san_data = []
                for ts in tai_san_records:
                    tai_san_data.append({
                        'id': ts.id,
                        'ma_tai_san': ts.ma_tai_san,
                        'ten_tai_san': ts.ten_tai_san,
                        'so_serial': getattr(ts, 'so_serial', '') or '',
                        'ngay_mua': getattr(ts, 'ngay_mua', None),
                        'gia_tien_mua': getattr(ts, 'gia_tien_mua', 0),
                        'gia_tri_hien_tai': getattr(ts, 'gia_tri_hien_tai', 0),
                        'trang_thai': getattr(ts, 'trang_thai', ''),
                        'vi_tri': getattr(ts.vi_tri_hien_tai_id, 'ten_vi_tri', '') if getattr(ts, 'vi_tri_hien_tai_id', None) else '',
                        'loai_tai_san': getattr(ts.loai_tai_san_id, 'ten_loai_tai_san', '') if getattr(ts, 'loai_tai_san_id', None) else '',
                        'nha_cung_cap': getattr(ts.nha_cung_cap_id, 'name', '') if getattr(ts, 'nha_cung_cap_id', None) else '',
                    })

                data['quan_ly_tai_san'] = {
                    'count': len(tai_san_data),
                    'tai_san': tai_san_data
                }
            except Exception as e:
                _logger.warning(f"Lỗi thu thập dữ liệu tài sản: {e}")
                data['quan_ly_tai_san'] = {'error': str(e)}

            # 3. Thu thập dữ liệu phòng họp và thống kê từ ke_toan_tai_san
            try:
                phong_hop_records = env['phong_hop'].search([])
                phong_hop_data = []
                for ph in phong_hop_records:
                    phong_hop_data.append({
                        'id': ph.id,
                        'ma_phong': ph.ma_phong,
                        'ten_phong': ph.ten_phong,
                        'suc_chua': ph.suc_chua,
                        'dien_tich': ph.dien_tich,
                        'trang_thai': ph.trang_thai,
                        'vi_tri': ph.vi_tri_id.ten_vi_tri if ph.vi_tri_id else None,
                        'mo_ta': ph.mo_ta,
                        'so_thiet_bi': len(ph.thiet_bi_ids),
                    })

                data['ke_toan_tai_san'] = {
                    'count_phong_hop': len(phong_hop_data),
                    'phong_hop': phong_hop_data
                }
            except Exception as e:
                _logger.warning(f"Lỗi thu thập dữ liệu phòng họp: {e}")
                data['ke_toan_tai_san'] = {'error': str(e)}

            # 4. Thống kê tổng quan
            try:
                data['thong_ke_tong_quan'] = {
                    'tai_san': {
                        'tong_so': env['tai_san'].search_count([]),
                        'dang_luu_tru': env['tai_san'].search_count([('trang_thai', '=', 'LuuTru')]),
                        'dang_muon': env['tai_san'].search_count([('trang_thai', '=', 'Muon')]),
                        'dang_bao_tri': env['tai_san'].search_count([('trang_thai', '=', 'BaoTri')]),
                        'bi_hong': env['tai_san'].search_count([('trang_thai', '=', 'Hong')]),
                        'tong_gia_tri': sum(env['tai_san'].search([]).mapped('gia_tri_hien_tai')),
                    },
                    'phong_hop': {
                        'tong_so': env['phong_hop'].search_count([]),
                        'san_sang': env['phong_hop'].search_count([('trang_thai', '=', 'san_sang')]),
                        'dang_su_dung': env['phong_hop'].search_count([('trang_thai', '=', 'dang_su_dung')]),
                    },
                    'nhan_su': {
                        'tong_so': env['nhan_vien'].search_count([]),
                    },
                    'dat_phong': {
                        'cho_xac_nhan': env['dat_phong'].search_count([('trang_thai', '=', 'cho_xac_nhan')]),
                    },
                }
            except Exception as e:
                _logger.warning(f"Lỗi tạo thống kê tổng quan: {e}")
                data['thong_ke_tong_quan'] = {'error': str(e)}

            return data

        except Exception as e:
            _logger.error(f"Lỗi thu thập dữ liệu hệ thống: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}

    @http.route('/api/ai/system_data', type='json', auth='public', methods=['GET'], csrf=False, cors='*')
    def get_system_data_for_ai(self, **kwargs):
        """API endpoint để lấy toàn bộ dữ liệu hệ thống cho AI"""
        try:
            api_key = request.httprequest.headers.get('X-API-Key')
            if api_key and not self._check_api_key(api_key) and not request.env.uid:
                return {'success': False, 'status': 401, 'message': 'Unauthorized'}

            data = self._collect_system_data()

            return {
                'success': True,
                'status': 200,
                'data': data,
                'message': 'Dữ liệu hệ thống cho AI'
            }

        except Exception as e:
            _logger.error(f"API system_data error: {e}")
            return {'success': False, 'status': 500, 'message': str(e)}

    @http.route('/api/ai/asset_search', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def ai_asset_search(self, **kwargs):
        try:
            api_key = request.httprequest.headers.get('X-API-Key')
            if api_key and not self._check_api_key(api_key) and not request.env.uid:
                return {'success': False, 'status': 401, 'message': 'Unauthorized'}

            # Forward request to internal asset API
            q = kwargs.get('q') or kwargs.get('message') or ''
            res = request.env['ir.http'].sudo()._dispatch('/api/assets', 'POST', kwargs={'q': q})
            # _dispatch returns a werkzeug response; instead call model directly for reliability
            assets = request.env['tai_san'].sudo().search([('ten_tai_san', 'ilike', q)], limit=50)
            data = []
            for a in assets:
                data.append({
                    'id': a.id,
                    'ma_tai_san': a.ma_tai_san,
                    'ten_tai_san': a.ten_tai_san,
                    'trang_thai': a.trang_thai,
                    'vi_tri': getattr(a.vi_tri_hien_tai_id, 'ten_vi_tri', '') if getattr(a, 'vi_tri_hien_tai_id', None) else ''
                })
            return {'success': True, 'status': 200, 'data': {'count': len(data), 'assets': data}}
        except Exception as e:
            _logger.exception('ai_asset_search error')
            return {'success': False, 'status': 500, 'message': str(e)}

