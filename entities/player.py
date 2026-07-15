"""
entities/player.py
--------------------
Nhân vật người chơi: xử lý di chuyển theo phím WASD/mũi tên, hoạt ảnh
miệng (mouth chomp) và trạng thái ẩn/lộ (is_hidden) trong bóng tối. Kế thừa
Entity để tái sử dụng move_and_collide(); tốc độ và tầm nhìn không tự lưu
trên Player mà lấy từ đối tượng PlayerStats (composition).
"""

import math

import pygame

from core.game_object import Entity
from config.settings import TILE, YELLOW


class Player(Entity):
    """Nhân vật người chơi: di chuyển, hoạt ảnh miệng, và trạng thái ẩn/lộ trước Ghost."""
    def __init__(self, x, y, stats):
        """Khởi tạo Player tại toạ độ (x, y) với các chỉ số lấy từ đối tượng PlayerStats, cùng các cờ trạng thái (has_candle, has_note, is_hidden) và biến hoạt ảnh miệng."""
        super().__init__(x, y, TILE-4, TILE-4, YELLOW, stats.speed)
        self.stats        = stats
        self.has_candle   = False
        self.has_note     = False
        self.is_hidden    = True
        self.facing_angle = 0
        self.mouth_angle  = 0
        self.mouth_speed  = 4
        self.mouth_dir    = 1
        self.step_timer   = 0

    def move(self, keys, walls, gs):
        """Đọc phím WASD/mũi tên để tính hướng di chuyển, cập nhật góc mặt (facing_angle) và hoạt ảnh miệng, phát âm thanh bước chân theo nhịp, rồi gọi move_and_collide() để di chuyển và né tường."""
        dx = dy = 0
        self.speed = self.stats.speed
        if keys[pygame.K_w] or keys[pygame.K_UP]:   dy -= self.speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  dy += self.speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  dx -= self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += self.speed

        if dx or dy:
            self.facing_angle = math.degrees(math.atan2(-dy, dx)) % 360
            self.mouth_angle += self.mouth_speed * self.mouth_dir
            if self.mouth_angle >= 45: self.mouth_angle = 45; self.mouth_dir = -1
            elif self.mouth_angle <= 0: self.mouth_angle = 0;  self.mouth_dir = 1
            self.step_timer -= 1
            if self.step_timer <= 0:
                if gs.sfx_step: gs.sfx_step.play()
                self.step_timer = 19
        else:
            self.mouth_angle = 0

        self.move_and_collide(dx, dy, walls)

    def get_candle_radius(self):
        """Tính bán kính vùng sáng do nến toả ra (theo tile), dựa trên chỉ số vision_radius trong PlayerStats."""
        return int(self.stats.vision_radius * TILE)

    def draw(self, surface, camera):
        """Vẽ Player dưới dạng hình tròn kiểu Pac-Man với miệng khép/mở theo hoạt ảnh; chuyển màu xám khi đang ẩn trong bóng tối (is_hidden)."""
        r      = camera.apply(self)
        center = r.center
        radius = self.rect.width // 2
        col = self.color if not self.is_hidden else (160, 160, 160)

        shadow = pygame.Surface((radius*2+4, radius*2+4), pygame.SRCALPHA)
        pygame.draw.circle(shadow, (0,0,0,80), (radius+2, radius+4), radius)
        surface.blit(shadow, (center[0]-radius-2, center[1]-radius-2))

        if self.mouth_angle > 0:
            pts  = [center]
            sa   = self.facing_angle + self.mouth_angle
            ea   = self.facing_angle + 360 - self.mouth_angle
            for i in range(31):
                ang = math.radians(sa + i*(ea-sa)/30)
                pts.append((center[0]+radius*math.cos(ang),
                             center[1]-radius*math.sin(ang)))
            pygame.draw.polygon(surface, col, pts)
            pygame.draw.polygon(surface, tuple(min(255,c+60) for c in col), pts, 1)
        else:
            pygame.draw.circle(surface, col, center, radius)
            pygame.draw.circle(surface, tuple(min(255,c+60) for c in col), center, radius, 1)
