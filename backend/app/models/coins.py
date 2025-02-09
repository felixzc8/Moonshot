from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, HttpUrl
from bson import ObjectId
from enum import Enum

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

class TrendDirection(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"

class CoinAnalysis(BaseModel):
    timestamp: datetime = Field(..., description="Analysis timestamp")
    sentiment_score: float = Field(..., description="Overall sentiment score from -1 to 1")
    trend_direction: TrendDirection = Field(..., description="Current trend direction")
    key_influencers: List[str] = Field(default_factory=list, description="Notable accounts discussing the coin")
    tweet_volume_24h: int = Field(..., description="Number of tweets in last 24 hours")
    tweet_sentiment_distribution: Dict[str, float] = Field(
        ..., 
        description="Distribution of sentiment in tweets (positive/negative/neutral)"
    )

class Coin(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    symbol: str = Field(..., description="Coin symbol (e.g., PEPE)")
    name: str = Field(..., description="Full name of the coin")
    contract_address: Optional[str] = Field(None, description="Smart contract address")
    chain: str = Field(..., description="Blockchain (e.g., ETH, BSC)")
    
    # Discovery info
    first_seen: datetime = Field(..., description="When the coin was first detected")
    discovery_price: float = Field(..., description="Price at first detection")
    discovery_tweet: str = Field(..., description="Tweet ID that first mentioned the coin")
    
    # Market data
    current_price: Optional[float] = Field(None, description="Current price in USD")
    market_cap: Optional[float] = Field(None, description="Current market cap in USD")
    volume_24h: Optional[float] = Field(None, description="24h trading volume")
    price_change_24h: Optional[float] = Field(None, description="24h price change percentage")
    
    # Social metrics
    telegram_members: Optional[int] = Field(None, description="Number of Telegram group members")
    twitter_followers: Optional[int] = Field(None, description="Number of Twitter followers")
    website: Optional[HttpUrl] = Field(None, description="Project website")
    
    # Analysis data
    pump_score: float = Field(..., description="Calculated probability of pumping (0-1)")
    risk_level: int = Field(..., description="Risk assessment (1-5)")
    analysis_history: List[CoinAnalysis] = Field(default_factory=list, description="Historical analysis data")
    
    # Flags and categories
    is_trending: bool = Field(default=False, description="Currently trending status")
    is_verified_contract: bool = Field(default=False, description="Contract verification status")
    is_honeypot: bool = Field(default=False, description="Honeypot detection flag")
    categories: List[str] = Field(default_factory=list, description="Categories (e.g., meme, defi)")
    
    # Gemini analysis results
    gemini_insights: Dict[str, any] = Field(
        default_factory=dict, 
        description="Raw insights from Gemini analysis"
    )
    key_factors: List[str] = Field(
        default_factory=list, 
        description="Key factors identified by Gemini"
    )
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "symbol": "PEPE",
                "name": "Pepe Coin",
                "contract_address": "0x6982508145454ce325ddbe47a25d4ec3d2311933",
                "chain": "ETH",
                "first_seen": "2024-02-08T12:00:00Z",
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
                    "timestamp": "2024-02-08T12:00:00Z",
                    "sentiment_score": 0.75,
                    "trend_direction": "bullish",
                    "key_influencers": ["@crypto_whale", "@meme_master"],
                    "tweet_volume_24h": 1500,
                    "tweet_sentiment_distribution": {
                        "positive": 0.65,
                        "neutral": 0.25,
                        "negative": 0.10
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
        }

# Response Models
class CoinResponse(BaseModel):
    status: str
    data: Coin

class CoinsListResponse(BaseModel):
    status: str
    data: List[Coin]
    total: int
    page: int
    limit: int