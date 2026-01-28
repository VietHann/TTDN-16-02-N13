# -*- coding: utf-8 -*-
{
    'name': "Kế toán Tài sản",
    'summary': """Quản lý kế toán tài sản cố định, khấu hao tự động và tích hợp AI""",
    'description': """
        Module Kế toán Tài sản - Đồ án Sinh viên
        ==========================================
        
        Tính năng chính:
        ---------------
        * Quản lý danh mục tài khoản kế toán
        * Tự động khấu hao tài sản hàng tháng (Cron Job)
        * Sinh bút toán kế toán tự động (account.move)
        * Quản lý Thu/Chi, Ngân sách, Công nợ
        * Quản lý Hóa đơn, Sao kê, Tính thuế
        * Liên kết với module Quản lý Tài sản và Nhân sự
        * Tích hợp AI:
            - Dự đoán thời điểm bảo trì/thanh lý
            - Phân tích hiệu quả sử dụng tài sản
        
        Phù hợp với:
        -----------
        * Chuẩn kế toán Việt Nam
        * Odoo 15 Community/Enterprise
        * Đồ án tốt nghiệp ngành CNTT/KTPM
    """,
    'author': "Đồ án Sinh viên",
    'website': "http://www.yourcompany.com",
    'category': 'Accounting/Accounting',
    'version': '15.0.1.1.0',
    'depends': [
        'base',
        'mail',
        'quan_ly_tai_san',
        'nhan_su',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',

        # Data
        'data/tai_khoan_data.xml',
        'data/ai_config_data.xml',
        'data/cron_khau_hao.xml',
        'data/sequences.xml',

        # Views (Actions phải load trước Menu)
        'views/tai_khoan_views.xml',
        'views/ke_toan_tai_san_views.xml',
        'views/but_toan_khau_hao_views.xml',
        'views/cau_hinh_khau_hao_views.xml',
        'views/ai_predictor_views.xml',
        'views/ai_analytics_views.xml',
        'views/ai_config_views.xml',
        'views/ai_chatbot_interface.xml',
        'views/ai_chat_history_views.xml',
        'views/thu_chi_views.xml',
        'views/ngan_sach_views.xml',
        'views/cong_no_views.xml',
        'views/hoa_don_views.xml',
        'views/sao_ke_views.xml',
        'views/tinh_thue_views.xml',
        'views/menu.xml',  # Menu phải load cuối cùng
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ke_toan_tai_san/static/src/css/ai_chatbot.css',
            'ke_toan_tai_san/static/src/css/ke_toan.css',
            'ke_toan_tai_san/static/src/js/ai_chatbot.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
