let ws;

document.getElementById("connectBtn").onclick = () => {
    const gameId = document.getElementById("gameId").value.trim();
    const playerName = document.getElementById("playerName").value.trim();

    if (!gameId || !playerName) {
        alert("Lütfen oyun ID ve oyuncu adını girin.");
        return;
    }

    // WebSocket bağlantısını aç
    ws = new WebSocket(`ws://192.168.1.118:8000/ws/${gameId}/${playerName}`);

    ws.onopen = () => {
        console.log("WebSocket bağlantısı açıldı.");
        alert("Odaya bağlandınız!");
    };

    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.type === "player_list") {
            const ul = document.getElementById("playersList");
            ul.innerHTML = "";
            msg.players.forEach(p => {
                const li = document.createElement("li");
                li.classList.add("list-group-item");
                li.textContent = p;
                ul.appendChild(li);
            });
        }
    };

    ws.onclose = () => {
        alert("Bağlantı kapandı.");
    };

    ws.onerror = (err) => {
        alert("Bağlantı hatası!");
        console.error(err);
    };
};
