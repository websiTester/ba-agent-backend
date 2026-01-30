import os
from dotenv import load_dotenv
from pymongo import MongoClient


load_dotenv()
MONGO_URI = os.getenv("MONGODB_URI")

def get_connection():
    client = MongoClient(MONGO_URI)
    
    client.admin.command('ping')
    print("✅ Kết nối MongoDB thành công!")
    db = client["ai_system_db"]
    print("Connected to MongoDB")
    return db


def get_db_connection(dbName: str):
    client = MongoClient(MONGO_URI)
    
    client.admin.command('ping')
    print("✅ Kết nối MongoDB thành công!")
    db = client[dbName]
    print("Connected to MongoDB")
    return db


if __name__ == "__main__":
    get_connection()