import mongo
from fastapi import FastAPI, HTTPException
from datetime import datetime
import uvicorn
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

class MessageModel(BaseModel):
    text: Optional[str] = None
    author: Optional[str] = None
    chat: Optional[str] = None

@app.post("/send_message/")
async def send_message(message_data: MessageModel):
    try:
        message = {
            'text': message_data.text,
            'author': message_data.author,
            'chat': message_data.chat,
            'time_of_send': datetime.now() }
        res = mongo.messages.insert_one(message)

        return {
            'status': 'done',
            'message_id': str(res.inserted_id),
            'message': 'Message successfully saved'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving message: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("rest_api:app", host="0.0.0.0", port=8000, reload=True)

# mongo.client.close()
"""
curl -X POST "http://localhost:8000/send_message/" \
     -H "Content-Type: application/json" \
     -d '{"text": "Hello world", "author": "John", "chat": "general"}'
"""