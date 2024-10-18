function printQRCode() {
    var printWindow = window.open('', 'PRINT', 'height=400,width=800');
    var qrCode = document.getElementById("qrcode-data-container").innerHTML;
    console.log(qrCode);
    printWindow.document.write('<html><head><title>Print QR Code</title>');
    printWindow.document.write('</head><body >');
    printWindow.document.write(qrCode);
    printWindow.document.write('</body></html>');
    printWindow.document.close();
    printWindow.focus();
    printWindow.print();
    printWindow.close();
}

function downloadQRCode(filename) {
    // the desktop version of the QR code is a img tag
    var qrcode = document.getElementById("qrcode-data-container").getElementsByTagName("img")[0];
    var link = document.createElement('a');
    link.download = filename ? filename : 'qrcode.png';
    if (qrcode.src.indexOf('data:image/png;base64,') == 0) {
        link.href = qrcode.src;
    } else {
        // the mobile version of the QR code is a canvas tag
        qrcodeCanvas = document.getElementById("qrcode-data-container").getElementsByTagName("canvas")[0];
        link.href = qrcodeCanvas.toDataURL("image/png");
    }
    link.click();
}
