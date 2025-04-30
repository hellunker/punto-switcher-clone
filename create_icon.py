import os
from PIL import Image, ImageDraw, ImageFont

def create_simple_icon(output_file="app_icon.ico", size=256):
    """
    Создает простую иконку для PuntoSwitcherClone.
    
    Args:
        output_file (str): Имя выходного файла .ico
        size (int): Размер иконки в пикселях
    """
    # Создаем новое изображение с прозрачным фоном
    icon = Image.new('RGBA', (size, size), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(icon)
    
    # Рисуем круг с градиентом
    for i in range(size//2):
        color = (41, 128, 185, 255 - i*2)  # Синий цвет с изменением прозрачности
        draw.ellipse((i, i, size-i, size-i), outline=color)
    
    # Рисуем фон для текста
    draw.ellipse((size//4, size//4, 3*size//4, 3*size//4), fill=(52, 152, 219, 200))
    
    # Пытаемся найти шрифт (или используем встроенный)
    try:
        font = ImageFont.truetype("arial.ttf", size=size//4)
    except IOError:
        font = ImageFont.load_default()
    
    # Добавляем текст
    draw.text((size//3, size//3), "PS", fill=(255, 255, 255), font=font)
    
    # Сохраняем как .ico
    if not output_file.lower().endswith('.ico'):
        output_file += '.ico'
    
    icon.save(output_file, format='ICO')
    print(f"Иконка создана: {os.path.abspath(output_file)}")
    
if __name__ == "__main__":
    create_simple_icon()
