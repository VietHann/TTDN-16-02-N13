# Tổng Quan Module Quản Lý Tài Sản

## 1. Module Gốc quan_ly_tai_san_ban_dau

### Chức Năng Chính (Đơn Giản)

#### 🏷️ **Quản Lý Thông Tin Tài Sản Cơ Bản**
- Mã tài sản tự động (TS-XXXXX), tên, hình ảnh, số serial
- Ngày mua, giá mua, giá trị hiện tại (tự động tính khấu hao 10%/năm)
- Trạng thái: Lưu trữ, Mượn, Bảo trì, Hỏng, Đã thanh lý
- Liên kết: Loại tài sản, vị trí, nhà cung cấp, người quản lý, người đang sử dụng

#### 🔄 **Mượn/Trả Tài Sản**
- Phiếu mượn với ngày mượn/trả
- Lịch sử sử dụng (LS-XXXXX)
- Ghi chú cho từng lần mượn

#### 🔧 **Bảo Trì & Kiểm Kê**
- Lịch sử bảo trì tài sản
- Phiếu kiểm kê định kỳ
- Trạng thái kiểm kê: Bình thường, Hỏng hóc, Mất, Đang sửa chữa

#### 💰 **Khấu Hao Tài Sản**
- Phương pháp: Đường thẳng hoặc số dư giảm dần
- Tự động tính giá trị khấu hao và còn lại
- Mã khấu hao tự động (KH-XXXXX)

#### 📍 **Vị Trí & Điều Chuyển**
- Quản lý vị trí lưu trữ
- Lịch sử di chuyển tài sản
- Phiếu điều chuyển

#### 🗑️ **Thanh Lý & Thống Kê**
- Xử lý tài sản hết sử dụng
- Dashboard: Tổng số lượng, giá trị, tài sản đang dùng/hỏng

---

## 2. Kết Hợp Với 2 Module Còn Lại

### 🤝 **Tích Hợp Với Module nhan_su**

#### Dữ Liệu Liên Kết
- `quan_ly_id`: Người quản lý tài sản (link tới `nhan_vien`)
- `nguoi_dang_dung_id`: Người đang sử dụng (link tới `nhan_vien`)
- `nhan_vien_id`: Người mượn trong lịch sử sử dụng
- `nguoi_lap_id`, `nguoi_duyet_id`: Trong các phiếu

#### Quy Trình Nghiệp Vụ
1. **Nhân viên** tạo phiếu mượn tài sản
2. **Người quản lý** (từ module nhan_su) duyệt phiếu
3. **Cập nhật** người đang sử dụng tài sản
4. **Ghi lịch sử** với thông tin nhân viên

---

### 💼 **Tích Hợp Với Module ke_toan_tai_san**

#### Dữ Liệu Liên Kết
- Khấu hao tài sản tự động sinh bút toán kế toán
- Giá trị tài sản cập nhật liên tục
- Liên kết với tài khoản kế toán, hóa đơn, công nợ

#### Quy Trình Nghiệp Vụ
1. **Mua tài sản**: Ghi nhận giá trị → Sinh bút toán
2. **Khấu hao định kỳ**: Tự động tính → Sinh bút toán khấu hao
3. **Thanh lý**: Giảm giá trị → Sinh bút toán thu nhập
4. **AI phân tích**: Dự đoán bảo trì, hiệu quả sử dụng

---

## 3. Điểm Chưa Hợp Lý Của Module Gốc

### ❌ **THIẾU (Missing Features)**

#### 1. **Không Có Quy Trình Nhập Hàng Chính Thức**
- **Vấn đề**: Chỉ tạo tài sản trực tiếp, không có phiếu nhập
- **Hậu quả**: Thiếu kiểm soát mua sắm, không theo dõi đơn hàng
- **Ảnh hưởng**: Khó quản lý chi phí, thiếu phê duyệt mua hàng

#### 2. **Không Quản Lý Phòng Họp**
- **Vấn đề**: Chỉ quản lý tài sản rời lẻ
- **Hậu quả**: Không theo dõi lịch đặt phòng, thiết bị trong phòng
- **Ảnh hưởng**: Trùng lịch, lãng phí tài nguyên phòng họp

#### 3. **Thiếu Tự Động Hóa & Thông Báo**
- **Vấn đề**: Không có cron job, email template
- **Hậu quả**: Phải theo dõi thủ công
- **Ảnh hưởng**: Trễ hạn bảo hành, khấu hao

---

### ❌ **SAI (Wrong Implementation)**

#### 1. **Logic Khấu Hao Sai Vị Trí**
- **Vấn đề**: Tính khấu hao trực tiếp trong model `tai_san`
- **Tại sao sai**: Vi phạm Single Responsibility Principle
- **Hậu quả**: Model trở nên nặng nề, khó maintain

#### 2. **Tự Tạo Mã Không Chuẩn**
- **Vấn đề**: Không dùng `ir.sequence`, tự tạo logic
- **Tại sao sai**: Không tuân thủ best practice Odoo
- **Hậu quả**: Khó customize, dễ xung đột khi import

#### 3. **Workflow Phê Duyệt Đơn Giản Quá**
- **Vấn đề**: Các phiếu thiếu trạng thái phê duyệt rõ ràng
- **Tại sao sai**: Thiếu kiểm soát, dễ bị lạm dụng
- **Hậu quả**: Rủi ro mất mát tài sản

---

### ⚠️ **THỪA (Unnecessary Complexity)**

#### 1. **Tính Toán Dashboard Trong Model Chính**
- **Vấn đề**: Logic dashboard xen lẫn trong `tai_san.py`
- **Hậu quả**: Model chậm, khó test
- **Giải pháp**: Tách thành computed fields riêng hoặc reports

#### 2. **Validation Constraints Cứng**
- **Vấn đề**: Hard-code tỷ lệ khấu hao 10%, format mã cứng
- **Hậu quả**: Không linh hoạt cho doanh nghiệp khác nhau
- **Giải pháp**: Lưu trong company settings hoặc configurable

---

## 4. Khuyến Nghị Sửa Đổi

### 🔧 **Cần Sửa Ngay**
1. **Chuyển logic khấu hao** sang module `ke_toan_tai_san`
2. **Dùng `ir.sequence`** cho tất cả mã tự động
3. **Thêm workflow phê duyệt** cho các phiếu

### ➕ **Cần Thêm**
1. **Phiếu nhập hàng** với workflow đầy đủ
2. **Quản lý phòng họp** (đặt phòng, bảo trì)
3. **Mail notifications** và cron jobs

### 🏗️ **Kiến Trúc**
- Tách business logic thành services
- Sử dụng proper workflow states
- Implement proper error handling

---

*Tóm tắt module quan_ly_tai_san_ban_dau và các vấn đề cần cải thiện*