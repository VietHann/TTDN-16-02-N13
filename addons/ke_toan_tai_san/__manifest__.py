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
    'version': '15.0.1.0.0',
    'depends': [
        'base',
        'account',
        'mail',
        'quan_ly_tai_san',
        'nhan_su',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        
        # Data
        'data/tai_khoan_data.xml',
        'data/cron_khau_hao.xml',
        
        # Views (Actions phải load trước Menu)
        'views/tai_khoan_views.xml',
        'views/ke_toan_tai_san_views.xml',
        'views/but_toan_khau_hao_views.xml',
        'views/cau_hinh_khau_hao_views.xml',
        'views/ai_predictor_views.xml',
        'views/ai_analytics_views.xml',
        'views/menu.xml',  # Menu phải load cuối cùng
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
