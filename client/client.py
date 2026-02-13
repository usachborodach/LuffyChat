import json
import requests
import logging
import threading
from flask import Flask, request
app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
config = json.loads(open("config.json", encoding='UTF-8').read())

@app.route('/send_message/', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def handle_all():
    received_data = request.get_json()
    message = f"{received_data['author']}: {received_data['text']}"
    print(message)
    return 'done'

def run_server():
    app.run(host='0.0.0.0', port=5000, debug=False)



threading.Thread(target=run_server, daemon=True).start()
print(f'{__name__} запущен')

while True:
    text = input(f"{config['author']:} ")
    data_to_send = {
        'text': text,
        'author': config['author'],
        'chat': ''
    }
    url = f'http://{config["address"]}:5000/send_message/'
    requests.post(url, json=data_to_send)