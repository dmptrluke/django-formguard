document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('[data-fg-ia]').forEach(function(field) {
        var form = field.form;
        if (!form) return;
        var marked = false;
        function mark() {
            if (!marked) {
                marked = true;
                field.value = '1';
            }
        }
        form.addEventListener('keydown', mark);
        form.addEventListener('focusin', mark);
        form.addEventListener('pointerdown', mark);
    });
});
