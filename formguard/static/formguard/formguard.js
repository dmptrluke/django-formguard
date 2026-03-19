document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('[data-fg-js]').forEach(function(field) {
        var form = field.form;
        if (!form) return;
        requestAnimationFrame(function() {
            var token = form.querySelector('[data-fg-token]');
            if (token && token.value) {
                var sum = 0;
                for (var i = 0; i < token.value.length; i++) {
                    sum = (sum + token.value.charCodeAt(i)) & 0xFFFF;
                }
                field.value = sum.toString(16);
            }
        });
    });
});
