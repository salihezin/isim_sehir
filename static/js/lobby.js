const urlParams = new URLSearchParams(window.location.search);
const gameId = urlParams.get('game_id');
const hostName = urlParams.get('host'); // host bilgisi URL'den alınmalı: ?game_id=abc123&host=salih

const gameIdInput = document.getElementById('gameIdInput');
const copyBtn = document.getElementById('copyBtn');
const playerNameInput = document.getElementById('playerNameInput');
const connectBtn = document.getElementById('connectBtn');
const playersListDiv = document.getElementById('playersList');
const playersUl = document.getElementById('playersUl');
const startGameBtn = document.getElementById('startGameBtn');

if (!gameId) {
    alert("Oyun ID bulunamadı!");
} else {
    gameIdInput.value = gameId;
}

copyBtn.addEventListener('click', () => {
    navigator.clipboard.writeText(gameIdInput.value).then(() => {
        alert('Oyun ID kopyalandı!');
    });
});

let ws = null;
let playerName = "";

connectBtn.addEventListener('click', () => {
    playerName = playerNameInput.value.trim();
    if (!playerName) {
        alert("Lütfen oyuncu adınızı girin.");
        return;
    }

    ws = new WebSocket(`ws://192.168.1.118:8000/ws/${gameId}/${encodeURIComponent(playerName)}`);

    ws.onopen = () => {
        playersListDiv.classList.remove('d-none');
        connectBtn.disabled = true;
        playerNameInput.disabled = true;

        // Eğer bu oyuncu host ise "Oyunu Başlat" butonunu göster
        if (hostName && hostName === playerName) {
            startGameBtn.classList.remove("d-none");
        }
    };

    ws.onmessage = event => {
        const data = JSON.parse(event.data);

        if (data.type === "player_list") {
            playersUl.innerHTML = "";
            data.players.forEach(p => {
                const li = document.createElement('li');
                li.className = "list-group-item d-flex justify-content-between align-items-center";
                li.textContent = p;

                if (hostName && playerName === hostName) {
                    // host ise butonları göster
                    const btn = document.createElement("button");
                    btn.className = "btn btn-sm btn-outline-info ms-2";
                    btn.textContent = "Jüri Yap";
                    btn.onclick = () => assignJury(p);
                    li.appendChild(btn);
                }

                playersUl.appendChild(li);
            });
        }

        if (data.type === "jury_assigned") {
            alert(`Jüri seçildi: ${data.jury}`);
            const items = playersUl.querySelectorAll("li");
            items.forEach(li => {
                if (li.textContent.includes(data.jury)) {
                    li.classList.add("list-group-item-warning");
                    li.textContent = `${data.jury} (Jüri)`;
                }
            });
        }


        if (data.type === "start_game") {
            // Oyun başlatıldı — yönlendir
            window.location.href = `game.html?game_id=${gameId}&player_name=${encodeURIComponent(playerName)}`;
        }
    };

    function assignJury(player) {
        fetch("http://192.168.1.118:8000/assign-jury", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ game_id: gameId, player_name: player })
        })
            .then(res => res.json())
            .then(data => {
                alert(`${data.jury} jüri olarak atandı.`);
            })
            .catch(err => alert("Jüri atanamadı: " + err.message));
    }

    ws.onclose = () => {
        alert("Bağlantı kesildi.");
        playersListDiv.classList.add('d-none');
        connectBtn.disabled = false;
        playerNameInput.disabled = false;
        playersUl.innerHTML = "";
    };

    ws.onerror = (err) => {
        console.error("WebSocket hata:", err);
        alert("WebSocket bağlantı hatası.");
    };
});

startGameBtn.addEventListener('click', () => {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send("start_game");
    }
});
