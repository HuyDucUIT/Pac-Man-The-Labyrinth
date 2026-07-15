"""
objects/items.py
-----------------
Các vật phẩm mà người chơi có thể nhặt/tương tác trực tiếp trong mê cung:
Dot (hạt tiền), Note (ghi chú), Candle (nến trang trí), UnpickableCandle
(nến cố định không nhặt được, chỉ chiếu sáng), và Artifact (Artifact -
vật phẩm đặc biệt của màn Boss). Tất cả (trừ UnpickableCandle) đều kế thừa
Interactable và tự quyết định hành vi interact() riêng — minh hoạ Đa hình.
"""

import math
import random

import pygame

from core.game_object import Interactable, GameObject
from config.settings import TILE, YELLOW, WHITE, ORANGE, MAGENTA


class Dot(Interactable):
    """Hạt tiền (dot) — nhặt được cộng xu và phát ra tiếng động nhỏ để Ghost có thể nghe thấy."""
    def __init__(self, x, y):
        """Tạo hạt tiền tại (x, y) với pha dao động ngẫu nhiên cho hiệu ứng nhấp nháy."""
        super().__init__(x+12, y+12, 8, 8, YELLOW)
        self._pulse = random.uniform(0, math.pi*2)

    def draw(self, surface, camera):
        """Vẽ hạt tiền với quầng sáng nhấp nháy (glow) nếu vẫn còn active."""
        if not self.active: return
        self._pulse += 0.08
        r = camera.apply(self)
        glow = pygame.Surface((24,24), pygame.SRCALPHA)
        alpha = int(60 + 40 * math.sin(self._pulse))
        pygame.draw.circle(glow, (*YELLOW, alpha), (12,12), 10)
        surface.blit(glow, (r.centerx-12, r.centery-12))
        pygame.draw.rect(surface, YELLOW, r)

    def interact(self, player, gs):
        """Cộng 10 xu cho người chơi, tắt vật phẩm và phát tiếng động nhỏ (không lớn) để lan tới Ghost."""
        if self.active:
            player.stats.coins += 10
            self.active = False
            gs.make_noise(self.rect.centerx, self.rect.centery,
                          radius=player.stats.noise_radius*TILE, is_loud=False)

class Note(Interactable):
    """Ghi chú nhặt được — mở khoá cờ has_note trên Player (gợi ý cốt truyện)."""
    def __init__(self, x, y):
        """Tạo ghi chú tại (x, y)."""
        super().__init__(x+8, y+8, 16, 16, WHITE)

    def draw(self, surface, camera):
        """Vẽ ghi chú dạng tờ giấy có vài dòng kẻ, nếu vẫn còn active."""
        if not self.active: return
        r = camera.apply(self)
        pygame.draw.rect(surface, (230,225,210), r)
        pygame.draw.rect(surface, (180,170,150), r, 1)
        for ly in [r.y+4, r.y+8, r.y+12]:
            pygame.draw.line(surface, (80,70,60), (r.x+3, ly), (r.x+13, ly), 1)

    def interact(self, player, gs):
        """Đặt cờ player.has_note = True và tắt vật phẩm sau khi đọc."""
        if self.active:
            player.has_note = True
            self.active = False

class Candle(Interactable):
    """Nến trang trí nhặt/đứng cạnh được — không có hành vi interact() cụ thể, vai trò chính là chiếu sáng thụ động."""
    def __init__(self, x, y):
        """Tạo nến tại (x, y) với pha dao động ngẫu nhiên cho hiệu ứng lửa lung linh."""
        super().__init__(x+8, y+8, 16, 16, ORANGE)
        self._flicker = random.uniform(0, math.pi*2)

    def draw(self, surface, camera):
        """Vẽ thân nến và ngọn lửa dao động (flicker) nếu vẫn còn active."""
        if not self.active: return
        self._flicker += 0.12
        r = camera.apply(self)
        pygame.draw.rect(surface, (220,200,170), (r.x+4, r.y+4, 8, 10))
        pygame.draw.rect(surface, (180,160,130), (r.x+4, r.y+4, 8, 10), 1)
        pygame.draw.line(surface, (80,60,40), (r.centerx, r.y+4), (r.centerx, r.y+2), 1)
        flicker_x = int(math.sin(self._flicker)*2)
        fx = r.centerx + flicker_x
        fy = r.y - 2
        pygame.draw.ellipse(surface, (255,200,50), (fx-3, fy-6, 6, 8))
        pygame.draw.ellipse(surface, (255,240,120),(fx-2, fy-4, 4, 5))

    def interact(self, player, gs):
        """Không xử lý gì (pass) — vai trò của nến chỉ là chiếu sáng thụ động khi đứng gần."""
        pass

class UnpickableCandle(GameObject):
    """Nến cố định không thể tương tác (không kế thừa Interactable) — chỉ tồn tại để chiếu sáng một khu vực an toàn."""
    def __init__(self, x, y):
        """Tạo nến cố định tại (x, y) với pha dao động ngẫu nhiên cho hiệu ứng lửa."""
        super().__init__(x+8, y+8, 16, 16, ORANGE)
        self._flicker = random.uniform(0, math.pi*2)

    def draw(self, surface, camera):
        """Vẽ thân nến và ngọn lửa dao động; luôn hiển thị (không có cờ active để tắt)."""
        self._flicker += 0.10
        r = camera.apply(self)
        pygame.draw.rect(surface, (220,200,170), (r.x+4, r.y+4, 8, 10))
        pygame.draw.rect(surface, (180,160,130), (r.x+4, r.y+4, 8, 10), 1)
        pygame.draw.line(surface, (80,60,40), (r.centerx, r.y+4),(r.centerx, r.y+2), 1)
        flicker_x = int(math.sin(self._flicker)*2)
        fx = r.centerx + flicker_x; fy = r.y - 2
        pygame.draw.ellipse(surface, (255,200,50), (fx-3, fy-6, 6, 8))
        pygame.draw.ellipse(surface, (255,240,120),(fx-2, fy-4, 4, 5))

class Artifact(Interactable):
    """Vật phẩm đặc biệt (Artifact) của màn Boss — mang về bàn thờ trung tâm để 'tiến hoá' Ghost."""
    def __init__(self, x, y):
        """Tạo vật phẩm đặc biệt tại (x, y) với pha bồng bềnh (bob) ngẫu nhiên."""
        super().__init__(x+4, y+4, 24, 24, MAGENTA)
        self._bob = random.uniform(0, math.pi*2)

    def draw(self, surface, camera):
        """Vẽ vật phẩm dạng viên pha lê phát sáng, bồng bềnh lên xuống, nếu vẫn còn active."""
        if not self.active: return
        self._bob += 0.06
        r   = camera.apply(self)
        bob = int(math.sin(self._bob)*2)
        glow = pygame.Surface((48,48), pygame.SRCALPHA)
        pygame.draw.circle(glow, (180,0,180,50), (24,24), 20)
        surface.blit(glow, (r.centerx-24, r.centery-24+bob))
        cx, cy = r.centerx, r.centery+bob
        pts = [(cx, cy-10),(cx+8, cy),(cx, cy+10),(cx-8, cy)]
        pygame.draw.polygon(surface, (200,0,200), pts)
        pygame.draw.polygon(surface, (255,80,255), pts, 1)

    def interact(self, player, gs):
        """Nếu người chơi chưa mang vật phẩm nào khác, đặt cờ carrying_item=True và tắt vật phẩm."""
        if self.active and not gs.carrying_item:
            gs.carrying_item = True
            self.active = False
