from fastapi import APIRouter
from app.database import db

router = APIRouter()

@router.get("/")
def get_tweets():
    tweets_cursor = db.tweets.find()
    tweets = list(tweets_cursor)
    return tweets
