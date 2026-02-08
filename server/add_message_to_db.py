import mongo

message = {
    'text':'first mes',
    'autor':'human',
    'chat':'human2',
    'time_of_send':'00:00'
}

res = mongo.messages.insert_one(message)
print(res)

mongo.client.close()
