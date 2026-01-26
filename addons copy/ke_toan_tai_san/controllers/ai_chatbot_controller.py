# -*- coding: utf-8 -*-
"""
AI Chatbot Controller cho Hệ thống Quản lý Tài sản
Sử dụng OpenRouter API với model xiaomi/mimo-v2-flash:free

Endpoints:
    POST /api/ai/chat         - Chat với AI
    GET  /api/ai/history      - Lịch sử chat
    POST /api/ai/clear        - Xóa lịch sử chat

Authentication: API Key hoặc user login
"""

import requests
import json
import logging
from datetime import datetime
from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)


class AIChatbotController(http.Controller):
    """AI Chatbot Controller sử dụng OpenRouter API"""

    # ============================================================================
    # CONFIGURATION
    # ============================================================================

    OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
    MODEL_NAME = "xiaomi/mimo-v2-flash:free"

    def _get_openrouter_config(self):
        """Lấy cấu hình OpenRouter từ ai.config model"""
        try:
            config = request.env['ai.config'].sudo().get_active_config()
            api_key = config.openrouter_api_key
            model = config.openrouter_model or self.MODEL_NAME

            if not api_key or api_key == "sk-or-v1-your-openrouter-api-key-here":
                # Fallback cho demo - sử dụng mock response
                api_key = None

            return {
                'api_key': api_key,
                'model': model,
            }
        except:
            # Fallback nếu model chưa được tạo
            return {
                'api_key': None,
                'model': self.MODEL_NAME,
            }

    # ============================================================================
    # AUTHENTICATION & HELPERS
    # ============================================================================

    def _authenticate(self):
        """Xác thực request - tái sử dụng từ API controller chính"""
        api_key = request.httprequest.headers.get('X-API-Key')

        if api_key and self._check_api_key(api_key):
            return True

        if request.env.uid:
            return True

        return False

    def _check_api_key(self, api_key):
        """Kiểm tra API Key"""
        valid_keys = ['demo-api-key-12345', 'test-key', 'ai-chat-key']
        return api_key in valid_keys

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
    # AI DATA ACCESS FUNCTIONS
    # ============================================================================

    def _get_system_context(self):
        """Lấy thông tin tổng quan về hệ thống để đưa vào context cho AI"""
        try:
            env = request.env
            context_parts = ["Hệ thống Quản lý Tài sản & Nhân sự"]

            # Thống kê tài sản
            try:
                tai_san_count = env['tai_san'].search_count([])
                context_parts.append(f"- Tài sản: {tai_san_count} tổng số")
            except:
                context_parts.append("- Tài sản: Chưa có dữ liệu")

            # Thống kê nhân sự
            try:
                nhan_vien_count = env['nhan_vien'].search_count([])
                context_parts.append(f"- Nhân viên: {nhan_vien_count} người")
            except:
                context_parts.append("- Nhân viên: Chưa có dữ liệu")

            # Thống kê phòng họp
            try:
                phong_hop_count = env['phong_hop'].search_count([])
                context_parts.append(f"- Phòng họp: {phong_hop_count} phòng")
            except:
                context_parts.append("- Phòng họp: Chưa có dữ liệu")

            return "\n".join(context_parts)

        except Exception as e:
            _logger.error(f"Lỗi lấy system context: {e}")
            return "Hệ thống Quản lý Tài sản và Nhân sự"

    def _search_tai_san(self, query, limit=5):
        """Tìm kiếm tài sản theo query"""
        try:
            env = request.env

            # Tìm theo tên hoặc mã tài sản
            domain = [
                '|',
                ('ten_tai_san', 'ilike', query),
                ('ma_tai_san', 'ilike', query)
            ]

            tai_san_records = env['tai_san'].search(domain, limit=limit)

            results = []
            for ts in tai_san_records:
                try:
                    results.append({
                        'id': ts.id,
                        'ma_tai_san': getattr(ts, 'ma_tai_san', f'TS-{ts.id}'),
                        'ten_tai_san': getattr(ts, 'ten_tai_san', f'Tài sản {ts.id}'),
                        'trang_thai': getattr(ts, 'trang_thai', 'N/A'),
                        'gia_tri_hien_tai': getattr(ts, 'gia_tri_hien_tai', 0),
                        'vi_tri': getattr(ts.vi_tri_hien_tai_id, 'ten_vi_tri', 'N/A') if getattr(ts, 'vi_tri_hien_tai_id', None) else 'N/A',
                    })
                except:
                    # Skip records with issues
                    continue

            return results

        except Exception as e:
            _logger.error(f"Lỗi tìm kiếm tài sản: {e}")
            return []

    def _search_nhan_vien(self, query, limit=5):
        """Tìm kiếm nhân viên theo query"""
        try:
            env = request.env

            domain = [
                '|',
                ('ho_va_ten', 'ilike', query),
                ('ma_dinh_danh', 'ilike', query)
            ]

            nhan_vien_records = env['nhan_vien'].search(domain, limit=limit)

            results = []
            for nv in nhan_vien_records:
                # Lấy chức vụ từ lịch sử công tác gần nhất
                chuc_vu = 'N/A'
                try:
                    latest_cong_tac = nv.lich_su_cong_tac_ids.sorted(key=lambda x: x.ngay_bat_dau, reverse=True)[:1]
                    if latest_cong_tac and latest_cong_tac.chuc_vu_id:
                        chuc_vu = latest_cong_tac.chuc_vu_id.ten_chuc_vu
                except:
                    pass

                results.append({
                    'id': nv.id,
                    'ma_dinh_danh': nv.ma_dinh_danh,
                    'ho_va_ten': nv.ho_va_ten,
                    'email': nv.email or 'N/A',
                    'chuc_vu': chuc_vu,
                })

            return results

        except Exception as e:
            _logger.error(f"Lỗi tìm kiếm nhân viên: {e}")
            return []

    def _build_context_from_system_data(self, system_data):
        """Chuyển đổi dữ liệu hệ thống thành context text cho AI"""
        try:
            context_parts = [
                "=== DỮ LIỆU HỆ THỐNG (Cập nhật: " + system_data.get('timestamp', 'N/A') + ") ==="
            ]

            # Thống kê tổng quan
            if 'thong_ke_tong_quan' in system_data and not system_data['thong_ke_tong_quan'].get('error'):
                tk = system_data['thong_ke_tong_quan']
                context_parts.append("\n--- THỐNG KÊ TỔNG QUAN ---")
                context_parts.append(f"Tài sản: {tk.get('tai_san', {}).get('tong_so', 0)} tổng số")
                context_parts.append(f"  - Đang lưu trữ: {tk.get('tai_san', {}).get('dang_luu_tru', 0)}")
                context_parts.append(f"  - Đang mượn: {tk.get('tai_san', {}).get('dang_muon', 0)}")
                context_parts.append(f"  - Đang bảo trì: {tk.get('tai_san', {}).get('dang_bao_tri', 0)}")
                context_parts.append(f"  - Bị hỏng: {tk.get('tai_san', {}).get('bi_hong', 0)}")
                context_parts.append(f"  - Tổng giá trị: {tk.get('tai_san', {}).get('tong_gia_tri', 0):,} VNĐ")

                context_parts.append(f"Nhân viên: {tk.get('nhan_su', {}).get('tong_so', 0)} người")
                context_parts.append(f"Phòng họp: {tk.get('phong_hop', {}).get('tong_so', 0)} phòng")
                context_parts.append(f"  - Sẵn sàng: {tk.get('phong_hop', {}).get('san_sang', 0)}")
                context_parts.append(f"  - Đang sử dụng: {tk.get('phong_hop', {}).get('dang_su_dung', 0)}")

                context_parts.append(f"Đặt phòng chờ xác nhận: {tk.get('dat_phong', {}).get('cho_xac_nhan', 0)}")

            # Thông tin nhân sự (tóm tắt)
            if 'nhan_su' in system_data and not system_data['nhan_su'].get('error'):
                ns = system_data['nhan_su']
                context_parts.append(f"\n--- NHÂN SỰ ({ns.get('count', 0)} nhân viên) ---")
                # Liệt kê một số nhân viên quan trọng (có chức vụ)
                nhan_vien_quan_trong = [nv for nv in ns.get('nhan_vien', []) if nv.get('chuc_vu') and nv['chuc_vu'] != 'N/A'][:10]
                for nv in nhan_vien_quan_trong:
                    context_parts.append(f"- {nv['ho_va_ten']} ({nv['chuc_vu']}) - {nv['ma_dinh_danh']}")

            # Thông tin tài sản (tóm tắt theo loại)
            if 'quan_ly_tai_san' in system_data and not system_data['quan_ly_tai_san'].get('error'):
                qlts = system_data['quan_ly_tai_san']
                context_parts.append(f"\n--- TÀI SẢN ({qlts.get('count', 0)} tài sản) ---")

                # Thống kê theo loại tài sản
                loai_count = {}
                vi_tri_count = {}
                for ts in qlts.get('tai_san', []):
                    loai = ts.get('loai_tai_san', 'Chưa phân loại')
                    vi_tri = ts.get('vi_tri', 'Chưa xác định')
                    loai_count[loai] = loai_count.get(loai, 0) + 1
                    vi_tri_count[vi_tri] = vi_tri_count.get(vi_tri, 0) + 1

                if loai_count:
                    context_parts.append("Theo loại:")
                    for loai, count in sorted(loai_count.items(), key=lambda x: x[1], reverse=True)[:5]:
                        context_parts.append(f"  - {loai}: {count} tài sản")

                if vi_tri_count:
                    context_parts.append("Theo vị trí:")
                    for vi_tri, count in sorted(vi_tri_count.items(), key=lambda x: x[1], reverse=True)[:5]:
                        context_parts.append(f"  - {vi_tri}: {count} tài sản")

            # Thông tin phòng họp
            if 'ke_toan_tai_san' in system_data and not system_data['ke_toan_tai_san'].get('error'):
                ktts = system_data['ke_toan_tai_san']
                context_parts.append(f"\n--- PHÒNG HỌP ({ktts.get('count_phong_hop', 0)} phòng) ---")
                for ph in ktts.get('phong_hop', [])[:10]:  # Chỉ lấy 10 phòng đầu
                    context_parts.append(f"- {ph['ten_phong']} ({ph['suc_chua']} người) - {ph['trang_thai']}")

            context_parts.append("\n=== HẾT DỮ LIỆU HỆ THỐNG ===")

            return "\n".join(context_parts)

        except Exception as e:
            _logger.error(f"Lỗi build context: {e}")
            return "Không thể tải dữ liệu hệ thống. Sẽ trả lời dựa trên kiến thức chung."

    def _get_thong_ke_tai_san(self):
        """Lấy thống kê tài sản chi tiết"""
        try:
            env = request.env

            # Thống kê theo loại
            loai_stats = []
            loai_records = env['loai_tai_san'].search([])
            for loai in loai_records:
                count = env['tai_san'].search_count([('loai_tai_san_id', '=', loai.id)])
                loai_stats.append(f"{loai.ten_loai_tai_san}: {count} tài sản")

            # Thống kê theo vị trí
            vi_tri_stats = []
            vi_tri_records = env['vi_tri'].search([])
            for vt in vi_tri_records:
                count = env['tai_san'].search_count([('vi_tri_hien_tai_id', '=', vt.id)])
                vi_tri_stats.append(f"{vt.ten_vi_tri}: {count} tài sản")

            return {
                'loai_tai_san': loai_stats,
                'vi_tri': vi_tri_stats,
            }

        except Exception as e:
            _logger.error(f"Lỗi lấy thống kê: {e}")
            return {}

    # ============================================================================
    # AI CHAT FUNCTIONS
    # ============================================================================

    def _build_system_prompt(self):
        """Tạo system prompt cho AI"""
        return """Bạn là trợ lý AI thông minh cho hệ thống Quản lý Tài sản và Nhân sự.

Nhiệm vụ của bạn:
1. Trả lời các câu hỏi về dữ liệu trong hệ thống dựa trên thông tin được cung cấp trong context
2. Giúp tra cứu thông tin tài sản, nhân viên, phòng họp từ dữ liệu thực tế
3. Phân tích và thống kê dữ liệu từ các module: nhan_su, quan_ly_tai_san, ke_toan_tai_san
4. Đưa ra gợi ý về quản lý tài sản hiệu quả
5. Tư vấn về bảo trì, khấu hao tài sản
6. Hỗ trợ đặt phòng họp và quản lý nhân sự

HƯỚNG DẪN QUAN TRỌNG - LUÔN LÀM THEO:
- Luôn trả lời bằng tiếng Việt
- SỬ DỤNG DỮ LIỆU TỪ CONTEXT được cung cấp (phần "DỮ LIỆU HỆ THỐNG CHI TIẾT")
- KHÔNG NÓI "không có quyền truy cập" hoặc "không thể truy cập" - bạn ĐÃ CÓ DỮ LIỆU
- Với câu hỏi về danh sách nhân viên: liệt kê từ "DANH SÁCH NHÂN VIÊN"
- Với câu hỏi về tài sản: liệt kê từ "DANH SÁCH TÀI SẢN"
- Với câu hỏi về phòng họp: liệt kê từ "DANH SÁCH PHÒNG HỌP"
- Với câu hỏi về số lượng: sử dụng từ "THỐNG KÊ TỔNG QUAN"
- Nếu thông tin cụ thể không có trong context, nói "Dựa trên dữ liệu hiện tại" và trả lời với thông tin có sẵn
- Giữ giọng điệu thân thiện, chuyên nghiệp, hữu ích

Đặc điểm hệ thống:
- Có 3 module chính: nhan_su, quan_ly_tai_san, ke_toan_tai_san
- Dữ liệu được cập nhật real-time từ các API
- Bạn có thể trả lời chính xác về tình trạng tài sản, thông tin nhân viên, và tình trạng phòng họp"""

    def _call_openrouter_api(self, messages):
        """Gọi OpenRouter API"""
        try:
            config = self._get_openrouter_config()

            # Nếu không có API key, trả về mock response
            if not config['api_key']:
                return self._get_mock_ai_response(messages)

            headers = {
                'Authorization': f'Bearer {config["api_key"]}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'http://localhost:8069',  # Thay bằng domain thật
                'X-Title': 'Odoo Asset Management AI Chatbot',
            }

            payload = {
                'model': config['model'],
                'messages': messages,
                'temperature': 0.7,
                'max_tokens': 1000,
                'top_p': 0.9,
            }

            response = requests.post(
                self.OPENROUTER_API_URL,
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                return data['choices'][0]['message']['content']
            else:
                _logger.error(f"OpenRouter API Error: {response.status_code} - {response.text}")
                return f"Lỗi API: {response.status_code}"

        except requests.exceptions.Timeout:
            return "Lỗi: Quá thời gian chờ phản hồi từ AI"
        except requests.exceptions.RequestException as e:
            _logger.error(f"Request Error: {e}")
            return f"Lỗi kết nối: {str(e)}"
        except Exception as e:
            _logger.error(f"Unexpected Error: {e}")
            return f"Lỗi không xác định: {str(e)}"

    def _get_mock_ai_response(self, messages):
        """Trả về mock response khi không có API key"""
        user_message = messages[-1]['content'] if messages else ""

        # Phân tích query để trả về response phù hợp
        query_lower = user_message.lower()

        if 'chào' in query_lower or 'hello' in query_lower:
            return "Xin chào! Tôi là trợ lý AI của hệ thống Quản lý Tài sản. Tôi có thể giúp bạn tra cứu thông tin về tài sản, nhân viên, thống kê dữ liệu và tư vấn về quản lý tài sản. Bạn cần hỗ trợ gì hôm nay?"

        elif 'tài sản' in query_lower or 'asset' in query_lower:
            if 'tìm' in query_lower or 'search' in query_lower or 'bao nhiêu' in query_lower or 'how many' in query_lower:
                return "Tôi tìm thấy một số tài sản phù hợp với yêu cầu của bạn. Tuy nhiên, để có kết quả chính xác, vui lòng cấu hình API key của OpenRouter trong Settings > System Parameters với key 'openrouter.api_key'."
            elif 'thống kê' in query_lower or 'stats' in query_lower:
                return "Theo dữ liệu hiện tại trong hệ thống, chúng ta có nhiều loại tài sản khác nhau. Để xem thống kê chi tiết, vui lòng cấu hình API key của OpenRouter."

        elif 'nhân viên' in query_lower or 'employee' in query_lower:
            return "Tôi có thể giúp bạn tìm kiếm thông tin nhân viên. Tuy nhiên, để sử dụng đầy đủ tính năng AI, vui lòng cấu hình API key của OpenRouter trong hệ thống."

        else:
            return "Cảm ơn bạn đã hỏi! Đây là chế độ demo của AI Chatbot. Để sử dụng đầy đủ tính năng AI thông minh, vui lòng cấu hình API key của OpenRouter trong Settings > System Parameters với key 'openrouter.api_key'."

    def _process_user_query(self, user_message, conversation_history=None):
        """Xử lý câu hỏi của user và tạo phản hồi"""

        # Khởi tạo conversation history nếu chưa có
        if conversation_history is None:
            conversation_history = []

        # Thêm system prompt nếu là tin nhắn đầu tiên
        messages = [
            {'role': 'system', 'content': self._build_system_prompt()}
        ]

        # Thêm lịch sử cuộc trò chuyện
        messages.extend(conversation_history[-10:])  # Giữ 10 tin nhắn gần nhất

        # TỰ ĐỘNG THU THẬP DỮ LIỆU TỪ TẤT CẢ API TRƯỚC KHI XỬ LÝ QUERY
        try:
            # Thu thập dữ liệu đầy đủ từ tất cả API
            env = request.env

            # Thu thập nhân viên chi tiết
            nhan_vien_records = env['nhan_vien'].search([], limit=20)
            nhan_vien_list = []
            for nv in nhan_vien_records:
                # Lấy chức vụ từ lịch sử công tác gần nhất
                chuc_vu = 'N/A'
                try:
                    latest_cong_tac = nv.lich_su_cong_tac_ids.sorted(key=lambda x: x.ngay_bat_dau, reverse=True)[:1]
                    if latest_cong_tac and latest_cong_tac.chuc_vu_id:
                        chuc_vu = latest_cong_tac.chuc_vu_id.ten_chuc_vu
                except:
                    pass

                nhan_vien_list.append({
                    'ma': nv.ma_dinh_danh,
                    'ten': nv.ho_va_ten,
                    'email': nv.email or 'N/A',
                    'dien_thoai': nv.so_dien_thoai or 'N/A',
                    'chuc_vu': chuc_vu
                })

            # Thu thập tài sản chi tiết
            tai_san_records = env['tai_san'].search([], limit=20)
            tai_san_list = []
            for ts in tai_san_records:
                tai_san_list.append({
                    'ma': ts.ma_tai_san,
                    'ten': ts.ten_tai_san,
                    'trang_thai': ts.trang_thai,
                    'vi_tri': getattr(ts.vi_tri_hien_tai_id, 'ten_vi_tri', 'N/A') if ts.vi_tri_hien_tai_id else 'N/A',
                    'gia_tri': ts.gia_tri_hien_tai
                })

            # Thu thập phòng họp
            phong_hop_records = env['phong_hop'].search([], limit=10)
            phong_hop_list = []
            for ph in phong_hop_records:
                phong_hop_list.append({
                    'ma': ph.ma_phong,
                    'ten': ph.ten_phong,
                    'suc_chua': ph.suc_chua,
                    'trang_thai': ph.trang_thai,
                    'vi_tri': ph.vi_tri_id.ten_vi_tri if ph.vi_tri_id else 'N/A'
                })

            # Thống kê tổng quan
            thong_ke = {
                'nhan_vien': len(nhan_vien_records),
                'tai_san': len(tai_san_records),
                'phong_hop': len(phong_hop_records)
            }

            # Tạo context chi tiết
            context_info = f"""
=== DỮ LIỆU HỆ THỐNG CHI TIẾT ===

THỐNG KÊ TỔNG QUAN:
- Nhân viên: {thong_ke['nhan_vien']} người
- Tài sản: {thong_ke['tai_san']} tài sản
- Phòng họp: {thong_ke['phong_hop']} phòng

DANH SÁCH NHÂN VIÊN:
"""
            for nv in nhan_vien_list[:10]:  # Hiển thị tối đa 10 nhân viên
                context_info += f"- {nv['ten']} ({nv['ma']}) - Chức vụ: {nv['chuc_vu']} - Email: {nv['email']}\n"

            context_info += "\nDANH SÁCH TÀI SẢN:\n"
            for ts in tai_san_list[:10]:  # Hiển thị tối đa 10 tài sản
                context_info += f"- {ts['ten']} ({ts['ma']}) - Trạng thái: {ts['trang_thai']} - Vị trí: {ts['vi_tri']}\n"

            context_info += "\nDANH SÁCH PHÒNG HỌP:\n"
            for ph in phong_hop_list:
                context_info += f"- {ph['ten']} ({ph['ma']}) - Sức chứa: {ph['suc_chua']} người - Trạng thái: {ph['trang_thai']}\n"

            context_info += "\n=== HẾT DỮ LIỆU HỆ THỐNG ==="

            user_message = f"{context_info}\n\nCâu hỏi của user: {user_message}"

        except Exception as e:
            _logger.warning(f"Không thể thu thập dữ liệu hệ thống: {e}")
            # Fallback: vẫn xử lý như bình thường
            user_message = f"Câu hỏi của user: {user_message}"

        # Phân tích query để lấy thêm dữ liệu cụ thể nếu cần
        query_lower = user_message.lower()

        # Nếu có từ khóa tìm kiếm cụ thể, bổ sung thêm thông tin chi tiết
        if any(keyword in query_lower for keyword in ['tìm', 'tra cứu', 'kiếm', 'search', 'find']):
            # Tìm kiếm tài sản
            if 'tài sản' in query_lower or 'asset' in query_lower:
                tai_san_results = self._search_tai_san(user_message, limit=5)
                if tai_san_results:
                    search_info = f"\n\nKết quả tìm kiếm tài sản:\n"
                    for ts in tai_san_results:
                        search_info += f"- {ts['ma_tai_san']}: {ts['ten_tai_san']} ({ts['trang_thai']}) - Vị trí: {ts['vi_tri']}\n"
                    user_message += search_info

            # Tìm kiếm nhân viên
            elif 'nhân viên' in query_lower or 'employee' in query_lower or 'staff' in query_lower:
                nv_results = self._search_nhan_vien(user_message, limit=5)
                if nv_results:
                    search_info = f"\n\nKết quả tìm kiếm nhân viên:\n"
                    for nv in nv_results:
                        search_info += f"- {nv['ma_dinh_danh']}: {nv['ho_va_ten']} ({nv['chuc_vu']}) - Email: {nv['email']}\n"
                    user_message += search_info

        # Nếu hỏi thống kê
        elif any(keyword in query_lower for keyword in ['thống kê', 'stats', 'tổng kết', 'báo cáo']):
            thong_ke = self._get_thong_ke_tai_san()
            if thong_ke:
                stats_info = f"\n\nThống kê chi tiết từ hệ thống:\n"
                if thong_ke.get('loai_tai_san'):
                    stats_info += "Theo loại tài sản:\n"
                    for stat in thong_ke['loai_tai_san'][:10]:  # Top 10
                        stats_info += f"- {stat}\n"
                if thong_ke.get('vi_tri'):
                    stats_info += "\nTheo vị trí:\n"
                    for stat in thong_ke['vi_tri'][:10]:  # Top 10
                        stats_info += f"- {stat}\n"
                user_message += stats_info

        # Thêm user message
        messages.append({'role': 'user', 'content': user_message})

        # Gọi AI
        ai_response = self._call_openrouter_api(messages)

        return ai_response

    def _collect_system_data_for_ai(self):
        """Thu thập dữ liệu tổng hợp từ tất cả các API trong hệ thống cho AI"""
        try:
            _logger.info("=== BẮT ĐẦU THU THẬP DỮ LIỆU HỆ THỐNG CHO AI ===")
            env = request.env
            data = {
                'timestamp': datetime.now().isoformat(),
                'nhan_su': {},
                'quan_ly_tai_san': {},
                'ke_toan_tai_san': {},
                'thong_ke_tong_quan': {}
            }

            # 1. Thu thập dữ liệu nhân sự
            try:
                nhan_vien_records = env['nhan_vien'].search([], limit=50)
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
                tai_san_records = env['tai_san'].search([], limit=100)
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

            # 3. Thu thập dữ liệu phòng họp
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

            _logger.info(f"=== HOÀN THÀNH THU THẬP DỮ LIỆU: {len(data)} keys ===")
            _logger.info(f"Nhân sự: {data['nhan_su'].get('count', 0)} records")
            _logger.info(f"Tài sản: {data['quan_ly_tai_san'].get('count', 0)} records")
            _logger.info(f"Phòng họp: {data['ke_toan_tai_san'].get('count_phong_hop', 0)} records")
            return data

        except Exception as e:
            _logger.error(f"Lỗi thu thập dữ liệu hệ thống cho AI: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}

    # ============================================================================
    # DEBUG ENDPOINTS
    # ============================================================================

    @http.route('/api/debug/system_data', type='json', auth='public', methods=['GET'], csrf=False, cors='*')
    def debug_system_data(self, **kwargs):
        """Debug endpoint để kiểm tra việc thu thập dữ liệu hệ thống"""
        try:
            if not self._authenticate():
                return {'success': False, 'status': 401, 'message': 'Unauthorized'}

            # Thu thập dữ liệu giống như trong chat
            env = request.env

            # Thu thập nhân viên chi tiết
            nhan_vien_records = env['nhan_vien'].search([], limit=20)
            nhan_vien_list = []
            for nv in nhan_vien_records:
                # Lấy chức vụ từ lịch sử công tác gần nhất
                chuc_vu = 'N/A'
                try:
                    latest_cong_tac = nv.lich_su_cong_tac_ids.sorted(key=lambda x: x.ngay_bat_dau, reverse=True)[:1]
                    if latest_cong_tac and latest_cong_tac.chuc_vu_id:
                        chuc_vu = latest_cong_tac.chuc_vu_id.ten_chuc_vu
                except:
                    pass

                nhan_vien_list.append({
                    'ma': nv.ma_dinh_danh,
                    'ten': nv.ho_va_ten,
                    'email': nv.email or 'N/A',
                    'dien_thoai': nv.so_dien_thoai or 'N/A',
                    'chuc_vu': chuc_vu
                })

            # Thu thập tài sản chi tiết
            tai_san_records = env['tai_san'].search([], limit=20)
            tai_san_list = []
            for ts in tai_san_records:
                tai_san_list.append({
                    'ma': ts.ma_tai_san,
                    'ten': ts.ten_tai_san,
                    'trang_thai': ts.trang_thai,
                    'vi_tri': getattr(ts.vi_tri_hien_tai_id, 'ten_vi_tri', 'N/A') if ts.vi_tri_hien_tai_id else 'N/A',
                    'gia_tri': ts.gia_tri_hien_tai
                })

            # Thu thập phòng họp
            phong_hop_records = env['phong_hop'].search([], limit=10)
            phong_hop_list = []
            for ph in phong_hop_records:
                phong_hop_list.append({
                    'ma': ph.ma_phong,
                    'ten': ph.ten_phong,
                    'suc_chua': ph.suc_chua,
                    'trang_thai': ph.trang_thai,
                    'vi_tri': ph.vi_tri_id.ten_vi_tri if ph.vi_tri_id else 'N/A'
                })

            data = {
                'nhan_vien': nhan_vien_list,
                'tai_san': tai_san_list,
                'phong_hop': phong_hop_list,
                'thong_ke': {
                    'nhan_vien_count': len(nhan_vien_records),
                    'tai_san_count': len(tai_san_records),
                    'phong_hop_count': len(phong_hop_records)
                }
            }

            return {
                'success': True,
                'status': 200,
                'data': data,
                'message': f'Dữ liệu hệ thống debug: {len(nhan_vien_list)} NV, {len(tai_san_list)} TS, {len(phong_hop_list)} PH'
            }

        except Exception as e:
            return {'success': False, 'status': 500, 'message': str(e)}

    # ============================================================================
    # ENDPOINTS
    # ============================================================================

    @http.route('/api/ai/chat', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def chat_with_ai(self, **kwargs):
        """
        Chat với AI Assistant

        Args:
            message: Câu hỏi của user
            conversation_id: ID cuộc trò chuyện (optional)
        """
        try:
            if not self._authenticate():
                return {'success': False, 'status': 401, 'message': 'Unauthorized'}

            # Extract message from kwargs (RPC) or JSON request body as fallback
            user_message = (kwargs.get('message') or '').strip()
            conversation_id = kwargs.get('conversation_id', 'default')
            if not user_message:
                try:
                    body = request.httprequest.data.decode('utf-8') or '{}'
                    json_body = json.loads(body)
                    user_message = (json_body.get('message') or '').strip()
                    conversation_id = json_body.get('conversation_id', conversation_id)
                except Exception:
                    user_message = (kwargs.get('message') or '').strip()

            if not user_message:
                return {'success': False, 'status': 400, 'message': 'Thiếu message'}

            # MỚI: Không load lịch sử chat cũ - mỗi lần là conversation mới
            conversation_history = []
            # Tắt tính năng load history cũ để tránh lỗi và tạo trải nghiệm chat mới mỗi lần
            # try:
            #     history_records = request.env['ai.chat.history'].sudo().search([
            #         ('conversation_id', '=', conversation_id)
            #     ], order='create_date asc', limit=20)
            #
            #     for record in history_records:
            #         if record.message_type == 'user':
            #             conversation_history.append({'role': 'user', 'content': record.message})
            #         elif record.message_type == 'assistant':
            #             conversation_history.append({'role': 'assistant', 'content': record.message})
            # except:
            #     pass

            # Xử lý message
            try:
                ai_response = self._process_user_query(user_message, conversation_history)
                # Đảm bảo ai_response luôn là string không null
                if not ai_response or not isinstance(ai_response, str):
                    ai_response = "Xin lỗi, tôi không thể xử lý yêu cầu của bạn lúc này. Vui lòng thử lại."
            except Exception as e:
                _logger.error(f"Lỗi xử lý query AI: {e}")
                ai_response = "Xin lỗi, có lỗi xảy ra khi xử lý yêu cầu của bạn. Vui lòng thử lại."

            # Lưu lịch sử (nếu có model)
            try:
                # Chỉ lưu user message nếu không null/empty
                if user_message and user_message.strip():
                    request.env['ai.chat.history'].sudo().create({
                        'conversation_id': conversation_id,
                        'message': user_message.strip(),
                        'message_type': 'user',
                        'user_id': request.env.uid or False,
                    })

                # Chỉ lưu AI response nếu không null/empty
                if ai_response and ai_response.strip():
                    request.env['ai.chat.history'].sudo().create({
                        'conversation_id': conversation_id,
                        'message': ai_response.strip(),
                        'message_type': 'assistant',
                        'user_id': request.env.uid or False,
                    })
            except Exception as e:
                # Nếu có lỗi khi lưu lịch sử, log và bỏ qua (không làm fail request)
                _logger.warning(f"Không thể lưu lịch sử chat: {e}")
                pass

            return {
                'success': True,
                'status': 200,
                'data': {
                    'response': ai_response,
                    'conversation_id': conversation_id,
                    'timestamp': datetime.now().isoformat(),
                }
            }

        except Exception as e:
            _logger.error(f"AI Chat Error: {e}")
            return {
                'success': False,
                'status': 500,
                'message': f'Lỗi server: {str(e)}'
            }

    @http.route('/api/ai/history', type='json', auth='public', methods=['GET', 'POST'], csrf=False, cors='*')
    def get_chat_history(self, **kwargs):
        """
        Lấy lịch sử chat

        Query params:
            - conversation_id: ID cuộc trò chuyện (default: 'default')
            - limit: Số lượng tin nhắn (default: 50)
        """
        try:
            if not self._authenticate():
                return {'success': False, 'status': 401, 'message': 'Unauthorized'}

            conversation_id = kwargs.get('conversation_id', 'default')
            limit = int(kwargs.get('limit', 50))

            try:
                history_records = request.env['ai.chat.history'].sudo().search([
                    ('conversation_id', '=', conversation_id)
                ], order='create_date desc', limit=limit)

                # Đảo ngược để có thứ tự cũ -> mới
                history_records = history_records.sorted(key=lambda r: r.create_date)

                history = []
                for record in history_records:
                    history.append({
                        'id': record.id,
                        'message': record.message,
                        'type': record.message_type,
                        'timestamp': record.create_date.isoformat(),
                        'user': record.user_id.name if record.user_id else 'AI Assistant',
                    })

                return {
                    'success': True,
                    'status': 200,
                    'data': {
                        'conversation_id': conversation_id,
                        'count': len(history),
                        'history': history,
                    }
                }

            except:
                # Nếu chưa có model
                return {
                    'success': True,
                    'status': 200,
                    'data': {
                        'conversation_id': conversation_id,
                        'count': 0,
                        'history': [],
                        'message': 'Chưa có lịch sử chat'
                    }
                }

        except Exception as e:
            _logger.error(f"Get History Error: {e}")
            return {'success': False, 'status': 500, 'message': str(e)}

    @http.route('/api/ai/clear', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def clear_chat_history(self, conversation_id='default', **kwargs):
        """
        Xóa lịch sử chat

        Args:
            conversation_id: ID cuộc trò chuyện cần xóa
        """
        try:
            if not self._authenticate():
                return {'success': False, 'status': 401, 'message': 'Unauthorized'}

            try:
                # Thay vì xóa hoàn toàn (có thể gây lỗi validation), hãy đánh dấu conversation_id thành null
                # để không load lại trong tương lai
                records_to_clear = request.env['ai.chat.history'].sudo().search([
                    ('conversation_id', '=', conversation_id)
                ])

                cleared_count = len(records_to_clear)

                # Thay đổi conversation_id để không bị load lại
                if records_to_clear:
                    new_conversation_id = f"cleared_{conversation_id}_{Date.now()}"
                    records_to_clear.write({
                        'conversation_id': new_conversation_id,
                        'message': f"[Đã xóa] {records_to_clear[0].message}" if records_to_clear else "[Đã xóa]"
                    })

                return {
                    'success': True,
                    'status': 200,
                    'data': {
                        'deleted_count': cleared_count,
                        'conversation_id': conversation_id,
                    },
                    'message': f'Đã xóa {cleared_count} tin nhắn'
                }

            except:
                return {
                    'success': True,
                    'status': 200,
                    'data': {
                        'deleted_count': 0,
                        'conversation_id': conversation_id,
                    },
                    'message': 'Không có lịch sử để xóa'
                }

        except Exception as e:
            _logger.error(f"Clear History Error: {e}")
            return {'success': False, 'status': 500, 'message': str(e)}