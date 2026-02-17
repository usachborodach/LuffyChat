from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.core.window import Window
import requests
import threading
import json
from datetime import datetime

class ChatApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.messages = []
        self.api_url = "http://172.29.1.9:5000"  # URL вашего Flask сервера
        self.username = "mobile_user"
        
    def build(self):
        Window.size = (700, 700)  # Размер окна для мобильного
        
        # Основной layout
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Заголовок
        title = Label(
            text='LuffyChat Mobile',
            size_hint=(1, 0.1),
            font_size='24sp',
            bold=True,
            color=(0.2, 0.6, 1, 1)
        )
        
        # Поле для сообщений
        self.chat_scroll = ScrollView(size_hint=(1, 0.7))
        self.chat_layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.chat_layout.bind(minimum_height=self.chat_layout.setter('height'))
        self.chat_scroll.add_widget(self.chat_layout)
        
        # Нижняя панель
        bottom_layout = BoxLayout(size_hint=(1, 0.2), spacing=10)
        
        self.message_input = TextInput(
            hint_text='Введите сообщение...',
            size_hint=(0.7, 1),
            multiline=False
        )
        
        send_button = Button(
            text='Отправить',
            size_hint=(0.3, 1),
            background_color=(0.2, 0.6, 1, 1)
        )
        send_button.bind(on_press=self.send_message)
        
        bottom_layout.add_widget(self.message_input)
        bottom_layout.add_widget(send_button)
        
        # Сборка интерфейса
        main_layout.add_widget(title)
        main_layout.add_widget(self.chat_scroll)
        main_layout.add_widget(bottom_layout)
        
        # Запуск обновления сообщений
        Clock.schedule_interval(self.update_messages, 2)
        
        # Загрузка истории
        self.load_messages()
        
        return main_layout
    
    def load_messages(self):
        """Загрузка истории сообщений"""
        try:
            response = requests.get(f"{self.api_url}/api/messages", timeout=5)
            if response.status_code == 200:
                self.messages = response.json()
                self.update_chat_display()
        except Exception as e:
            self.add_message_to_chat("System", f"Ошибка подключения: {e}")
    
    def send_message(self, instance):
        """Отправка сообщения"""
        text = self.message_input.text.strip()
        if not text:
            return
            
        # Показываем сообщение сразу
        self.add_message_to_chat("Вы", text, is_me=True)
        self.message_input.text = ""
        
        # Отправка на сервер в отдельном потоке
        threading.Thread(target=self._send_to_server, args=(text,)).start()
    
    def _send_to_server(self, text):
        """Отправка сообщения на сервер"""
        try:
            data = {
                "sender": self.username,
                "receiver": "all",
                "text": text,
                "timestamp": datetime.now().isoformat()
            }
            
            response = requests.post(
                f"{self.api_url}/api/messages/send",
                json=data,
                timeout=5
            )
            
            if response.status_code != 200:
                self.add_message_to_chat("System", "Ошибка отправки")
                
        except Exception as e:
            self.add_message_to_chat("System", f"Ошибка: {str(e)}")
    
    def update_messages(self, dt):
        """Периодическое обновление сообщений"""
        threading.Thread(target=self._fetch_new_messages).start()
    
    def _fetch_new_messages(self):
        """Получение новых сообщений"""
        try:
            response = requests.get(f"{self.api_url}/api/messages", timeout=5)
            if response.status_code == 200:
                new_messages = response.json()
                
                # Находим новые сообщения
                if len(new_messages) > len(self.messages):
                    for msg in new_messages[len(self.messages):]:
                        sender = msg.get('sender', 'Unknown')
                        if sender != self.username:  # Не показываем свои сообщения дважды
                            text = msg.get('text', '')
                            Clock.schedule_once(lambda dt, s=sender, t=text: 
                                              self.add_message_to_chat(s, t))
                    
                    self.messages = new_messages
                    
        except Exception:
            pass  # Игнорируем ошибки таймаута
    
    def add_message_to_chat(self, sender, text, is_me=False):
        """Добавление сообщения в чат"""
        def add(dt):
            message_layout = BoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height=50,
                spacing=10
            )
            
            if is_me:
                # Мои сообщения справа
                message_layout.add_widget(Label(size_hint=(0.3, 1)))
                message_box = BoxLayout(
                    orientation='vertical',
                    size_hint=(0.7, 1),
                    padding=5
                )
                message_box.add_widget(Label(
                    text=f"[color=0066cc]{text}[/color]",
                    markup=True,
                    halign='right',
                    text_size=(200, None)
                ))
                message_box.add_widget(Label(
                    text=f"[color=888888][size=10]Вы[/size][/color]",
                    markup=True,
                    halign='right',
                    size_hint=(1, 0.3)
                ))
                message_layout.add_widget(message_box)
            else:
                # Сообщения других слева
                message_box = BoxLayout(
                    orientation='vertical',
                    size_hint=(0.7, 1),
                    padding=5
                )
                message_box.add_widget(Label(
                    text=f"[color=333333]{text}[/color]",
                    markup=True,
                    halign='left',
                    text_size=(200, None)
                ))
                message_box.add_widget(Label(
                    text=f"[color=888888][size=10]{sender}[/size][/color]",
                    markup=True,
                    halign='left',
                    size_hint=(1, 0.3)
                ))
                message_layout.add_widget(message_box)
                message_layout.add_widget(Label(size_hint=(0.3, 1)))
            
            self.chat_layout.add_widget(message_layout)
            # Прокрутка вниз
            Clock.schedule_once(self.scroll_to_bottom)
        
        Clock.schedule_once(add)
    
    def scroll_to_bottom(self, dt):
        """Прокрутка к последнему сообщению"""
        self.chat_scroll.scroll_y = 0
    
    def update_chat_display(self):
        """Обновление отображения всех сообщений"""
        self.chat_layout.clear_widgets()
        for msg in self.messages[-20:]:  # Последние 20 сообщений
            sender = msg.get('sender', 'Unknown')
            text = msg.get('text', '')
            is_me = (sender == self.username)
            self.add_message_to_chat(sender, text, is_me)

if __name__ == '__main__':
    ChatApp().run()
