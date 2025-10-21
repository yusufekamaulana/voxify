document.addEventListener('DOMContentLoaded', () => {
    
    const continueButton = document.getElementById('continue-btn');

    continueButton.addEventListener('click', () => {
        // Ganti baris ini dari alert ke navigasi halaman
        window.location.href = '/login';
    });

});