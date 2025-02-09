from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from bson import ObjectId
from app.models.coins import Coin, CoinsListResponse, CoinResponse
from app.database import db

router = APIRouter(
    prefix="/coins",
    tags=["coins"]
)

@router.get("/{coin_id}", response_model=CoinResponse)
async def get_coin(coin_id: str):
    """
    Retrieve a specific coin by its ID.
    
    - **coin_id**: The MongoDB ObjectId of the coin
    """
    try:
        # Validate and convert string ID to ObjectId
        if not ObjectId.is_valid(coin_id):
            raise HTTPException(status_code=400, detail="Invalid coin ID format")
            
        coin = await db.coins.find_one({"_id": ObjectId(coin_id)})
        
        if coin is None:
            raise HTTPException(status_code=404, detail="Coin not found")

        return {
            "status": "success",
            "data": coin
        }

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error retrieving coin: {str(e)}")

@router.get("/", response_model=CoinsListResponse)
async def get_coins(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    min_pump_score: Optional[float] = Query(None, ge=0, le=1, description="Minimum pump score"),
    is_trending: Optional[bool] = Query(None, description="Filter by trending status"),
    sort_by: str = Query("pump_score", description="Sort field"),
    sort_order: int = Query(-1, ge=-1, le=1, description="Sort order: -1 for descending, 1 for ascending")
):
    """
    Retrieve all coins with filtering and pagination options.
    
    - **page**: Page number (starts from 1)
    - **limit**: Number of items per page
    - **min_pump_score**: Filter coins by minimum pump score
    - **is_trending**: Filter by trending status
    - **sort_by**: Field to sort by (default: pump_score)
    - **sort_order**: Sort direction (-1 for descending, 1 for ascending)
    """
    try:
        # Build filter query
        filter_query = {}
        if min_pump_score is not None:
            filter_query["pump_score"] = {"$gte": min_pump_score}
        if is_trending is not None:
            filter_query["is_trending"] = is_trending

        # Calculate skip for pagination
        skip = (page - 1) * limit

        # Get total count for pagination
        total_count = await db.coins.count_documents(filter_query)

        # Get coins with pagination
        cursor = db.coins.find(filter_query)
        
        # Apply sorting
        cursor = cursor.sort(sort_by, sort_order)
        
        # Apply pagination
        cursor = cursor.skip(skip).limit(limit)
        
        # Convert cursor to list
        coins = await cursor.to_list(length=limit)

        return {
            "status": "success",
            "data": coins,
            "total": total_count,
            "page": page,
            "limit": limit
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving coins: {str(e)}")