import requests

input_data = input("text;author;chat\n")
input_data = input_data.split(';')
data = {
    'text': input_data[0],
    'author': input_data[1],
    'chat': input_data[2]
}
url = 'http://192.168.1.11:8000/send_message/'
requests.post(url, json=data)