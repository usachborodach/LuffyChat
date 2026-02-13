import json
import requests

config = json.loads(open("config.json", encoding='UTF-8').read())
print('post.py запущен')
text = input()
data = {
    'text': text,
    'author': config['author'],
    'chat': ''
}
url = f'http://{config["adress"]}:5000/send_message/'
requests.post(url, json=data)
