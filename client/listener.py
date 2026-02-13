from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def handle_all():
    data = request.get_json()
    message = f"{data['author']}: {data['text']}"
    print(message)

app.run(host='0.0.0.0', port=5000, debug=False)