const form = document.getElementById('createGameForm');
const resultDiv = document.getElementById('result');
const goLobbyBtn = document.getElementById('goLobbyBtn');
let currentGameId = null;

form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const hostName = document.getElementById('hostName').value.trim();
    const roundTime = parseInt(document.getElementById('roundTime').value);

    if (!hostName) {
        alert("Lütfen isminizi girin.");
        return;
    }

    try {
        const res = await fetch('http://192.168.1.118:8000/create-game', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ host_name: hostName, round_time: roundTime })
        });

        if (!res.ok) throw new Error('Oyun oluşturulamadı.');

        const data = await res.json();

        // 🔁 Burada yönlendiriyoruz:
        window.location.href = `lobby.html?game_id=${data.game_id}&host=${encodeURIComponent(hostName)}`;

    } catch (err) {
        alert(err.message);
    }
});

goLobbyBtn.addEventListener('click', () => {
    if (currentGameId) {
        window.location.href = `lobby.html?game_id=${currentGameId}`;
    }
});
