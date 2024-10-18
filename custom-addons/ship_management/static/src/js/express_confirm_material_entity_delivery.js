/** @odoo-module **/
import SystrayMenu from 'web.SystrayMenu';
import Widget from 'web.Widget';
import core from 'web.core';
import Dialog from 'web.Dialog';

const _t = core._t;
const QWeb = core.qweb;
function _confirm_delivery () {
    // ajax send Post request to /material_paint_quote/confirm_delivery
    // with form-data: quote_ref: $("#quote_ref").val()
    $.ajax({
        type: "POST",
        url: "/material_paint_quote/confirm_delivery",
        data: {
            quote_ref: $("#quote_ref").val(),
            delivered_quantity: $("#delivered_quantity").val(),
            csrf_token: core.csrf_token,
        },
        success: function (response) {
            console.log(response);
        },
        error: function (error) {
            console.log(error);
        }
    });
    // Clear the input
    $("#quote_ref").val("");
}

var ExpressDeliveryConfirmWidget = Widget.extend({
    template:'ship_management.express_confirm_material_entity_delivery',
    events: {
        "keydown #quote_ref": "on_keydown",
        "click #show_delivery_confirmation_dialog": "_show_delivery_confirmation_dialog",
        "click #qr_scanner": "on_qr_click",
    },
    on_keydown: function (event) {
        if (event.key === "Enter" || event.keyCode === 13) {
            // Prevent the default action to stop it from triggering a form submit
            event.preventDefault();
            this._show_delivery_confirmation_dialog();
        }
    },
    _show_delivery_confirmation_dialog: function () {
        // get quote data from /material_paint_quote/confirm_delivery/quote_ref
        // then show it in dialog
        $.ajax({
            type: "GET",
            url: "/material_paint_quote/confirm_delivery/" + $("#quote_ref").val(),
            success: function (response) {
                let dialog = new Dialog(this, {
                    size: 'medium',
                    title: _t("Confirm Delivery"),
                    buttons: [
                        {
                            text: _t("Hủy"),
                            id: 'btn_cancel',
                            classes: "btn-secondary",
                            click: function () {
                                dialog.close()
                            }
                        },
                        {
                            text: _t("Xác nhận"),
                            id: 'btn_confirm',
                            classes: "btn-primary",
                            click: function () {
                                _confirm_delivery()
                                dialog.close()
                            },
                        }
                    ],
                    $content: $(QWeb.render("ship_management.delivery_confirmation_dialog", {quote: response}))
                });
                dialog.open();
            },
            error: function (error) {
                console.log(error);
            }
        });
        
    },
    _start_scan_qr: function (dialog) {
        let QrCode = new Html5Qrcode("webcam_viewport")
        $('#webcam_viewport').height('100px')
        // Stop scanning after dialog closed
        dialog.on('closed', this, function () {
            // if QrCode is not Null, stop it
            if (QrCode!=null && QrCode.getState() == Html5QrcodeScannerState.SCANNING) {
                QrCode.stop()
            }
        })
        // get value from camera_id name camera_id, using $
        let device_uid = $('#camera_id').val()
        if (device_uid!=''){
            QrCode.start(
                device_uid, { fps: 10 },
                qrCodeData => {
                    $.when(QrCode.stop()).then(function () {
                        dialog.close()
                    })
                    // set value to input with id="quote_ref"
                    $('#quote_ref').val(qrCodeData)
                },
                errorMessage => {console.log("QR code not detected")}
            ).catch(err => {console.log(err)})
        }
        // when camera_id change, stop current camera and start new camera
        $('#camera_id').on("change", function(){
            if (QrCode.getState() == Html5QrcodeScannerState.SCANNING) {
                QrCode.stop().then(function () {
                let device_uid = $('#camera_id').val()
                if (device_uid!=''){
                    QrCode.start(
                        device_uid, { fps: 10, },
                        qrCodeData => {
                            $.when(QrCode.stop()).then(function () {
                                dialog.close()
                            })
                            // set value to input with id="quote_ref"
                            $('#quote_ref').val(qrCodeData)
                        },
                        errorMessage => {console.log("QR code not detected")}
                    ).catch(err => {console.log(err)})
                }
                })
            } else { 
                let device_uid = $('#camera_id').val()
                if (device_uid!=''){
                    QrCode.start(
                        device_uid, { fps: 10 },
                        qrCodeData => {
                            $.when(QrCode.stop()).then(function () {
                                dialog.close()
                            })
                            // set value to input with id="quote_ref"
                            $('#quote_ref').val(qrCodeData)
                        },
                        errorMessage => {console.log("QR code not detected")}
                    ).catch(err => {console.log(err)})
                }
            }
        })
    },
    on_qr_click: function (event) {
        self = this;
        Html5Qrcode.getCameras().then(function(devices){
            let dialog = new Dialog(self, {
                size: 'medium',
                title: _t("Scan QR Code"),
                $content: $(QWeb.render("ship_management.qr_scanner", {devices: devices}))
            });
            
            $.when(dialog.open()).then(function () {
                self._start_scan_qr(dialog);
            });
        }).catch(err => {
            // this.do_warn(_t("Camera Not Found"), err);
            console.log(err);
        });
    },
});
SystrayMenu.Items.push(ExpressDeliveryConfirmWidget);
export default ExpressDeliveryConfirmWidget;
