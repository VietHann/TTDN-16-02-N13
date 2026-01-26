from odoo import models, fields, api


class DanhSachChungChiBangCap(models.Model):
    _name = 'danh_sach_chung_chi_bang_cap'
    _description = 'Bảng danh sách chứng chỉ bằng cấp'

    chung_chi_bang_cap_id = fields.Many2one("chung_chi_bang_cap", string="Chứng chỉ bằng cấp", required=True)
    nhan_vien_id = fields.Many2one("nhan_vien", string="Nhân viên", required=True)
    ghi_chu = fields.Char("Ghi chú")
    ma_dinh_danh = fields.Char("Mã định danh", related='nhan_vien_id.ma_dinh_danh')
    tuoi = fields.Integer("Tuổi", related='nhan_vien_id.tuoi')
    
