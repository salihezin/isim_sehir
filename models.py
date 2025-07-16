from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database import Base

class PlayerAnswer(Base):
    __tablename__ = "player_answers"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(String, index=True, nullable=False)
    player_name = Column(String, index=True, nullable=False)
    round_letter = Column(String, nullable=False)

    answer_isim = Column(String, default="")
    answer_sehir = Column(String, default="")
    answer_hayvan = Column(String, default="")
    answer_bitki = Column(String, default="")
    answer_unlu = Column(String, default="")
    answer_esya = Column(String, default="")

    created_at = Column(DateTime, default=datetime.utcnow)
