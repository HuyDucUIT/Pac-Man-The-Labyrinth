"""
core/game_object.py
--------------------
Ba lớp nền tảng (hạ tầng OOP) mà toàn bộ hệ thống được xây trên đó:

- GameObject (abstract): gốc của mọi thứ xuất hiện trên màn hình, buộc lớp
  con phải hiện thực draw().
- Interactable (abstract): kế thừa GameObject, dành cho vật thể người chơi
  có thể tương tác (bấm phím E), buộc lớp con hiện thực interact().
- Entity: kế thừa GameObject, dành cho thực thể "sống" có thể di chuyển và
  va chạm với tường (Player, Ghost).
"""

import pygame
from abc import ABC, abstractmethod


class GameObject(ABC):
    """Lớp trừu tượng gốc: mọi đối tượng hiển thị đều có rect, màu và cờ active."""

    def __init__(self, x, y, w, h, color):
        """Khởi tạo vùng hình chữ nhật (rect), màu sắc và trạng thái hoạt động của đối tượng."""
        self.rect   = pygame.Rect(x, y, w, h)
        self.color  = color
        self.active = True

    @abstractmethod
    def draw(self, surface, camera):
        """Vẽ đối tượng lên surface theo góc nhìn camera. Lớp con bắt buộc phải hiện thực."""
        pass


class Interactable(GameObject):
    """Lớp trừu tượng cho vật thể mà người chơi có thể tương tác (bấm phím E)."""

    @abstractmethod
    def interact(self, player, game_state):
        """Xử lý hành vi khi người chơi tương tác với vật thể này. Lớp con bắt buộc phải hiện thực."""
        pass


class Entity(GameObject):
    """Đối tượng có thể di chuyển và va chạm với tường (Player, Ghost kế thừa từ đây)."""

    def __init__(self, x, y, w, h, color, speed=0.0):
        """Khởi tạo entity với toạ độ thực (float) riêng để di chuyển mượt hơn số nguyên của rect."""
        super().__init__(x, y, w, h, color)
        self.x, self.y = float(x), float(y)
        self.speed = self.current_speed = speed

    def move_and_collide(self, dx, dy, walls, ignore_walls=False):
        """
        Di chuyển entity theo (dx, dy) và xử lý va chạm trục X/Y tách biệt với
        danh sách tường `walls`. Nếu ignore_walls=True (dùng khi Boss truy đuổi),
        entity có thể xuyên tường. Trả về True nếu có va chạm xảy ra.
        """
        collided = False
        self.x += dx; self.rect.x = int(self.x)
        if not ignore_walls:
            for w in walls:
                if self.rect.colliderect(w):
                    collided = True
                    if dx > 0: self.rect.right  = w.left
                    if dx < 0: self.rect.left   = w.right
                    self.x = float(self.rect.x); break
        self.y += dy; self.rect.y = int(self.y)
        if not ignore_walls:
            for w in walls:
                if self.rect.colliderect(w):
                    collided = True
                    if dy > 0: self.rect.bottom = w.top
                    if dy < 0: self.rect.top    = w.bottom
                    self.y = float(self.rect.y); break
        return collided
