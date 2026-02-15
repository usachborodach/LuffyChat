import sys
import json
import requests
import logging
import threading
from flask import Flask, request
app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
config = json.loads(open("config.json", encoding='UTF-8').read())

history = open('history.log', encoding="UTF-8").read()
print(history)


@app.route('/send_message/', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def listen():
    received_data = request.get_json()
    in_message = f"{received_data['author']}: {received_data['text']}"
    with open('history.log', 'a', encoding='UTF-8') as file:
        file.write(in_message)
    return 'done'

def run_server():
    app.run(host='0.0.0.0', port=5000, debug=False)
threading.Thread(target=run_server, daemon=True).start()



while True:
    text = input()
    sys.stdout.write('\033[F')
    sys.stdout.write('\033[K')

    out_message = f"{config['author']}: {text}"
    print(out_message)
    with open('history.log', 'a', encoding='UTF-8') as file:
        file.write(out_message)

    data_to_send = {
        'text': text,
        'author': config['author'],
        'chat': ''
    }
    url = f'http://{config["address"]}:5000/send_message/'
    requests.post(url, json=data_to_send)