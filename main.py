from fastapi import Body, Depends, FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import Base, SessionLocal, engine
from game_manager import game_manager
from models import PlayerAnswer



app = FastAPI()
Base.metadata.create_all(bind=engine)

# Basit CORS ayarı
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Oda bazlı WebSocket bağlantıları
connected_clients = {}  # game_id -> [WebSocket, ...]

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/create-game")
async def create_game_endpoint(request: Request):
    data = await request.json()
    host_name = data.get("host_name")
    if not host_name:
        return {"error": "host_name gerekli"}

    round_time = data.get("round_time", 20)
    game_id = game_manager.create_game(host_name, round_time)
    print(f"Oyun oluşturuldu: {game_id} sahibi: {host_name}")
    return {"game_id": game_id}


@app.websocket("/ws/{game_id}/{player_name}")
async def websocket_endpoint(websocket: WebSocket, game_id: str, player_name: str):
    await websocket.accept()

    if game_id not in connected_clients:
        connected_clients[game_id] = []

    connected_clients[game_id].append(websocket)
    game_manager.join_game(game_id, player_name)
    print(f"{player_name} oyuna katıldı: {game_id}")

    try:
        await notify_players(game_id)

        while True:
            data = await websocket.receive_text()
            print(f"[{game_id}] {player_name} mesaj gönderdi: {data}")

            # Eğer JSON mesajsa ayrıştır
            try:
                import json
                msg = json.loads(data)
            except Exception:
                msg = None

            # Basit metin mesajları
            if data == "start_game":
                for client in connected_clients.get(game_id, []):
                    await client.send_json({"type": "start_game"})

            elif data == "round_finished":
                if not game_manager.has_round_ended(game_id):
                    game_manager.set_round_ended(game_id)
                    print(f"{player_name} ilk bitiren oldu.")
                    await notify_start_final_timer(game_id)

                import asyncio
                await asyncio.sleep(22)  # 20 sn + 2 sn buffer
                await broadcast_answers(game_id)

            # İtiraz mesajı geldiğinde
            elif msg and msg.get("type") == "challenge_answer":
                # Örnek msg:
                # {
                #   "type": "challenge_answer",
                #   "challenger": "Ayşe",
                #   "target": "Hasan",
                #   "category": "isim",
                #   "answer": "Slovakya",
                #   "round_letter": "S"
                # }

                # Jüriye veya tüm oyunculara bildir
                challenge_info = {
                    "type": "new_challenge",
                    "challenger": msg.get("challenger"),
                    "target": msg.get("target"),
                    "category": msg.get("category"),
                    "answer": msg.get("answer"),
                    "round_letter": msg.get("round_letter")
                }

                await broadcast(game_id, challenge_info)

            # Jüri itirazı cevapladı (onay/red)
            elif msg and msg.get("type") == "challenge_response":
                # Örnek msg:
                # {
                #   "type": "challenge_response",
                #   "challenge_id": "some_id", (isteğe bağlı, sen kendin id ekleyebilirsin)
                #   "approved": True / False
                # }

                response_info = {
                    "type": "challenge_result",
                    "challenge_id": msg.get("challenge_id"),
                    "approved": msg.get("approved")
                }

                await broadcast(game_id, response_info)

    except WebSocketDisconnect:
        connected_clients[game_id].remove(websocket)
        game_manager.leave_game(game_id, player_name)
        await notify_players(game_id)


@app.post("/submit-answer")
async def submit_answers(
    answer_data: dict = Body(...),
    db: Session = Depends(get_db)
):
    # Zorunlu alan kontrolü
    required_fields = ["game_id", "player_name", "round_letter"]
    for field in required_fields:
        if field not in answer_data:
            raise HTTPException(status_code=400, detail=f"{field} alanı eksik.")
        
    answer = PlayerAnswer(
        game_id=answer_data["game_id"],
        player_name=answer_data["player_name"],
        round_letter=answer_data["round_letter"],
        answer_isim=answer_data.get("isim", ""),
        answer_sehir=answer_data.get("sehir", ""),
        answer_hayvan=answer_data.get("hayvan", ""),
        answer_bitki=answer_data.get("bitki", ""),
        answer_unlu=answer_data.get("unlu", ""),
        answer_esya=answer_data.get("esya", ""),
    )

    db.add(answer)
    db.commit()
    db.refresh(answer)
    
    return {"message": "Cevap başarıyla kaydedildi", "answer_id": answer.id}

