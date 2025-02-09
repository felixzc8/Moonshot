import os

MONGODB_URI = os.getenv("MONGODB_URI", "url")
DB_NAME = os.getenv("DB_NAME", "Moonshot")