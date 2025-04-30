import sys
import os
import time
import keyboard
import pyautogui
import win32api
import win32con
import win32gui
import win32process
import threading
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QObject, pyqtSignal, Qt

# Константы для русской и английской раскладок
RUSSIAN_LAYOUT_ID = 0x0419
ENGLISH_LAYOUT_ID = 0x0409

# Словари для преобразования символов между раскладками
ru_to_en = {
    'й': 'q', 'ц': 'w', 'у': 'e', 'к': 'r', 'е': 't', 'н': 'y', 'г': 'u', 'ш': 'i', 'щ': 'o', 'з': 'p',
    'х': '[', 'ъ': ']', 'ф': 'a', 'ы': 's', 'в': 'd', 'а': 'f', 'п': 'g', 'р': 'h', 'о': 'j', 'л': 'k',
    'д': 'l', 'ж': ';', 'э': '\'', 'я': 'z', 'ч': 'x', 'с': 'c', 'м': 'v', 'и': 'b', 'т': 'n', 'ь': 'm',
    'б': ',', 'ю': '.', '.': '/', 'Й': 'Q', 'Ц': 'W', 'У': 'E', 'К': 'R', 'Е': 'T', 'Н': 'Y', 'Г': 'U',
    'Ш': 'I', 'Щ': 'O', 'З': 'P', 'Х': '{', 'Ъ': '}', 'Ф': 'A', 'Ы': 'S', 'В': 'D', 'А': 'F', 'П': 'G',
    'Р': 'H', 'О': 'J', 'Л': 'K', 'Д': 'L', 'Ж': ':', 'Э': '"', 'Я': 'Z', 'Ч': 'X', 'С': 'C', 'М': 'V',
    'И': 'B', 'Т': 'N', 'Ь': 'M', 'Б': '<', 'Ю': '>', ',': '<', '?': '/', '!': '!'
}

en_to_ru = {value: key for key, value in ru_to_en.items()}

# Классы для определения языка ввода
class LanguageDetector:
    def __init__(self):
        self.buffer = []
        self.max_buffer_size = 15
        
    def add_char(self, char):
        self.buffer.append(char)
        if len(self.buffer) > self.max_buffer_size:
            self.buffer.pop(0)
            
    def clear_buffer(self):
        self.buffer = []
        
    def get_buffer_text(self):
        return ''.join(self.buffer)
    
    def is_russian_text(self, text):
        # Проверяем, содержит ли текст русские символы
        russian_chars = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'
        for char in text:
            if char in russian_chars:
                return True
        return False
    
    def is_english_text(self, text):
        # Проверяем, содержит ли текст английские символы
        english_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        for char in text:
            if char in english_chars:
                return True
        return False
    
    def detect_wrong_layout(self):
        text = self.get_buffer_text()
        if len(text) < 3:  # Нужно хотя бы несколько символов для определения
            return None
            
        # Получаем текущую раскладку клавиатуры
        current_layout = get_keyboard_layout()
        
        if current_layout == RUSSIAN_LAYOUT_ID and self.is_english_text(text):
            return 'ru'  # Печатаем на английском с русской раскладкой
        elif current_layout == ENGLISH_LAYOUT_ID and self.is_russian_text(text):
            return 'en'  # Печатаем на русском с английской раскладкой
            
        return None

# Функции для работы с раскладкой клавиатуры Windows
def get_foreground_window_process_id():
    hwnd = win32gui.GetForegroundWindow()
    _, process_id = win32process.GetWindowThreadProcessId(hwnd)
    return process_id, hwnd

def get_keyboard_layout():
    hwnd = win32gui.GetForegroundWindow()
    thread_id = win32process.GetWindowThreadProcessId(hwnd)[0]
    layout_id = win32api.GetKeyboardLayout(thread_id) & 0xFFFF
    return layout_id

def set_keyboard_layout(layout_id):
    # Переключаем раскладку используя Alt+Shift
    if layout_id == RUSSIAN_LAYOUT_ID:
        if get_keyboard_layout() != RUSSIAN_LAYOUT_ID:
            pyautogui.hotkey('alt', 'shift')
    elif layout_id == ENGLISH_LAYOUT_ID:
        if get_keyboard_layout() != ENGLISH_LAYOUT_ID:
            pyautogui.hotkey('alt', 'shift')

