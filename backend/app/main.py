from fastapi import FastAPI
from app.routes import coins, tweets

app = FastAPI(
    title="Moonshot",
    description="An API for suggesting high potential Solana coins",
    version="0.1.0"
)

# Include route modules
app.include_router(coins.router, prefix="/coins")
app.include_router(tweets.router, prefix="/tweets")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
