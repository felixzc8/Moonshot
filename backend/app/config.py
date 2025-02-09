import os

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://felixzc8:JtIy6G8fHIjowsNo@cluster0.larn4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DB_NAME = os.getenv("DB_NAME", "Moonshot")