from fastapi import HTTPException

@app.post("/assign-jury")
async def assign_jury(request: Request):
    data = await request.json()
    game_id = data.get("game_id")
    player_name = data.get("player_name")

    if not game_id or not player_name:
        raise HTTPException(status_code=400, detail="game_id ve player_name gereklidir.")

    game_manager.assign_jury(game_id, player_name)

    # Tüm oyunculara jüri bilgisi gönder
    await notify_jury_assigned(game_id)

    return {"message": "Jüri atandı", "jury": player_name}

@app.get("/get-answers/{game_id}/{letter}")
async def get_answers(game_id: str, letter: str):
    db: Session = SessionLocal()
    answers = db.query(PlayerAnswer).filter(
        PlayerAnswer.game_id == game_id,
        PlayerAnswer.round_letter == letter
    ).all()

    return [
        {
            "player": a.player_name,
            "isim": a.answer_isim,
            "sehir": a.answer_sehir,
            "hayvan": a.answer_hayvan,
            "bitki": a.answer_bitki,
            "unlu": a.answer_unlu,
            "esya": a.answer_esya,
        }
        for a in answers
    ]
        
async def notify_start_final_timer(game_id: str):

    for client in connected_clients.get(game_id, []):
        try:
            await client.send_json({
                "type": "start_final_timer",
                "seconds": 20,
            })
        except Exception as e:
            print(f"Final timer mesajı gönderilemedi: {e}")


# Yayın mesajı
async def broadcast(game_id: str, message: dict):
    for client in connected_clients.get(game_id, []):
        try:
            await client.send_json(message)
        except Exception as e:
            print(f"Yayın hatası: {e}")


# Katılımcılara oyuncu listesini gönder
async def notify_players(game_id: str):
    players = game_manager.get_players(game_id)
    message = {
        "type": "player_list",
        "players": players,
        "jury": game_manager.get_jury(game_id),
        "round_letter": game_manager.get_round_letter(game_id),
    }

    for client in connected_clients.get(game_id, []):
        print(f"Yayında oyuncu listesi: {players}")
        try:
            await client.send_json(message)
        except Exception as e:
            print(f"Mesaj gönderilemedi: {e}")

async def notify_jury_assigned(game_id: str):
    jury = game_manager.get_jury(game_id)
    message = {
        "type": "jury_assigned",
        "jury": jury
    }

    for client in connected_clients.get(game_id, []):
        try:
            await client.send_json(message)
        except Exception as e:
            print(f"Jüri bilgisi gönderilemedi: {e}")

async def notify_jury_selected(game_id: str, jury_name: str):
    message = {
        "type": "jury_assigned",
        "jury": jury_name
    }

    for client in connected_clients.get(game_id, []):
        try:
            await client.send_json(message)
        except Exception as e:
            print(f"Jüri bilgisi gönderilemedi: {e}")


# Oyuncu cevaplarını tüm oyunculara gönder
async def broadcast_answers(game_id: str):
    from database import SessionLocal
    from models import PlayerAnswer

    db = SessionLocal()
    letter = game_manager.get_round_letter(game_id)

    answers = db.query(PlayerAnswer).filter(
        PlayerAnswer.game_id == game_id,
        PlayerAnswer.round_letter == letter
    ).all()

    response = {
        "type": "show_answers",
        "answers": [
            {
                "player": ans.player_name,
                "isim": ans.answer_isim,
                "sehir": ans.answer_sehir,
                "hayvan": ans.answer_hayvan,
                "bitki": ans.answer_bitki,
                "unlu": ans.answer_unlu,
                "esya": ans.answer_esya,
            }
            for ans in answers
        ]
    }

    for client in connected_clients.get(game_id, []):
        await client.send_json(response)