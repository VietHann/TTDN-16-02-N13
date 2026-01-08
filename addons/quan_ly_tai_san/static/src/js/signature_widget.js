odoo.define('quan_ly_tai_san.signature_widget', function (require) {
    'use strict';

    var AbstractField = require('web.AbstractField');
    var fieldRegistry = require('web.field_registry');

    var SignatureField = AbstractField.extend({
        template: 'SignatureField',
        events: _.extend({}, AbstractField.prototype.events, {
            'click .signature-clear': '_onClearSignature',
            'click .signature-save': '_onSaveSignature',
        }),

        init: function () {
            this._super.apply(this, arguments);
            this.canvas = null;
            this.ctx = null;
            this.isDrawing = false;
            this.signatureData = null;
        },

        _render: function () {
            this._super.apply(this, arguments);
            this.$el.html(this._renderSignatureWidget());
            this._initCanvas();
        },

        _renderSignatureWidget: function () {
            return `
                <div class="signature-widget">
                    <div class="signature-header">
                        <h6>Ký xác nhận trả tài sản</h6>
                        <div class="signature-actions">
                            <button type="button" class="btn btn-sm btn-secondary signature-clear">Xóa</button>
                            <button type="button" class="btn btn-sm btn-primary signature-save">Lưu chữ ký</button>
                        </div>
                    </div>
                    <div class="signature-canvas-container">
                        <canvas id="signature-canvas" width="400" height="200" style="border: 1px solid #ccc;"></canvas>
                    </div>
                    <div class="signature-info">
                        <small class="text-muted">Vui lòng ký tên vào khung trên để xác nhận trả tài sản</small>
                    </div>
                </div>
            `;
        },

        _initCanvas: function () {
            this.canvas = this.$('#signature-canvas')[0];
            this.ctx = this.canvas.getContext('2d');

            // Set canvas properties
            this.ctx.strokeStyle = '#000';
            this.ctx.lineWidth = 2;
            this.ctx.lineCap = 'round';
            this.ctx.lineJoin = 'round';

            // Bind mouse events
            this.canvas.addEventListener('mousedown', this._startDrawing.bind(this));
            this.canvas.addEventListener('mousemove', this._draw.bind(this));
            this.canvas.addEventListener('mouseup', this._stopDrawing.bind(this));
            this.canvas.addEventListener('mouseout', this._stopDrawing.bind(this));

            // Bind touch events for mobile
            this.canvas.addEventListener('touchstart', this._handleTouchStart.bind(this));
            this.canvas.addEventListener('touchmove', this._handleTouchMove.bind(this));
            this.canvas.addEventListener('touchend', this._stopDrawing.bind(this));
        },

        _startDrawing: function (e) {
            this.isDrawing = true;
            this.ctx.beginPath();
            this.ctx.moveTo(e.offsetX, e.offsetY);
        },

        _draw: function (e) {
            if (!this.isDrawing) return;
            this.ctx.lineTo(e.offsetX, e.offsetY);
            this.ctx.stroke();
        },

        _stopDrawing: function () {
            this.isDrawing = false;
        },

        _handleTouchStart: function (e) {
            e.preventDefault();
            var touch = e.touches[0];
            var rect = this.canvas.getBoundingClientRect();
            var x = touch.clientX - rect.left;
            var y = touch.clientY - rect.top;

            this.isDrawing = true;
            this.ctx.beginPath();
            this.ctx.moveTo(x, y);
        },

        _handleTouchMove: function (e) {
            e.preventDefault();
            if (!this.isDrawing) return;

            var touch = e.touches[0];
            var rect = this.canvas.getBoundingClientRect();
            var x = touch.clientX - rect.left;
            var y = touch.clientY - rect.top;

            this.ctx.lineTo(x, y);
            this.ctx.stroke();
        },

        _onClearSignature: function () {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
            this.signatureData = null;
        },

        _onSaveSignature: function () {
            if (this._isCanvasEmpty()) {
                this.displayNotification({
                    title: 'Cảnh báo',
                    message: 'Vui lòng ký tên trước khi lưu!',
                    type: 'warning'
                });
                return;
            }

            // Get signature as base64 image and extract base64 data only
            var dataURL = this.canvas.toDataURL('image/png');
            // Remove the data URL prefix (data:image/png;base64,) to get pure base64
            this.signatureData = dataURL.split(',')[1];

            // Show confirmation dialog
            if (confirm('Bạn có chắc muốn lưu chữ ký này để xác nhận trả tài sản?')) {
                this._saveSignature();
            }
        },

        _isCanvasEmpty: function () {
            var imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
            for (var i = 0; i < imageData.data.length; i += 4) {
                if (imageData.data[i + 3] !== 0) return false;
            }
            return true;
        },

        _saveSignature: function () {
            var self = this;
            var currentUser = this.getSession().user_id;
            var userName = this.getSession().name;

            this._rpc({
                model: 'phieu_muon',
                method: 'action_sign_return',
                args: [[this.res_id], this.signatureData, userName],
            }).then(function (result) {
                self.displayNotification({
                    title: 'Thành công',
                    message: 'Đã lưu chữ ký xác nhận trả tài sản!',
                    type: 'success'
                });
                // Reload the form to show updated signature status
                self.trigger_up('reload');
            }).catch(function (error) {
                self.displayNotification({
                    title: 'Lỗi',
                    message: 'Không thể lưu chữ ký: ' + error.message,
                    type: 'danger'
                });
            });
        },

        _formatValue: function (value) {
            // Handle the display of existing signature
            this.signatureData = value;
            if (value && this.canvas && this.ctx) {
                try {
                    var img = new Image();
                    img.onload = function() {
                        try {
                            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
                            this.ctx.drawImage(img, 0, 0);
                        } catch (drawError) {
                            console.warn('Error drawing signature image:', drawError);
                        }
                    }.bind(this);
                    img.onerror = function() {
                        console.warn('Error loading signature image');
                        // If image fails to load, just clear canvas
                        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
                        this.ctx.fillText('Signature loaded but cannot display', 10, 30);
                    }.bind(this);

                    // If value is base64 text, add data URL prefix
                    var imageSrc = value;
                    if (value && !value.startsWith('data:')) {
                        imageSrc = 'data:image/png;base64,' + value;
                    }
                    img.src = imageSrc;
                } catch (error) {
                    console.warn('Error in _formatValue:', error);
                }
            }
        }
    });

    fieldRegistry.add('asset_signature', SignatureField);

    return SignatureField;
});