import json
import threading
import time
from datetime import datetime
from flask import Flask, request, jsonify
import requests
import socket
from pymongo import MongoClient
from bson import json_util
from bson.objectid import ObjectId

app = Flask(__name__)

class MongoMessenger:
    def __init__(self, host='0.0.0.0', port=5000, mongo_uri="mongodb://172.29.1.9:27017"):
        self.host = host
        self.port = port
        
        # Подключение к MongoDB
        try:
            self.mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            self.mongo_client.server_info()  # Проверка подключения
            self.db = self.mongo_client['LuffyChat']
            self.messages_collection = self.db['messages']
            self.users_collection = self.db['users']
            print(f"✅ Успешное подключение к MongoDB: {mongo_uri}")
        except Exception as e:
            print(f"❌ Ошибка подключения к MongoDB: {e}")
            raise
        
        self.peers = {}  # Локальный кэш пиров
        self.last_message_id = None
        self.my_username = socket.gethostname()
        
        # Создаем индексы в MongoDB
        self._create_indexes()
        
        # Регистрируем текущего пользователя в базе
        self._register_user()
    
    def _create_indexes(self):
        """Создание индексов в MongoDB для оптимизации"""
        self.messages_collection.create_index([("timestamp", -1)])
        self.messages_collection.create_index([("sender", 1), ("receiver", 1)])
        self.users_collection.create_index([("username", 1)], unique=True)
    
    def _register_user(self):
        """Регистрация пользователя в базе данных"""
        try:
            self.users_collection.update_one(
                {"username": self.my_username},
                {"$set": {
                    "username": self.my_username,
                    "ip": self.get_local_ip(),
                    "port": self.port,
                    "last_seen": datetime.now(),
                    "status": "online"
                }},
                upsert=True
            )
        except Exception as e:
            print(f"Ошибка при регистрации пользователя: {e}")
    
    def get_local_ip(self):
        """Получаем локальный IP адрес"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def start(self):
        """Запуск сервера в отдельном потоке"""
        thread = threading.Thread(target=self.run_server)
        thread.daemon = True
        thread.start()
        print(f"Сервер запущен на http://{self.get_local_ip()}:{self.port}")
        
        # Запуск потока для проверки новых сообщений
        update_thread = threading.Thread(target=self.check_new_messages)
        update_thread.daemon = True
        update_thread.start()
    
    def run_server(self):
        """Запуск Flask сервера"""
        app.run(host=self.host, port=self.port, debug=False)
    
    def add_peer(self, name, url):
        """Добавление другого пользователя в локальный кэш"""
        self.peers[name] = url
        print(f"Добавлен пир: {name} -> {url}")
        
        # Также обновляем информацию в MongoDB
        try:
            self.users_collection.update_one(
                {"username": name},
                {"$set": {
                    "url": url,
                    "last_updated": datetime.now()
                }},
                upsert=True
            )
        except Exception as e:
            print(f"Ошибка при сохранении пира в БД: {e}")
    
    def send_message_to_db(self, receiver, text):
        """Отправка сообщения через сохранение в MongoDB"""
        try:
            message = {
                'sender': self.my_username,
                'receiver': receiver,
                'text': text,
                'timestamp': datetime.now(),
                'status': 'sent',
                'read': False
            }
            
            # Сохраняем сообщение в MongoDB
            result = self.messages_collection.insert_one(message)
            message['_id'] = result.inserted_id
            
            print(f"Сообщение сохранено в БД для {receiver}")
            return True
                
        except Exception as e:
            print(f"Ошибка при сохранении в БД: {e}")
            return False
    
    def get_all_messages(self, limit=100):
        """Получение всех сообщений из MongoDB"""
        try:
            cursor = self.messages_collection.find({
                "$or": [
                    {"sender": self.my_username},
                    {"receiver": self.my_username},
                    {"receiver": "all"}  # Для групповых сообщений
                ]
            }).sort("timestamp", -1).limit(limit)
            
            messages = list(cursor)
            # Конвертируем ObjectId и datetime в строки
            for msg in messages:
                if '_id' in msg:
                    msg['_id'] = str(msg['_id'])
                if 'timestamp' in msg and isinstance(msg['timestamp'], datetime):
                    msg['timestamp'] = msg['timestamp'].isoformat()
            
            return messages[::-1]  # Возвращаем в хронологическом порядке
        except Exception as e:
            print(f"Ошибка при получении сообщений: {e}")
            return []
    
    def get_unread_messages(self):
        """Получение непрочитанных сообщений"""
        try:
            cursor = self.messages_collection.find({
                "receiver": self.my_username,
                "read": False
            }).sort("timestamp", 1)
            
            messages = list(cursor)
            # Помечаем как прочитанные
            for msg in messages:
                self.messages_collection.update_one(
                    {"_id": msg['_id']},
                    {"$set": {"read": True}}
                )
                
            # Конвертируем ObjectId и datetime
            for msg in messages:
                if '_id' in msg:
                    msg['_id'] = str(msg['_id'])
                if 'timestamp' in msg and isinstance(msg['timestamp'], datetime):
                    msg['timestamp'] = msg['timestamp'].isoformat()
            
            return messages
        except Exception as e:
            print(f"Ошибка при получении непрочитанных: {e}")
            return []
    
    def get_online_users(self):
        """Получение списка онлайн пользователей"""
        try:
            five_minutes_ago = datetime.now().timestamp() - 300  # 5 минут
            cursor = self.users_collection.find({
                "last_seen": {"$gte": datetime.fromtimestamp(five_minutes_ago)},
                "username": {"$ne": self.my_username}
            })
            
            users = []
            for user in cursor:
                users.append({
                    'username': user.get('username', 'Unknown'),
                    'ip': user.get('ip', ''),
                    'port': user.get('port', ''),
                    'status': user.get('status', 'offline')
                })
            
            return users
        except Exception as e:
            print(f"Ошибка при получении пользователей: {e}")
            return []
    
    def check_new_messages(self):
        """Фоновая проверка новых сообщений"""
        while True:
            try:
                # Получаем последнее сообщение ID для этого пользователя
                last_msg = self.messages_collection.find_one({
                    "$or": [
                        {"sender": self.my_username},
                        {"receiver": self.my_username}
                    ]
                }, sort=[("timestamp", -1)])
                
                if last_msg and last_msg['_id'] != self.last_message_id:
                    self.last_message_id = last_msg['_id']
                    
                    # Если это новое входящее сообщение
                    if last_msg.get('receiver') == self.my_username and not last_msg.get('read', True):
                        print(f"\n📨 Новое сообщение от {last_msg.get('sender')}:")
                        print(f"   {last_msg.get('text', '')}")
                        print(f"   {last_msg.get('timestamp', '').strftime('%H:%M:%S') if isinstance(last_msg.get('timestamp'), datetime) else ''}")
                        print("-" * 40)
                
                # Обновляем статус онлайн
                self.users_collection.update_one(
                    {"username": self.my_username},
                    {"$set": {
                        "last_seen": datetime.now(),
                        "status": "online"
                    }}
                )
                
            except Exception as e:
                print(f"Ошибка в фоновой проверке: {e}")
            
            time.sleep(2)  # Проверяем каждые 2 секунды

# Создаем экземпляр мессенджера
messenger = MongoMessenger()

# API endpoints
@app.route('/receive', methods=['POST'])
def receive_message():
    """Получение сообщения и сохранение в MongoDB"""
    try:
        message = request.json
        message['received_at'] = datetime.now()
        message['read'] = False
        
        # Сохраняем в MongoDB
        messenger.messages_collection.insert_one(message)
        
        print(f"\nНовое сообщение от {message.get('sender', 'Unknown')}:")
        print(f"Текст: {message.get('text', '')}")
        print("-" * 40)
        
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'status': 'online',
        'hostname': socket.gethostname(),
        'peers': list(messenger.peers.keys()),
        'message_count': messenger.messages_collection.count_documents({
            "$or": [
                {"sender": messenger.my_username},
                {"receiver": messenger.my_username}
            ]
        })
    })

@app.route('/api/messages', methods=['GET'])
def get_messages_api():
    """API для получения сообщений"""
    limit = request.args.get('limit', default=50, type=int)
    messages = messenger.get_all_messages(limit)
    return json.loads(json_util.dumps(messages))

@app.route('/api/messages/send', methods=['POST'])
def send_message_api():
    """API для отправки сообщений"""
    data = request.json
    receiver = data.get('receiver')
    text = data.get('text')
    
    if not receiver or not text:
        return jsonify({'error': 'Missing receiver or text'}), 400
    
    success = messenger.send_message_to_db(receiver, text)
    
    if success:
        return jsonify({'status': 'sent'}), 200
    else:
        return jsonify({'error': 'Failed to send message'}), 500

@app.route('/api/users/online', methods=['GET'])
def get_online_users_api():
    """API для получения онлайн пользователей"""
    users = messenger.get_online_users()
    return jsonify(users)

def main():
    # Запускаем сервер
    messenger.start()
    
    print("\n" + "="*60)
    print("MongoDB HTTP Мессенджер")
    print("="*60)
    print(f"Ваше имя: {messenger.my_username}")
    print(f"Ваш адрес: http://{messenger.get_local_ip()}:{messenger.port}")
    print("="*60)
    
    # Основной цикл интерфейса
    while True:
        print("\nКоманды:")
        print("1. Добавить пользователя (вручную)")
        print("2. Отправить сообщение")
        print("3. Показать все сообщения")
        print("4. Показать новые сообщения")
        print("5. Показать онлайн пользователей")
        print("6. Обновить список пользователей из БД")
        print("7. Выход")
        
        choice = input("\nВыберите действие: ")
        
        if choice == '1':
            name = input("Имя пользователя: ")
            ip = input("IP адрес: ")
            port = input("Порт (по умолчанию 5000): ") or "5000"
            url = f"http://{ip}:{port}"
            messenger.add_peer(name, url)
            
        elif choice == '2':
            print("\n1. Отправить конкретному пользователю")
            print("2. Отправить всем онлайн")
            
            send_choice = input("Выберите вариант: ")
            
            if send_choice == '1':
                online_users = messenger.get_online_users()
                if online_users:
                    print("\nОнлайн пользователи:")
                    for i, user in enumerate(online_users, 1):
                        print(f"{i}. {user['username']} ({user['status']})")
                
                receiver = input("\nИмя получателя: ")
                text = input("Сообщение: ")
                messenger.send_message_to_db(receiver, text)
                
            elif send_choice == '2':
                text = input("Сообщение для всех: ")
                online_users = messenger.get_online_users()
                for user in online_users:
                    messenger.send_message_to_db(user['username'], text)
                print(f"Сообщение отправлено {len(online_users)} пользователям")
            
        elif choice == '3':
            messages = messenger.get_all_messages()
            if not messages:
                print("\nСообщений нет")
            else:
                print("\n" + "="*60)
                print(f"Все сообщения ({len(messages)}):")
                print("="*60)
                for msg in messages:
                    sender = msg.get('sender', 'Unknown')
                    receiver = msg.get('receiver', 'Unknown')
                    text = msg.get('text', '')
                    timestamp = msg.get('timestamp', '')
                    
                    if isinstance(timestamp, str):
                        timestamp = timestamp[:19]  # Обрезаем до секунд
                    
                    if receiver == messenger.my_username:
                        print(f"\n📨 От: {sender} → Вам")
                    elif sender == messenger.my_username:
                        print(f"\n📤 Вам → {receiver}")
                    else:
                        print(f"\n📝 {sender} → {receiver}")
                    
                    print(f"   {text}")
                    print(f"   {timestamp}")
                print("="*60)
                
        elif choice == '4':
            messages = messenger.get_unread_messages()
            if messages:
                print(f"\nНепрочитанные сообщения ({len(messages)}):")
                for msg in messages:
                    print(f"\nОт: {msg.get('sender', 'Unknown')}")
                    print(f"Текст: {msg.get('text', '')}")
                    timestamp = msg.get('timestamp', '')
                    if isinstance(timestamp, str):
                        timestamp = timestamp[:19]
                    print(f"Время: {timestamp}")
            else:
                print("\nНовых сообщений нет")
                
        elif choice == '5':
            users = messenger.get_online_users()
            if users:
                print(f"\nОнлайн пользователи ({len(users)}):")
                for user in users:
                    print(f"- {user['username']} ({user['status']})")
            else:
                print("\nДругих пользователей онлайн нет")
                
        elif choice == '6':
            users = messenger.get_online_users()
            print(f"\nНайдено {len(users)} пользователей в БД")
            for user in users:
                url = f"http://{user['ip']}:{user['port']}"
                messenger.add_peer(user['username'], url)
                
        elif choice == '7':
            # Устанавливаем статус оффлайн
            messenger.users_collection.update_one(
                {"username": messenger.my_username},
                {"$set": {"status": "offline"}}
            )
            print("Выход...")
            break

if __name__ == '__main__':
    main()
