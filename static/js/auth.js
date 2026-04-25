// Highlight the chosen role card on the Sign Up Step 1 screen.
document.addEventListener('DOMContentLoaded', function () {
    const options = document.querySelectorAll('.role-option');
    options.forEach(function (opt) {
        opt.addEventListener('click', function () {
            options.forEach(o => o.classList.remove('selected'));
            opt.classList.add('selected');
            const radio = opt.querySelector('input[type="radio"]');
            if (radio) radio.checked = true;
        });
    });
});