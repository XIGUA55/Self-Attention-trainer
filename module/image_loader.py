import os
import random
from PIL import Image, ImageEnhance
from rich.text import Text

# 你的图片列表
WAIFU_META = {
    "madoka.jpg": ("Puella Magi Madoka Magica", "magenta"),
    "bloom.jpg":  ("Bloom Into You", "orange1"),
    "adachi.jpg": ("Adachi and Shimamura", "cyan"),
    "cdr.jpg":    ("Creation by", "blue"),
}

def get_image_path(filename):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(current_dir) 
    return os.path.join(base_dir, "data", "images", filename)

def image_to_ascii(image_path, width=60):
    if not os.path.exists(image_path):
        return None, None

    try:
        img = Image.open(image_path).convert("RGB")
    except:
        return None, None

    # ================= 关键修复 =================
    # 因为我们在下面使用了 "  " (两个空格) 来表示一个像素
    # 所以实际渲染宽度是像素宽度的 2 倍。
    # 为了让输出符合传入的 width (终端列数)，我们需要先把像素宽除以 2。
    render_width = width // 2  
    # ===========================================

    # 2. 调整大小
    w, h = img.size
    aspect_ratio = h / w
    
    # 计算高度：
    # 因为我们用了双空格模拟正方形像素，所以高度不需要像普通 ASCII 那样乘以 0.55
    # 直接按比例缩放即可
    new_height = int(aspect_ratio * render_width )
    
    # 使用 render_width 而不是传入的 width
    img = img.resize((render_width, new_height), Image.Resampling.LANCZOS)
    
    # 3. 色彩增强 (保持不变)
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(1.8) 
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.2)
    
    pixels = img.load()

    # 4. 构建字符画
    ascii_str = Text()
    
    for y in range(new_height):
        # 注意这里遍历的是 render_width
        for x in range(render_width):
            r, g, b = pixels[x, y]
            ascii_str.append("  ", style=f"on rgb({r},{g},{b})")
                
        ascii_str.append("\n")
        
    return ascii_str, img.size

def get_random_waifu_art(width=50):
    available_files = []
    try:
        data_dir = os.path.dirname(get_image_path("placeholder"))
        if os.path.exists(data_dir):
            for f in os.listdir(data_dir):
                if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                    available_files.append(f)
    except: pass

    if not available_files:
        return None, "No Images Found", "red"

    selected_file = random.choice(available_files)
    full_path = os.path.join(data_dir, selected_file)
    meta = WAIFU_META.get(selected_file, ("Unknown Character", "white"))
    
    art, _ = image_to_ascii(full_path, width=width)
    return art, meta[0], meta[1]