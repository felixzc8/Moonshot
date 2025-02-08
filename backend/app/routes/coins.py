from fastapi import APIRouter
from app.database import db
from backend.app.models.tweets import Coin
from typing import List

router = APIRouter()

@router.get("/", response_model=List[Coin])
def get_coins():
    # For simplicity, assume each document in the "coins" collection matches the Coin model
    coins_cursor = db.coins.find()
    coins = list(coins_cursor)
    return coins
