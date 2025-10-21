document.addEventListener('DOMContentLoaded', () => {
    // Tombol-tombol di header
    const profileBtn = document.getElementById('profile-btn');
    const langBtn = document.getElementById('lang-btn');
    const historyBtn = document.getElementById('history-btn');

    // Popup-popup
    const profilePopup = document.getElementById('profile-popup');
    const languagePopup = document.getElementById('language-popup');

    // Fungsi untuk menutup semua popup
    function closeAllPopups() {
        if (profilePopup) profilePopup.style.display = 'none';
        if (languagePopup) languagePopup.style.display = 'none';
    }

    // Event listener untuk tombol profil
    if (profileBtn && profilePopup) {
        profileBtn.addEventListener('click', (event) => {
            event.stopPropagation();
            const isVisible = profilePopup.style.display === 'block';
            closeAllPopups();
            profilePopup.style.display = isVisible ? 'none' : 'block';
        });
    }

    // Event listener untuk tombol bahasa
    if (langBtn && languagePopup) {
        langBtn.addEventListener('click', (event) => {
            event.stopPropagation();
            const isVisible = languagePopup.style.display === 'block';
            closeAllPopups();
            languagePopup.style.display = isVisible ? 'none' : 'block';
        });
    }

    // Event listener tombol History lama (yang di tengah halaman)
    if (historyBtn) {
        historyBtn.addEventListener('click', () => {
            alert("Gunakan tombol 📜 di pojok kanan bawah untuk melihat riwayat rekamanmu!");
        });
    }

    // Klik di luar popup menutup semua popup
    window.addEventListener('click', () => closeAllPopups());

    // Cegah popup tertutup saat diklik di dalamnya
    if (profilePopup) profilePopup.addEventListener('click', (e) => e.stopPropagation());
    if (languagePopup) languagePopup.addEventListener('click', (e) => e.stopPropagation());

    // =======================================================
    // === Floating History (📜 pojok kanan bawah)
    // =======================================================
    const floatingBtn = document.getElementById('floating-history-btn');
    const historyPopup = document.getElementById('history-popup');
    const closeHistory = document.getElementById('close-history');
    const historyList = document.getElementById('history-list');

    if (floatingBtn && historyPopup && closeHistory && historyList) {
        floatingBtn.addEventListener('click', async () => {
            historyPopup.style.display = 'block';
            historyList.innerHTML = "<li>Loading...</li>";

            try {
                const res = await fetch("/history");
                const data = await res.json();
                historyList.innerHTML = "";

                if (data.length === 0) {
                    historyList.innerHTML = "<li>No recordings yet.</li>";
                } else {
                    data.slice().reverse().forEach(item => {
                        const li = document.createElement("li");
                        li.textContent = `${item.filename} – ${item.duration}s – ${item.timestamp}`;
                        historyList.appendChild(li);
                    });
                }
            } catch (err) {
                historyList.innerHTML = "<li>Error loading history.</li>";
            }
        });

        closeHistory.addEventListener('click', () => {
            historyPopup.style.display = 'none';
        });
    }
});
