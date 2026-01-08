#!/bin/bash
# Script kiểm tra dependencies

echo "=== KIỂM TRA DEPENDENCIES ==="

# Kiểm tra module quan_ly_tai_san
if [ -d "/home/vietlv/odo/odoo-fitdnu/addons/quan_ly_tai_san" ]; then
    echo "✅ quan_ly_tai_san: Tồn tại"
else
    echo "❌ quan_ly_tai_san: KHÔNG TỒN TẠI"
fi

# Kiểm tra module nhan_su
if [ -d "/home/vietlv/odo/odoo-fitdnu/addons/nhan_su" ]; then
    echo "✅ nhan_su: Tồn tại"
else
    echo "❌ nhan_su: KHÔNG TỒN TẠI"
fi

# Kiểm tra module ke_toan_tai_san
if [ -d "/home/vietlv/odo/odoo-fitdnu/addons/ke_toan_tai_san" ]; then
    echo "✅ ke_toan_tai_san: Tồn tại"
    
    # Kiểm tra các file quan trọng
    if [ -f "/home/vietlv/odo/odoo-fitdnu/addons/ke_toan_tai_san/__manifest__.py" ]; then
        echo "  ✅ __manifest__.py: OK"
    fi
    
    if [ -f "/home/vietlv/odo/odoo-fitdnu/addons/ke_toan_tai_san/__init__.py" ]; then
        echo "  ✅ __init__.py: OK"
    fi
else
    echo "❌ ke_toan_tai_san: KHÔNG TỒN TẠI"
fi

echo ""
echo "=== HƯỚNG DẪN ==="
echo "1. Đảm bảo cả 3 module tồn tại"
echo "2. Trong Odoo: Apps → ⋮ → Update Apps List"
echo "3. Tìm 'Kế toán Tài sản' (tiếng Việt)"
echo "4. Nếu vẫn không thấy, cài 'quan_ly_tai_san' và 'nhan_su' trước"
