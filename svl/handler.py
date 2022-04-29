import telegram
import pymongo
import requests
import os

TOKEN = os.environ['TELEGRAM_TOKEN']
MONGO_TOKEN = os.environ['MONGO_PASSWORD']
chosen_messages = {}


def generate_message(user_type, messages_collection):
    if user_type in chosen_messages:
        return chosen_messages[user_type]
    message = messages_collection[user_type].find_one_and_update(
        {},
        {'$inc': {"count": 1}},
        {'_id': 0},
        sort=[("count", 1), ("priority", 1)]
    )['message']
    chosen_messages[user_type] = message
    return message


def send_message(event, context):
    myquirkydb_client = pymongo.MongoClient(
        "mongodb+srv://myquirkybot:" +
        MONGO_TOKEN +
        "@cluster0.imta3.mongodb.net/myquirkydb?retryWrites=true&w=majority")

    bot = telegram.Bot(token=TOKEN)

    usertype_collection = myquirkydb_client.myquirkydb.usertype
    update_collection = myquirkydb_client.myquirkydb.lastupdate
    messages_collection = myquirkydb_client.myquirkymessages

    telegram_users = usertype_collection.find({}, {"_id": 0})
    last_updated = update_collection.find_one({}, {'_id': 0})['last_updated']
    update_object = update_collection.find_one({}, {})['_id']
    r = requests.get('https://api.telegram.org/bot' + TOKEN + '/getUpdates?offset=' + str(last_updated + 1))
    formatted = r.json()['result']

    for new_request in formatted:
        if new_request.get('message', None) and new_request['message'].get('text', None):
            if new_request['message']['text'].casefold() == '/start@myquirkybot'.casefold():
                if not usertype_collection.find_one({'chat_id': new_request['message']['chat']['id']}):
                    usertype_collection.insert_one({'chat_id': new_request['message']['chat']['id'], 'type': 'default'})
            if new_request['message']['text'].casefold() == '/stop@myquirkybot'.casefold():
                usertype_collection.delete_many({'chat_id': new_request['message']['chat']['id']})
            continue

        if new_request.get('channel_post', None) and new_request['channel_post'].get('text', None):
            if new_request['channel_post']['text'].casefold() == '/start@myquirkybot'.casefold():
                if not usertype_collection.find_one({'chat_id': new_request['channel_post']['chat']['id']}):
                    usertype_collection.insert_one(
                        {'chat_id': new_request['channel_post']['chat']['id'], 'type': 'default'})
            if new_request['channel_post']['text'].casefold() == '/stop@myquirkybot'.casefold():
                usertype_collection.delete_many({'chat_id': new_request['channel_post']['chat']['id']})
            continue

    if formatted:
        # update last_update
        update_collection.update_one({'_id': update_object}, {"$set": {'last_updated': formatted[-1]['update_id']}}, upsert=True)

    for document in telegram_users:
        chat_id, user_type = document['chat_id'], document['type']
        message = generate_message(user_type, messages_collection)
        try:
            bot.sendMessage(chat_id=chat_id, text=message)
        except:
            usertype_collection.delete_many({'chat_id': chat_id})

# send_message(None, None)