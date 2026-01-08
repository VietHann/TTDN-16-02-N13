# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import json
import logging

_logger = logging.getLogger(__name__)


class AITaiSanAnalytics(models.Model):
    """Phân tích AI: Hiệu quả sử dụng tài sản"""
    _name = 'ai.tai_san.analytics'
    _description = 'Phân tích AI hiệu quả tài sản'
    _order = 'ngay_phan_tich desc'
    
    name = fields.Char('Tên báo cáo', required=True, default=lambda self: f"Phân tích {fields.Date.today()}")
    ngay_phan_tich = fields.Date('Ngày phân tích', default=fields.Date.today, required=True)
    
    # Thống kê tổng quan
    tong_tai_san = fields.Integer('Tổng số tài sản', compute='_compute_metrics', store=True)
    tong_gia_tri = fields.Float('Tổng giá trị', compute='_compute_metrics', store=True, digits=(16, 2))
    tong_chi_phi_bao_tri = fields.Float('Tổng chi phí bảo trì', compute='_compute_metrics', store=True, digits=(16, 2))
    ty_le_hieu_qua_tb = fields.Float('Tỷ lệ hiệu quả TB (%)', compute='_compute_metrics', store=True)
    
    # Top assets
    tai_san_hieu_qua_cao_ids = fields.Many2many(
        'tai_san', 'ai_analytics_efficient_rel', 
        string='Top 10 tài sản hiệu quả cao'
    )
    tai_san_ton_kem_ids = fields.Many2many(
        'tai_san', 'ai_analytics_inefficient_rel',
        string='Tài sản kém hiệu quả (Đề xuất thanh lý)'
    )
    
    # Dữ liệu biểu đồ
    chart_data_json = fields.Text('Dữ liệu biểu đồ (JSON)')
    
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('done', 'Hoàn thành'),
    ], default='draft', string='Trạng thái')
    
    ghi_chu = fields.Text('Ghi chú')
    
    @api.depends('tai_san_hieu_qua_cao_ids', 'tai_san_ton_kem_ids')
    def _compute_metrics(self):
        for record in self:
            all_tai_san = self.env['tai_san'].search([('trang_thai', '!=', 'DaThanhLy')])
            record.tong_tai_san = len(all_tai_san)
            record.tong_gia_tri = sum(all_tai_san.mapped('gia_tien_mua'))
            
            # Tính tổng chi phí bảo trì
            lich_su_bt = self.env['lich_su_bao_tri'].search([('tai_san_id', 'in', all_tai_san.ids)])
            record.tong_chi_phi_bao_tri = sum(lich_su_bt.mapped('chi_phi'))
            
            # Giả định điểm hiệu quả trung bình
            record.ty_le_hieu_qua_tb = 65.0
    
    def action_analyze(self):
        """Thực hiện phân tích"""
        self.ensure_one()
        
        tai_san_records = self.env['tai_san'].search([('trang_thai', '!=', 'DaThanhLy')])
        results = []
        
        for ts in tai_san_records:
            score = self._compute_efficiency_score(ts)
            results.append({'tai_san': ts, 'score': score})
        
        # Sắp xếp
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # Top 10
        self.tai_san_hieu_qua_cao_ids = [(6, 0, [r['tai_san'].id for r in results[:10]])]
        
        # Bottom (score < 40)
        tai_san_kem = [r['tai_san'].id for r in results if r['score'] < 40]
        self.tai_san_ton_kem_ids = [(6, 0, tai_san_kem)]
        
        # Tạo dữ liệu biểu đồ
        chart_data = {
            'labels': [r['tai_san'].ten_tai_san for r in results[:20]],
            'scores': [r['score'] for r in results[:20]],
        }
        self.chart_data_json = json.dumps(chart_data)
        self.state = 'done'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Phân tích hoàn tất'),
                'message': f'Đã phân tích {len(results)} tài sản',
                'type': 'success',
            }
        }
    
    def _compute_efficiency_score(self, tai_san):
        """Tính điểm hiệu quả (0-100)"""
        # Đơn giản hóa: Kết hợp các chỉ số
        score = 50  # Điểm cơ bản
        
        # Tần suất sử dụng
        so_lan_muon = self.env['phieu_muon'].search_count([
            ('tai_san_id', '=', tai_san.id), ('state', '=', 'done')
        ])
        score += min(so_lan_muon * 2, 30)
        
        # Chi phí bảo trì thấp = tốt
        chi_phi = sum(self.env['lich_su_bao_tri'].search([
            ('tai_san_id', '=', tai_san.id)
        ]).mapped('chi_phi'))
        
        if tai_san.gia_tien_mua > 0:
            ty_le = chi_phi / tai_san.gia_tien_mua
            if ty_le < 0.1:
                score += 20
            elif ty_le < 0.3:
                score += 10
            else:
                score -= 10
        
        return min(max(score, 0), 100)
