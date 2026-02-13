from flask import Flask, request, jsonify
app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route('/send_message/', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def handle_all():
    data = request.get_json()
    message = f"{data['author']}: {data['text']}"
    print(message)
    return 'done'

app.run(host='0.0.0.0', port=5000, debug=False)