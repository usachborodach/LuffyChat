import requests

print('post.py запущен')
text = input_data()
data = {
    'text': text,
    'author': 'Луффи',
    'chat': ''
}
url = 'http://192.168.1.10:8000/send_message/'
requests.post(url, json=data)