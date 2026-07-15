"""
core/asset_loader.py
---------------------
Nạp tài nguyên (sprite, font, âm thanh) theo chiến lược "suy biến an toàn"
(graceful degradation): mỗi hàm đều bọc trong try/except, nếu file asset
bị thiếu hoặc lỗi sẽ tự sinh ra một đối tượng thay thế hợp lý (hình chữ nhật
màu, font hệ thống, hoặc None) thay vì làm crash toàn bộ game. Nhờ vậy,
thành viên nhóm thiếu file asset vẫn chạy thử và test logic game bình thường.
"""

import pygame

from config.settings import TILE, MAGENTA


def load_sprite_scaled(name, scale=TILE):
    """Nạp và scale sprite tile/tường theo kích thước ô lưới; nếu thiếu file, tự vẽ khối màu placeholder tương ứng loại tường."""
    try:
        img = pygame.image.load(name).convert_alpha()
        return pygame.transform.scale(img, (scale, scale))
    except:
        s = pygame.Surface((scale, scale))
        if "tile" in name: s.fill((30, 30, 30))
        elif "wall1" in name: s.fill((60, 60, 60))
        elif "wall2" in name: s.fill((70, 70, 70))
        elif "wall3" in name: s.fill((50, 50, 50))
        elif "wallwindow" in name:
            s.fill((60, 60, 60))
            pygame.draw.rect(s, (20,20,40), (scale//4, scale//4, scale//2, scale//2))
        elif "bush" in name: s.fill((20, 80, 20))
        return s


def load_font(name, size):
    """Thử nạp font pixel tuỳ chỉnh theo nhiều biến thể tên file; nếu không tìm thấy, dùng font hệ thống Courier New làm phương án dự phòng."""
    for f in [name, name.lower(), "assets/04B_03__.TTF", "assets/04b_03.ttf"]:
        try: return pygame.font.Font(f, size)
        except: pass
    return pygame.font.SysFont("Courier New", size, bold=True)


def load_img(name, scale):
    """Nạp và scale một hình ảnh theo kích thước chỉ định; nếu lỗi, trả về mặt phẳng màu magenta để dễ nhận biết ảnh bị thiếu."""
    try: return pygame.transform.scale(pygame.image.load(name).convert_alpha(), scale)
    except:
        s = pygame.Surface(scale, pygame.SRCALPHA); s.fill(MAGENTA); return s


def load_sound(name):
    """Nạp một file âm thanh; trả về None nếu không tải được để các lệnh gọi .play() phía sau có thể kiểm tra an toàn."""
    try: return pygame.mixer.Sound(name)
    except: return None
