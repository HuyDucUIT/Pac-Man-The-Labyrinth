"""
config/settings.py
-------------------
Tập trung toàn bộ hằng số cấu hình và bảng màu dùng chung cho toàn bộ dự án
(kích thước màn hình, kích thước bản đồ, kích thước ô lưới, tốc độ khung hình
và các mã màu RGB). Mọi package khác import từ đây thay vì khai báo lại
"magic number" rải rác trong code.
"""

SCREEN_WIDTH, SCREEN_HEIGHT = 1024, 768
ZOOM = 1.5
GAME_WIDTH = int(SCREEN_WIDTH / ZOOM)
GAME_HEIGHT = int(SCREEN_HEIGHT / ZOOM)

BASE_MAP_W, BASE_MAP_H = 3200, 2400
TILE = 32
FPS = 60
MIN_HALL = 3  # kích thước tối thiểu 1 "chunk" hành lang khi sinh mê cung

# ------------------- Bảng màu (Màu sắc) -------------------
BLACK       = (5, 5, 5)
WHITE       = (240, 240, 240)
DARK_GRAY   = (30, 30, 30)
GRAY        = (120, 120, 120)
RED         = (200, 20, 20)
BOSS_RED    = (150, 15, 15)
YELLOW      = (255, 220, 0)
ORANGE      = (255, 150, 50)
MAGENTA     = (255, 0, 255)
GREEN       = (0, 200, 0)
BLUE        = (0, 150, 255)
BROWN       = (139, 69, 19)