def switch_text(text, source_layout):
    """Преобразует текст из одной раскладки в другую"""
    result = []
    if source_layout == 'ru':  # Преобразуем из русской раскладки в английскую
        for char in text:
            result.append(ru_to_en.get(char, char))
    else:  # Преобразуем из английской раскладки в русскую
        for char in text:
            result.append(en_to_ru.get(char, char))
    return ''.join(result)

class KeyLogger:
    def __init__(self):
        self.detector = LanguageDetector()
        self.is_running = False
        self.thread = None
        self.enabled = True
        
    def key_callback(self, event):
        if not self.enabled:
            return
            
        if event.event_type == keyboard.KEY_DOWN:
            # Проверяем, не нажата ли комбинация клавиш
            if keyboard.is_pressed('ctrl') or keyboard.is_pressed('alt'):
                return
                
            # Получаем нажатый символ
            char = event.name
            
            # Игнорируем специальные клавиши
            if len(char) == 1:
                self.detector.add_char(char)
                
                # Анализируем буфер на предмет неправильной раскладки
                wrong_layout = self.detector.detect_wrong_layout()
                if wrong_layout:
                    # Получаем текст буфера
                    buffer_text = self.detector.get_buffer_text()
                    # Преобразуем текст
                    corrected_text = switch_text(buffer_text, wrong_layout)
                    
                    # Удаляем неправильный текст и вставляем правильный
                    for _ in range(len(buffer_text)):
                        keyboard.press_and_release('backspace')
                        
                    # Устанавливаем правильную раскладку
                    if wrong_layout == 'ru':
                        set_keyboard_layout(ENGLISH_LAYOUT_ID)
                    else:
                        set_keyboard_layout(RUSSIAN_LAYOUT_ID)
                        
                    # Вставляем правильный текст
                    keyboard.write(corrected_text)
                    
                    # Очищаем буфер
                    self.detector.clear_buffer()
            else:
                # Если нажата специальная клавиша (Enter, Space и т.д.), очищаем буфер
                if char in ['space', 'enter']:
                    self.detector.clear_buffer()
        
    def start(self):
        if not self.is_running:
            self.is_running = True
            keyboard.hook(self.key_callback)
            
    def stop(self):
        if self.is_running:
            keyboard.unhook_all()
            self.is_running = False
            
    def toggle_enabled(self):
        self.enabled = not self.enabled
        return self.enabled

# Класс для отображения иконки в системном трее
class SystemTrayApp(QObject):
    def __init__(self):
        super().__init__()
        self.keylogger = KeyLogger()
        
        # Создаем приложение Qt
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        # Создаем иконку в трее
        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setToolTip('PuntoSwitcherClone')
        self.tray_icon.setIcon(self.get_default_icon())
        
        # Создаем меню для иконки
        self.menu = QMenu()
        
        # Добавляем пункты меню
        self.enabled_action = QAction('Отключить', self)
        self.enabled_action.triggered.connect(self.toggle_enabled)
        self.menu.addAction(self.enabled_action)
        
        self.exit_action = QAction('Выход', self)
        self.exit_action.triggered.connect(self.exit_app)
        self.menu.addAction(self.exit_action)
        
        # Устанавливаем меню
        self.tray_icon.setContextMenu(self.menu)
        
        # Показываем иконку
        self.tray_icon.show()
        
        # Запускаем отслеживание клавиатуры
        self.keylogger.start()
        
    def get_default_icon(self):
        # Путь к файлу иконки в зависимости от того, используем ли мы PyInstaller
        if hasattr(sys, '_MEIPASS'):
            # Путь при запуске из exe
            icon_path = os.path.join(sys._MEIPASS, "app_icon.ico")
        else:
            # Путь при запуске из .py файла
            icon_path = "app_icon.ico"
            
        # Проверяем существование файла иконки
        if os.path.exists(icon_path):
            return QIcon(icon_path)
        else:
            # Если иконка не найдена, используем системную иконку
            icon = QIcon.fromTheme("input-keyboard")
            if icon.isNull():
                return QIcon()
            return icon
    
    def toggle_enabled(self):
        enabled = self.keylogger.toggle_enabled()
        if enabled:
            self.enabled_action.setText('Отключить')
        else:
            self.enabled_action.setText('Включить')
    
    def exit_app(self):
        self.keylogger.stop()
        self.tray_icon.hide()
        QApplication.quit()
        
    def run(self):
        return self.app.exec_()

if __name__ == "__main__":
    app = SystemTrayApp()
    sys.exit(app.run())
