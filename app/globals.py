from pymongo import MongoClient
from os import getenv

def ObjectId_to_str(input: list):
    for i,_ in enumerate(input):
        input[i]["_id"] = str(input[i]["_id"])
    return input

upload_folder = getenv("UPLOAD_FOLDER")
client = MongoClient(getenv("MONGO_URL"))
secret_key = getenv("SECRET_KEY")

db = client["DoF-gratuity"]
DoF = db["DoF"]
User = db["User"]

