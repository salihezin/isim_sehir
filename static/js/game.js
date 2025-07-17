        const urlParams = new URLSearchParams(window.location.search);
        const gameId = urlParams.get("game_id");
        const playerName = urlParams.get("player_name");

        let currentLetter = "?"; // sunucudan gelecek
        const letterDisplay = document.getElementById("letter");
        const timer = document.getElementById("timer");
        const form = document.getElementById("answerForm");

        const ws = new WebSocket(`ws://192.168.1.118:8000/ws/${gameId}/${playerName}`);

        ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            currentLetter = msg.round_letter || currentLetter;
            letterDisplay.textContent = currentLetter;

            if (msg.type === "start_final_timer") {
                alert("Bir oyuncu bitirdi! 20 saniyeniz kaldı.");

                let remaining = msg.seconds;
                timer.textContent = remaining;

                const interval = setInterval(() => {
                    remaining--;
                    timer.textContent = remaining;

                    if (remaining <= 0) {
                        clearInterval(interval);
                        timer.textContent = "Süre doldu!";
                        form.querySelectorAll("input").forEach(inp => inp.disabled = true);
                        sendAnswers(); // otomatik gönder
                    }
                }, 1000);
            }

            if (msg.type === "show_answers") {
                const categories = ["isim", "sehir", "hayvan", "bitki", "unlu", "esya"];
                let currentCategoryIndex = 0;

                function showNextCategoryModal() {
                    if (currentCategoryIndex >= categories.length) {
                        // Oyun bitti, yeni harf başlat
                        ws.send(JSON.stringify({ type: "next_round" }));
                        return;
                    }

                    const category = categories[currentCategoryIndex];
                    document.getElementById("modalCategoryTitle").textContent = category.toUpperCase() + " Cevapları";

                    const tableBody = document.getElementById("modalAnswerTableBody");
                    tableBody.innerHTML = "";

                    msg.answers.forEach(ans => {
                        const row = document.createElement("tr");

                        const playerCell = document.createElement("td");
                        playerCell.textContent = ans.player;

                        const answerCell = document.createElement("td");
                        answerCell.textContent = ans[category];

                        const itirazCell = document.createElement("td");
                        if (ans.player !== playerName) {
                            const btn = document.createElement("button");
                            btn.className = "btn btn-sm btn-danger";
                            btn.textContent = "İtiraz Et";
                            btn.onclick = () => {
                                if (ws.readyState === WebSocket.OPEN) {
                                    ws.send(JSON.stringify({
                                        type: "challenge_answer",
                                        challenger: playerName,
                                        target: ans.player,
                                        category: category,
                                        answer: ans[category],
                                        round_letter: currentLetter
                                    }));
                                    alert(`${ans.player} adlı oyuncunun "${category}" cevabına itiraz ettiniz.`);
                                }
                            };
                            itirazCell.appendChild(btn);
                        } else {
                            itirazCell.textContent = "-";
                        }

                        row.appendChild(playerCell);
                        row.appendChild(answerCell);
                        row.appendChild(itirazCell);
                        tableBody.appendChild(row);
                    });

                    const modal = new bootstrap.Modal(document.getElementById("answerReviewModal"));
                    modal.show();

                    document.getElementById("nextCategoryBtn").onclick = () => {
                        modal.hide();
                        currentCategoryIndex++;
                        setTimeout(showNextCategoryModal, 500); // bir sonraki modalı aç
                    };
                }

                showNextCategoryModal();
            }
        };

        document.getElementById("finishBtn").addEventListener("click", () => {
            if (ws.readyState === WebSocket.OPEN) {
                ws.send("round_finished");
                sendAnswers(); // bitiren hemen gönderiyor
                form.querySelectorAll("input").forEach(inp => inp.disabled = true);
            }
        });

        function sendAnswers() {
            const formData = new FormData(form);
            console.log('Form Data:', formData);

            const cevaplar = Object.fromEntries(formData.entries());
            console.log('***', cevaplar);


            const payload = {
                game_id: gameId,
                player_name: playerName,
                round_letter: currentLetter,
                isim: cevaplar.isim || "",
                sehir: cevaplar.sehir || "",
                hayvan: cevaplar.hayvan || "",
                bitki: cevaplar.bitki || "",
                unlu: cevaplar.unlu || "",
                esya: cevaplar.esya || ""
            };

            fetch(`http://192.168.1.118:8000/submit-answer`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            }).then(res => {
                if (!res.ok) throw new Error("Cevaplar gönderilemedi.");
            }).catch(err => console.error(err));
        }
