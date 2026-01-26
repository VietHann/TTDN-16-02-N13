{
    'name': "Quản lý tài sản",

    'summary': "Quản lý tài sản, lịch sử sử dụng và khấu hao",

    'description': """
        Module quản lý tài sản trong doanh nghiệp, bao gồm:
        - Thông tin tài sản (tai_san, loai_tai_san, vi_tri, nha_cung_cap)
        - Nhập hàng/Mua hàng (phieu_nhap_hang)
        - Lịch sử sử dụng (lich_su_su_dung)
        - Lịch sử bảo trì (lich_su_bao_tri)
        - Khấu hao tài sản (khau_hao)
        - Quản lý phòng họp (phong_hop, dat_phong, bao_tri_phong_hop, nang_cap_phong_hop)
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    'category': 'Human Resources/Assets',
    'version': '0.1',

    'depends': ['base', 'mail', 'nhan_su'],
    'license': 'LGPL-3',

    'data': [
        'security/ir.model.access.csv',
        'sequences.xml',
        'data/sequences.xml',
        'data/mail_templates.xml',
        'data/cron_notifications.xml',
        'views/menu_root.xml',
        'views/tai_san.xml',
        'views/phieu_muon.xml',
        'views/phieu_bao_tri.xml',
        'views/vi_tri.xml',
        'views/loai_tai_san.xml',
        'views/nha_cung_cap.xml',
        'views/lich_su_su_dung.xml',
        'views/lich_su_bao_tri.xml',
        'views/lich_su_di_chuyen.xml',
        'views/phieu_dieu_chuyen.xml',
        'views/phieu_kiem_ke.xml',
        'views/lich_su_kiem_ke.xml',
        'views/thanh_ly.xml',
        'views/khau_hao.xml',
        'views/phieu_nhap_hang.xml',    
        'views/phong_hop.xml',
        'views/dat_phong.xml',
        'views/bao_tri_phong_hop.xml',
        'views/nang_cap_phong_hop.xml',
        'views/menu.xml',
        'views/thong_ke.xml',
    ],

    'demo': [
        'demo/demo_data.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'quan_ly_tai_san/static/src/css/tai_san.css',
            'quan_ly_tai_san/static/src/js/simple_signature.js',
        ],
    },
    'installable': True,
    'application': True,
}
