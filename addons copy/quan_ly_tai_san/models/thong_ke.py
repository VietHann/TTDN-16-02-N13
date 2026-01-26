from odoo import models, fields, api

class ThongKeTaiSan(models.Model):
    _name = 'thong_ke'
    _description = 'Thống kê tài sản'
    _auto = False

    tai_san_id = fields.Many2one('tai_san', string="Tài sản", readonly=True)
    trang_thai = fields.Selection([
        ('moi', 'Mới'),
        ('dang_su_dung', 'Đang sử dụng'),
        ('bao_tri', 'Bảo trì'),
        ('thanh_ly', 'Thanh lý')
    ], string="Trạng thái", readonly=True)
    loai_tai_san_id = fields.Many2one('loai_tai_san', string="Loại tài sản", readonly=True)
    vi_tri_hien_tai_id = fields.Many2one('vi_tri', string="Vị trí hiện tại", readonly=True)
    nha_cung_cap_id = fields.Many2one('nha_cung_cap', string="Nhà cung cấp", readonly=True)
    gia_tien_mua = fields.Float(string="Giá mua", readonly=True)
    gia_tri_hien_tai = fields.Float(string="Giá trị hiện tại", readonly=True)
    ngay_mua = fields.Datetime(string="Ngày mua", readonly=True)
    ngay_het_han_bao_hanh = fields.Date(string="Ngày hết bảo hành", readonly=True)
    ngay_thanh_ly = fields.Date(string="Ngày thanh lý", readonly=True)
    gia_tri_thanh_ly = fields.Float(string="Giá trị thanh lý", readonly=True)
    so_lan_su_dung = fields.Integer(string="Số lần sử dụng", default=0, readonly=True)
    so_lan_bao_tri = fields.Integer(string="Số lần bảo trì", default=0, readonly=True)
    tong_chi_phi_bao_tri = fields.Float(string="Tổng chi phí bảo trì", readonly=True)

    @api.model
    def init(self):
        self.env.cr.execute("DROP VIEW IF EXISTS thong_ke CASCADE;")
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW thong_ke AS (
                SELECT  
                    ts.id AS id,
                    ts.id AS tai_san_id,
                    ts.trang_thai,
                    ts.loai_tai_san_id,
                    ts.vi_tri_hien_tai_id,
                    ts.nha_cung_cap_id,
                    ts.gia_tien_mua,
                    ts.gia_tri_hien_tai,
                    ts.ngay_mua,
                    ts.ngay_het_han_bao_hanh,
                    tl.ngay_thanh_ly,
                    tl.gia_tri_thanh_ly,
                    (SELECT COUNT(*) FROM lich_su_su_dung lsd WHERE lsd.tai_san_id = ts.id) AS so_lan_su_dung,
                    (SELECT COUNT(*) FROM lich_su_bao_tri lbt WHERE lbt.tai_san_id = ts.id) AS so_lan_bao_tri,
                    (SELECT COALESCE(SUM(lbt.chi_phi), 0) FROM lich_su_bao_tri lbt WHERE lbt.tai_san_id = ts.id) AS tong_chi_phi_bao_tri
                FROM tai_san ts
                LEFT JOIN thanh_ly tl ON ts.thanh_ly_id = tl.id
            )
        """)
