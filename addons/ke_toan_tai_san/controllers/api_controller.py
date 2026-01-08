# -*- coding: utf-8 -*-
"""
REST API Controller cho Hệ thống Quản lý Tài sản

Endpoints:
    GET  /api/tai_san           - Danh sách tài sản
    GET  /api/tai_san/<id>      - Chi tiết tài sản
    GET  /api/phong_hop         - Danh sách phòng họp
    GET  /api/phong_hop/<id>    - Chi tiết phòng họp
    GET  /api/nhan_vien         - Danh sách nhân viên
    POST /api/dat_phong         - Đặt phòng
    GET  /api/thong_ke          - Thống kê tổng quan

Authentication: Basic Auth hoặc API Key
"""

from odoo import http
from odoo.http import request, Response
import json
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


class TaiSanAPIController(http.Controller):
    """REST API Controller cho Quản lý Tài sản"""
    
    # ============================================================================
    # AUTHENTICATION & HELPERS
    # ============================================================================
    
    def _check_api_key(self, api_key):
        """
        Kiểm tra API Key (Đơn giản - cho demo)
        Production nên dùng OAuth2 hoặc JWT
        """
        # TODO: Lưu API keys trong database
        # Hiện tại hardcode cho demo
        valid_keys = ['demo-api-key-12345', 'test-key']
        return api_key in valid_keys
    
    def _authenticate(self):
        """Xác thực request"""
        # Lấy API key từ header
        api_key = request.httprequest.headers.get('X-API-Key')
        
        if api_key and self._check_api_key(api_key):
            return True
        
        # Fallback: Kiểm tra user đã login
        if request.env.uid:
            return True
        
        return False
    
    def _json_response(self, data, status=200, message=None):
        """Tạo JSON response chuẩn"""
        response_data = {
            'success': status == 200,
            'status': status,
            'data': data,
        }
        
        if message:
            response_data['message'] = message
        
        return Response(
            json.dumps(response_data, ensure_ascii=False, default=str),
            status=status,
            mimetype='application/json',
            headers={'Content-Type': 'application/json; charset=utf-8'}
        )
    
    def _error_response(self, message, status=400):
        """Tạo error response"""
        return self._json_response(None, status=status, message=message)
    
    # ============================================================================
    # ENDPOINTS - TÀI SẢN
    # ============================================================================
    
    @http.route('/api/tai_san', type='http', auth='public', methods=['GET'], csrf=False, cors='*')
    def get_tai_san_list(self, **kwargs):
        """
        Lấy danh sách tài sản
        
        Query params:
            - limit: Số lượng (default: 100)
            - offset: Bắt đầu từ (default: 0)
            - trang_thai: Lọc theo trạng thái (LuuTru, Muon, BaoTri, Hong)
            - loai_id: Lọc theo loại tài sản
        """
        try:
            if not self._authenticate():
                return self._error_response('Unauthorized - Missing or invalid API key', 401)
            
            # Parse params
            limit = int(kwargs.get('limit', 100))
            offset = int(kwargs.get('offset', 0))
            trang_thai = kwargs.get('trang_thai')
            loai_id = kwargs.get('loai_id')
            
            # Build domain
            domain = []
            if trang_thai:
                domain.append(('trang_thai', '=', trang_thai))
            if loai_id:
                domain.append(('loai_tai_san_id', '=', int(loai_id)))
            
            # Query
            tai_san_records = request.env['tai_san'].sudo().search(
                domain, 
                limit=limit, 
                offset=offset,
                order='ma_tai_san'
            )
            
            # Format response
            tai_san_list = []
            for ts in tai_san_records:
                tai_san_list.append({
                    'id': ts.id,
                    'ma_tai_san': ts.ma_tai_san,
                    'ten_tai_san': ts.ten_tai_san,
                    'so_serial': ts.so_serial,
                    'loai_tai_san': ts.loai_tai_san_id.ten_loai_tai_san if ts.loai_tai_san_id else None,
                    'trang_thai': ts.trang_thai,
                    'gia_tien_mua': ts.gia_tien_mua,
                    'gia_tri_hien_tai': ts.gia_tri_hien_tai,
                    'vi_tri': ts.vi_tri_hien_tai_id.ten_vi_tri if ts.vi_tri_hien_tai_id else None,
                    'nha_cung_cap': ts.nha_cung_cap_id.ten_nha_cung_cap if ts.nha_cung_cap_id else None,
                })
            
            return self._json_response({
                'count': len(tai_san_list),
                'total': request.env['tai_san'].sudo().search_count(domain),
                'items': tai_san_list
            })
            
        except Exception as e:
            _logger.error(f"API Error: {e}")
            return self._error_response(str(e), 500)
    
    @http.route('/api/tai_san/<int:tai_san_id>', type='http', auth='public', methods=['GET'], csrf=False, cors='*')
    def get_tai_san_detail(self, tai_san_id, **kwargs):
        """Lấy thông tin chi tiết 1 tài sản"""
        try:
            if not self._authenticate():
                return self._error_response('Unauthorized', 401)
            
            ts = request.env['tai_san'].sudo().browse(tai_san_id)
            
            if not ts.exists():
                return self._error_response(f'Tài sản {tai_san_id} không tồn tại', 404)
            
            # Chi tiết đầy đủ
            data = {
                'id': ts.id,
                'ma_tai_san': ts.ma_tai_san,
                'ten_tai_san': ts.ten_tai_san,
                'so_serial': ts.so_serial,
                'ngay_mua': ts.ngay_mua.isoformat() if ts.ngay_mua else None,
                'gia_tien_mua': ts.gia_tien_mua,
                'gia_tri_hien_tai': ts.gia_tri_hien_tai,
                'trang_thai': ts.trang_thai,
                'loai_tai_san': {
                    'id': ts.loai_tai_san_id.id,
                    'ma': ts.loai_tai_san_id.ma_loai_tai_san,
                    'ten': ts.loai_tai_san_id.ten_loai_tai_san,
                } if ts.loai_tai_san_id else None,
                'vi_tri': {
                    'id': ts.vi_tri_hien_tai_id.id,
                    'ma': ts.vi_tri_hien_tai_id.ma_vi_tri,
                    'ten': ts.vi_tri_hien_tai_id.ten_vi_tri,
                } if ts.vi_tri_hien_tai_id else None,
                'nha_cung_cap': {
                    'id': ts.nha_cung_cap_id.id,
                    'ma': ts.nha_cung_cap_id.ma_nha_cung_cap,
                    'ten': ts.nha_cung_cap_id.ten_nha_cung_cap,
                } if ts.nha_cung_cap_id else None,
                'nguoi_quan_ly': {
                    'id': ts.quan_ly_id.id,
                    'ma': ts.quan_ly_id.ma_dinh_danh,
                    'ten': ts.quan_ly_id.ho_va_ten,
                } if ts.quan_ly_id else None,
                'lich_su_bao_tri': [
                    {
                        'ngay': ls.ngay_bao_tri.isoformat() if ls.ngay_bao_tri else None,
                        'chi_phi': ls.chi_phi,
                        'ghi_chu': ls.ghi_chu,
                    } for ls in ts.lich_su_bao_tri_ids
                ],
                'so_lan_muon': len(ts.lich_su_su_dung_ids),
            }
            
            return self._json_response(data)
            
        except Exception as e:
            _logger.error(f"API Error: {e}")
            return self._error_response(str(e), 500)
    
    # ============================================================================
    # ENDPOINTS - PHÒNG HỌP
    # ============================================================================
    
    @http.route('/api/phong_hop', type='http', auth='public', methods=['GET'], csrf=False, cors='*')
    def get_phong_hop_list(self, **kwargs):
        """
        Lấy danh sách phòng họp
        
        Query params:
            - trang_thai: Lọc theo trạng thái (san_sang, dang_su_dung, bao_tri)
            - ngay: Kiểm tra phòng trống vào ngày (YYYY-MM-DD)
        """
        try:
            if not self._authenticate():
                return self._error_response('Unauthorized', 401)
            
            domain = []
            trang_thai = kwargs.get('trang_thai')
            if trang_thai:
                domain.append(('trang_thai', '=', trang_thai))
            
            phong_hop_records = request.env['phong_hop'].sudo().search(domain, order='ma_phong')
            
            phong_hop_list = []
            for ph in phong_hop_records:
                phong_hop_list.append({
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
            
            return self._json_response({
                'count': len(phong_hop_list),
                'items': phong_hop_list
            })
            
        except Exception as e:
            _logger.error(f"API Error: {e}")
            return self._error_response(str(e), 500)
    
    @http.route('/api/phong_hop/<int:phong_id>', type='http', auth='public', methods=['GET'], csrf=False, cors='*')
    def get_phong_hop_detail(self, phong_id, **kwargs):
        """Lấy thông tin chi tiết phòng họp"""
        try:
            if not self._authenticate():
                return self._error_response('Unauthorized', 401)
            
            ph = request.env['phong_hop'].sudo().browse(phong_id)
            
            if not ph.exists():
                return self._error_response(f'Phòng họp {phong_id} không tồn tại', 404)
            
            data = {
                'id': ph.id,
                'ma_phong': ph.ma_phong,
                'ten_phong': ph.ten_phong,
                'suc_chua': ph.suc_chua,
                'dien_tich': ph.dien_tich,
                'trang_thai': ph.trang_thai,
                'vi_tri': {
                    'id': ph.vi_tri_id.id,
                    'ten': ph.vi_tri_id.ten_vi_tri,
                } if ph.vi_tri_id else None,
                'mo_ta': ph.mo_ta,
                'thiet_bi': [
                    {
                        'id': tb.id,
                        'ma': tb.ma_tai_san,
                        'ten': tb.ten_tai_san,
                    } for tb in ph.thiet_bi_ids
                ],
                'lich_dat_phong': [
                    {
                        'id': dp.id,
                        'ma': dp.ma_dat_phong,
                        'tieu_de': dp.tieu_de,
                        'ngay_bat_dau': dp.ngay_bat_dau.isoformat() if dp.ngay_bat_dau else None,
                        'ngay_ket_thuc': dp.ngay_ket_thuc.isoformat() if dp.ngay_ket_thuc else None,
                        'trang_thai': dp.trang_thai,
                    } for dp in ph.dat_phong_ids[:10]  # Lấy 10 booking gần nhất
                ],
            }
            
            return self._json_response(data)
            
        except Exception as e:
            _logger.error(f"API Error: {e}")
            return self._error_response(str(e), 500)
    
    # ============================================================================
    # ENDPOINTS - NHÂN VIÊN
    # ============================================================================
    
    @http.route('/api/nhan_vien', type='http', auth='public', methods=['GET'], csrf=False, cors='*')
    def get_nhan_vien_list(self, **kwargs):
        """Lấy danh sách nhân viên"""
        try:
            if not self._authenticate():
                return self._error_response('Unauthorized', 401)
            
            limit = int(kwargs.get('limit', 100))
            offset = int(kwargs.get('offset', 0))
            
            nhan_vien_records = request.env['nhan_vien'].sudo().search(
                [], 
                limit=limit, 
                offset=offset,
                order='ma_dinh_danh'
            )
            
            nhan_vien_list = []
            for nv in nhan_vien_records:
                nhan_vien_list.append({
                    'id': nv.id,
                    'ma_dinh_danh': nv.ma_dinh_danh,
                    'ho_va_ten': nv.ho_va_ten,
                    'email': nv.email,
                    'so_dien_thoai': nv.so_dien_thoai,
                })
            
            return self._json_response({
                'count': len(nhan_vien_list),
                'items': nhan_vien_list
            })
            
        except Exception as e:
            _logger.error(f"API Error: {e}")
            return self._error_response(str(e), 500)
    
    # ============================================================================
    # ENDPOINTS - ĐẶT PHÒNG
    # ============================================================================
    
    @http.route('/api/dat_phong', type='http', auth='public', methods=['POST'], csrf=False, cors='*')
    def create_dat_phong(self, **kwargs):
        """
        Tạo đặt phòng mới
        
        Body (JSON):
        {
            "phong_hop_id": 1,
            "nguoi_dat_id": 2,
            "tieu_de": "Họp team",
            "ngay_bat_dau": "2026-01-10 09:00:00",
            "ngay_ket_thuc": "2026-01-10 11:00:00",
            "so_nguoi_tham_gia": 10,
            "noi_dung": "Sprint planning"
        }
        """
        try:
            if not self._authenticate():
                return self._error_response('Unauthorized', 401)
            
            # Parse JSON body
            data = json.loads(request.httprequest.data.decode('utf-8'))
            
            # Validate required fields
            required_fields = ['phong_hop_id', 'nguoi_dat_id', 'tieu_de', 'ngay_bat_dau', 'ngay_ket_thuc']
            for field in required_fields:
                if field not in data:
                    return self._error_response(f'Thiếu trường bắt buộc: {field}', 400)
            
            # Kiểm tra phòng tồn tại và available
            phong = request.env['phong_hop'].sudo().browse(data['phong_hop_id'])
            if not phong.exists():
                return self._error_response(f"Phòng họp {data['phong_hop_id']} không tồn tại", 404)
            
            # Tạo đặt phòng
            dat_phong = request.env['dat_phong'].sudo().create({
                'phong_hop_id': data['phong_hop_id'],
                'nguoi_dat_id': data['nguoi_dat_id'],
                'tieu_de': data['tieu_de'],
                'ngay_bat_dau': data['ngay_bat_dau'],
                'ngay_ket_thuc': data['ngay_ket_thuc'],
                'so_nguoi_tham_gia': data.get('so_nguoi_tham_gia', 0),
                'noi_dung': data.get('noi_dung', ''),
                'trang_thai': 'cho_xac_nhan',
            })
            
            _logger.info(f"API: Đã tạo đặt phòng {dat_phong.ma_dat_phong}")
            
            return self._json_response({
                'id': dat_phong.id,
                'ma_dat_phong': dat_phong.ma_dat_phong,
                'trang_thai': dat_phong.trang_thai,
            }, status=201, message='Đặt phòng thành công')
            
        except Exception as e:
            _logger.error(f"API Error: {e}")
            return self._error_response(str(e), 500)
    
    # ============================================================================
    # ENDPOINTS - THỐNG KÊ
    # ============================================================================
    
    @http.route('/api/thong_ke', type='http', auth='public', methods=['GET'], csrf=False, cors='*')
    def get_thong_ke(self, **kwargs):
        """Lấy thống kê tổng quan hệ thống"""
        try:
            if not self._authenticate():
                return self._error_response('Unauthorized', 401)
            
            env = request.env.sudo()
            
            data = {
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
                    'hom_nay': env['dat_phong'].search_count([
                        ('ngay_bat_dau', '>=', datetime.now().strftime('%Y-%m-%d 00:00:00')),
                        ('ngay_bat_dau', '<=', datetime.now().strftime('%Y-%m-%d 23:59:59')),
                    ]),
                    'cho_xac_nhan': env['dat_phong'].search_count([('trang_thai', '=', 'cho_xac_nhan')]),
                },
            }
            
            return self._json_response(data)
            
        except Exception as e:
            _logger.error(f"API Error: {e}")
            return self._error_response(str(e), 500)
    
    # ============================================================================
    # ENDPOINT - API INFO
    # ============================================================================
    
    @http.route('/api/info', type='http', auth='public', methods=['GET'], csrf=False, cors='*')
    def api_info(self):
        """Thông tin về API"""
        return self._json_response({
            'name': 'Odoo Asset Management API',
            'version': '1.0.0',
            'endpoints': [
                {'method': 'GET', 'path': '/api/tai_san', 'description': 'Danh sách tài sản'},
                {'method': 'GET', 'path': '/api/tai_san/<id>', 'description': 'Chi tiết tài sản'},
                {'method': 'GET', 'path': '/api/phong_hop', 'description': 'Danh sách phòng họp'},
                {'method': 'GET', 'path': '/api/phong_hop/<id>', 'description': 'Chi tiết phòng họp'},
                {'method': 'GET', 'path': '/api/nhan_vien', 'description': 'Danh sách nhân viên'},
                {'method': 'POST', 'path': '/api/dat_phong', 'description': 'Đặt phòng mới'},
                {'method': 'GET', 'path': '/api/thong_ke', 'description': 'Thống kê tổng quan'},
            ],
            'authentication': {
                'method': 'API Key',
                'header': 'X-API-Key',
                'demo_key': 'demo-api-key-12345',
            }
        })
