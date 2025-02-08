# test_db.py
from pymongo import MongoClient
from datetime import datetime
from app.config import MONGODB_URI, DB_NAME

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

def test_tweets():
    tweets_collection = db.tweets
    
    # Sample tweet document
    test_tweet = {
        "tweet_id": "1234567890",
        "username": "crypto_whale",
        "tweet_body": "Found a new gem! $PEPE is going to explode! 🚀 #memecoin #crypto",
        "url": "https://twitter.com/crypto_whale/status/1234567890",
        "timestamp": datetime.utcnow(),
        "language": "en",
        "view_count": 5000,
        "reply_count": 100,
        "retweet_count": 250,
        "like_count": 800,
        "quote_count": 30,
        "hashtags": ["memecoin", "crypto"],
        "mentioned_users": ["@elonmusk"],
        "links": ["https://example.com"],
        "sentiment_score": 0.9,
        "is_verified_author": True,
        "follower_count": 100000,
        "engagement_rate": 0.05,
        "contains_memecoin_reference": True,
        "referenced_coins": ["PEPE"]
    }
    
    # Insert tweet
    tweet_result = tweets_collection.insert_one(test_tweet)
    print("\nTweet Test:")
    print("Inserted tweet with id:", tweet_result.inserted_id)
    
    # Fetch tweet
    fetched_tweet = tweets_collection.find_one({"tweet_id": "1234567890"})
    print("Fetched tweet:", fetched_tweet)

def test_coins():
    coins_collection = db.coins
    
    # Sample coin document
    test_coin = {
        "symbol": "PEPE",
        "name": "Pepe Coin",
        "contract_address": "0x6982508145454ce325ddbe47a25d4ec3d2311933",
        "chain": "ETH",
        "first_seen": datetime.utcnow(),
        "discovery_price": 0.000001,
        "discovery_tweet": "1234567890",
        "current_price": 0.000002,
        "market_cap": 1000000,
        "volume_24h": 500000,
        "price_change_24h": 15.5,
        "telegram_members": 5000,
        "twitter_followers": 10000,
        "website": "https://pepecoin.example.com",
        "pump_score": 0.85,
        "risk_level": 4,
        "analysis_history": [{
            "timestamp": datetime.utcnow(),
            "sentiment_score": 0.8,
            "trend_direction": "bullish",
            "key_influencers": ["@crypto_whale", "@meme_master"],
            "tweet_volume_24h": 1500,
            "tweet_sentiment_distribution": {
                "positive": 0.7,
                "neutral": 0.2,
                "negative": 0.1
            }
        }],
        "is_trending": True,
        "is_verified_contract": True,
        "is_honeypot": False,
        "categories": ["meme", "community"],
        "gemini_insights": {
            "community_strength": "high",
            "viral_potential": "very_high",
            "market_timing": "favorable"
        },
        "key_factors": [
            "Strong meme appeal",
            "Active developer team",
            "Growing social media presence"
        ]
    }
    
    # Insert coin
    coin_result = coins_collection.insert_one(test_coin)
    print("\nCoin Test:")
    print("Inserted coin with id:", coin_result.inserted_id)
    
    # Fetch coin
    fetched_coin = coins_collection.find_one({"symbol": "PEPE"})
    print("Fetched coin:", fetched_coin)

if __name__ == "__main__":
    try:
        # Test connection
        test_collection = db.test
        test_result = test_collection.insert_one({"name": "MongoDB Test", "status": "connected"})
        print("MongoDB Connection Test:")
        print("Inserted test document with id:", test_result.inserted_id)
        
        # Run model tests
        test_tweets()
        test_coins()
        
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        client.close()