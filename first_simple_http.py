import json
import threading
from datetime import datetime
from flask import Flask, request, jsonify
import requests
import socket

app = Flask(__name__)

class SimpleMessenger:
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.messages = []
        self.peers = {}  # Список известных пиров: {"имя": "http://ip:port"}
        
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
    
    def run_server(self):
        """Запуск Flask сервера"""
        app.run(host=self.host, port=self.port, debug=False)
    
    def add_peer(self, name, url):
        """Добавление другого пользователя"""
        self.peers[name] = url
        print(f"Добавлен пир: {name} -> {url}")
    
    def send_message(self, peer_name, text):
        """Отправка сообщения другому пользователю"""
        if peer_name not in self.peers:
            print(f"Ошибка: пир '{peer_name}' не найден")
            return False
        
        try:
            message = {
                'sender': socket.gethostname(),
                'text': text,
                'timestamp': datetime.now().isoformat()
            }
            
            response = requests.post(
                f"{self.peers[peer_name]}/receive",
                json=message,
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"Сообщение отправлено {peer_name}")
                return True
            else:
                print(f"Ошибка отправки: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Ошибка при отправке: {e}")
            return False
    
    def get_messages(self):
        """Получение всех сообщений"""
        return self.messages

# Создаем экземпляр мессенджера
messenger = SimpleMessenger()

# API endpoint для приема сообщений
@app.route('/receive', methods=['POST'])
def receive_message():
    """Получение сообщения от другого пользователя"""
    try:
        message = request.json
        message['received_at'] = datetime.now().isoformat()
        messenger.messages.append(message)
        
        print(f"\nНовое сообщение от {message['sender']}:")
        print(f"Текст: {message['text']}")
        print(f"Время: {message['timestamp']}")
        print("-" * 40)
        
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# API endpoint для проверки статуса
@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'status': 'online',
        'hostname': socket.gethostname(),
        'peers': list(messenger.peers.keys()),
        'message_count': len(messenger.messages)
    })

def main():
    # Запускаем сервер
    messenger.start()
    
    print("\n" + "="*50)
    print("Простой HTTP Мессенджер")
    print("="*50)
    print(f"Ваш адрес: http://{messenger.get_local_ip()}:{messenger.port}")
    print(f"Имя хоста: {socket.gethostname()}")
    print("="*50)
    
    # Основной цикл интерфейса
    while True:
        print("\nКоманды:")
        print("1. Добавить пользователя")
        print("2. Отправить сообщение")
        print("3. Показать все сообщения")
        print("4. Показать список пользователей")
        print("5. Выход")
        
        choice = input("\nВыберите действие: ")
        
        if choice == '1':
            name = input("Имя пользователя: ")
            ip = input("IP адрес: ")
            port = input("Порт (по умолчанию 5000): ") or "5000"
            url = f"http://{ip}:{port}"
            messenger.add_peer(name, url)
            
        elif choice == '2':
            if not messenger.peers:
                print("Сначала добавьте пользователя!")
                continue
                
            print("\nДоступные пользователи:")
            for i, name in enumerate(messenger.peers.keys(), 1):
                print(f"{i}. {name}")
            
            peer_choice = input("Выберите пользователя (номер или имя): ")
            
            # Пробуем по номеру
            try:
                index = int(peer_choice) - 1
                peer_name = list(messenger.peers.keys())[index]
            except:
                # Или по имени
                peer_name = peer_choice
            
            if peer_name not in messenger.peers:
                print("Пользователь не найден!")
                continue
                
            text = input("Сообщение: ")
            messenger.send_message(peer_name, text)
            
        elif choice == '3':
            messages = messenger.get_messages()
            if not messages:
                print("\nСообщений нет")
            else:
                print("\n" + "="*50)
                print("Все сообщения:")
                print("="*50)
                for msg in messages:
                    print(f"\nОт: {msg.get('sender', 'Неизвестно')}")
                    print(f"Текст: {msg.get('text', '')}")
                    print(f"Отправлено: {msg.get('timestamp', '')}")
                    if 'received_at' in msg:
                        print(f"Получено: {msg.get('received_at', '')}")
                print("="*50)
                
        elif choice == '4':
            print("\nСписок пользователей:")
            for name, url in messenger.peers.items():
                print(f"- {name}: {url}")
                
        elif choice == '5':
            print("Выход...")
            break

if __name__ == '__main__':
    main()
