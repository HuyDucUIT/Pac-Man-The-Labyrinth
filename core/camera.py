"""
core/camera.py
---------------
Camera theo dõi và cuộn theo người chơi trong bản đồ mê cung. Áp dụng phép
nội suy tuyến tính (lerp) để camera đuổi theo mục tiêu mượt mà thay vì bám
cứng theo từng khung hình, đồng thời giới hạn (clamp) camera không vượt ra
ngoài biên bản đồ.
"""

import pygame

from config.settings import GAME_WIDTH, GAME_HEIGHT


class Camera:
    """Camera cuộn theo Player, dùng lerp để di chuyển mượt và tự giới hạn trong biên bản đồ."""
    def __init__(self, map_width, map_height):
        """Khởi tạo camera với kích thước bản đồ và vị trí ban đầu (0,0)."""
        self.map_width  = map_width
        self.map_height = map_height
        self.cam_x = 0.0
        self.cam_y = 0.0
        self.camera = pygame.Rect(0, 0, map_width, map_height)

    def snap(self, target):
        """Đặt camera ngay lập tức về giữa mục tiêu (dùng khi vào màn mới, tránh giật hình do lerp)."""
        self.cam_x = -target.rect.centerx + GAME_WIDTH  // 2
        self.cam_y = -target.rect.centery + GAME_HEIGHT // 2
        self.update_rect()

    def apply(self, entity):
        """Chuyển toạ độ rect của một entity từ hệ toạ độ bản đồ sang hệ toạ độ màn hình theo camera hiện tại."""
        return entity.rect.move(self.camera.topleft)

    def apply_rect(self, r):
        """Chuyển một pygame.Rect bất kỳ từ hệ toạ độ bản đồ sang hệ toạ độ màn hình."""
        return r.move(self.camera.topleft)

    def update(self, target):
        """Cập nhật vị trí camera mỗi khung hình bằng nội suy tuyến tính (lerp 6%) hướng về tâm mục tiêu."""
        tx = -target.rect.centerx + GAME_WIDTH  // 2
        ty = -target.rect.centery + GAME_HEIGHT // 2
        self.cam_x += (tx - self.cam_x) * 0.06
        self.cam_y += (ty - self.cam_y) * 0.06
        self.update_rect()

    def update_rect(self):
        """Tính lại pygame.Rect của camera, giới hạn (clamp) không cho camera lộ ra ngoài biên bản đồ."""
        x = min(0, max(-(self.map_width  - GAME_WIDTH),  self.cam_x))
        y = min(0, max(-(self.map_height - GAME_HEIGHT), self.cam_y))
        self.camera = pygame.Rect(int(x), int(y), self.map_width, self.map_height)
