document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('[data-fg-js]').forEach(function(field) {
        var form = field.form;
        if (!form) return;
        requestAnimationFrame(function() {
            var nonce = form.querySelector('[data-fg-nonce]');
            if (nonce && nonce.value) {
                var sum = 0;
                for (var i = 0; i < nonce.value.length; i++) {
                    sum = (sum + nonce.value.charCodeAt(i)) & 0xFFFF;
                }
                field.value = sum.toString(16);
            }
        });
    });
});
