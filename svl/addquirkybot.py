import telegram
import pymongo
import requests
import os

# remember to add token in environment
MONGO_TOKEN = os.environ['MONGO_PASSWORD']

new_messages = {
    "default": ["The person below is a faggot"]
}


def convert_mongo(text):
    return {"message": text, "count": 0, "priority": 1}


def handle_messages():
    for key, value in new_messages.items():
        new_messages[key] = list(map(convert_mongo, value))


def send_message():
    myquirkydb_client = pymongo.MongoClient(
        "mongodb+srv://myquirkybot:" +
        MONGO_TOKEN +
        "@cluster0.imta3.mongodb.net/myquirkydb?retryWrites=true&w=majority")

    handle_messages()
    messages_collection = myquirkydb_client.myquirkymessages

    for key, value in new_messages.items():
        current_collection = messages_collection[key]
        current_collection.insert_many(value)

send_message()