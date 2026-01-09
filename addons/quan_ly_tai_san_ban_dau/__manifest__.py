{
    'name': "Quản lý tài sản",

    'summary': "Quản lý tài sản, lịch sử sử dụng và khấu hao",

    'description': """
        Module quản lý tài sản trong doanh nghiệp, bao gồm:
        - Thông tin tài sản (tai_san, loai_tai_san, vi_tri, nha_cung_cap)
        - Lịch sử sử dụng (lich_su_su_dung)
        - Lịch sử bảo trì (lich_su_bao_tri)
        - Khấu hao tài sản (khau_hao)
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    'category': 'Human Resources/Assets',
    'version': '0.1',

    'depends': ['base', 'nhan_su'],

    'data': [
        'security/ir.model.access.csv',
        'sequences.xml',
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
        'views/thong_ke.xml',
        'views/menu.xml',
    ],

    'demo': [
        'demo/demo.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'quan_ly_tai_san/static/src/css/tai_san.css',
        ],
    },
    'installable': True,
    'application': True,
}
