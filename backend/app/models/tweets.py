from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl
from bson import ObjectId

# Custom field for MongoDB ObjectId handling
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

# Tweet Model
class Tweet(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    tweet_id: str = Field(..., description="Original Twitter/X tweet ID")
    username: str = Field(..., description="Username of tweet author")
    tweet_body: str = Field(..., description="Content of the tweet")
    url: HttpUrl = Field(..., description="URL of the tweet")
    timestamp: datetime = Field(..., description="Tweet creation timestamp")
    language: str = Field(..., description="Language of the tweet")
    
    # Engagement metrics
    view_count: Optional[int] = Field(default=0, description="Number of views")
    reply_count: int = Field(default=0, description="Number of replies")
    retweet_count: int = Field(default=0, description="Number of retweets")
    like_count: int = Field(default=0, description="Number of likes")
    quote_count: int = Field(default=0, description="Number of quote tweets")
    
    # Content analysis
    hashtags: List[str] = Field(default_factory=list, description="Hashtags used in tweet")
    mentioned_users: List[str] = Field(default_factory=list, description="Users mentioned in tweet")
    links: List[HttpUrl] = Field(default_factory=list, description="URLs included in tweet")
    
    # Additional suggested fields for memecoin analysis
    sentiment_score: Optional[float] = Field(None, description="Sentiment analysis score")
    is_verified_author: bool = Field(default=False, description="Whether the author is verified")
    follower_count: Optional[int] = Field(None, description="Author's follower count at tweet time")
    engagement_rate: Optional[float] = Field(None, description="Engagement rate calculation")
    contains_memecoin_reference: bool = Field(default=False, description="Whether tweet mentions memecoins")
    referenced_coins: List[str] = Field(default_factory=list, description="Memecoin symbols mentioned")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "tweet_id": "1234567890",
                "username": "crypto_influencer",
                "tweet_body": "New #memecoin alert! $DOGE to the moon! 🚀",
                "url": "https://twitter.com/username/status/1234567890",
                "timestamp": "2024-02-08T12:00:00Z",
                "language": "en",
                "view_count": 10000,
                "reply_count": 150,
                "retweet_count": 500,
                "like_count": 1000,
                "quote_count": 50,
                "hashtags": ["memecoin", "crypto"],
                "mentioned_users": ["@elonmusk"],
                "links": ["https://example.com"],
                "sentiment_score": 0.8,
                "is_verified_author": True,
                "follower_count": 50000,
                "engagement_rate": 0.05,
                "contains_memecoin_reference": True,
                "referenced_coins": ["DOGE"]
            }
        }

# Response Models (for API endpoints)
class TweetResponse(BaseModel):
    status: str
    data: Tweet

class TweetsListResponse(BaseModel):
    status: str
    data: List[Tweet]
    total: int
    page: int
    limit: int