"""
objects/doors.py
------------------
Bàn thờ (Altar) và hai loại cửa: GreenDoor (cửa chính khoá theo tiến độ màn
chơi, mở khi đủ điều kiện) và WoodenDoor (cửa phụ luôn mở, dẫn tới Cửa hàng
nâng cấp). Altar không tương tác được (chỉ để trang trí/định vị), còn hai
loại cửa kế thừa Interactable.
"""

import pygame

from core.game_object import GameObject, Interactable
from core.asset_loader import load_font
from config.settings import TILE, WHITE, GREEN, BROWN, YELLOW


class Altar(GameObject):
    """Bàn thờ trung tâm ở màn Boss (màn 5) — nơi mang 4 Artifact về đặt để 'tiến hoá' Ghost. Không tương tác được, chỉ hiển thị."""
    def __init__(self, x, y):
        """Tạo bàn thờ tại (x, y) với kích thước 2x2 ô lưới."""
        super().__init__(x, y, TILE*2, TILE*2, WHITE)

    def draw(self, surface, camera):
        """Vẽ khối bàn thờ kèm nhãn chữ 'ALTAR'."""
        r = camera.apply(self)
        pygame.draw.rect(surface, (80,72,60), r)
        pygame.draw.rect(surface, (120,108,90), r, 2)
        font = load_font("assets/04b_03.ttf", 12)
        t = font.render("ALTAR", True, (200,190,170))
        surface.blit(t, (r.centerx-t.get_width()//2, r.centery-t.get_height()//2))

class GreenDoor(Interactable):
    """Cửa chính giữa các màn — mặc định khoá (locked=True), chỉ mở khi người chơi hoàn thành đủ điều kiện (kéo hết Lever/bấm hết Button) của màn hiện tại."""
    def __init__(self, x, y):
        """Tạo cửa xanh tại (x, y), mặc định ở trạng thái khoá."""
        super().__init__(x, y, TILE*2, TILE*2, GREEN)
        self.locked = True

    def draw(self, surface, camera):
        """Vẽ cửa với dấu X đỏ khi đang khoá, hoặc màu xanh kèm chấm vàng (tay nắm) khi đã mở."""
        r = camera.apply(self)
        if self.locked:
            pygame.draw.rect(surface, (50, 50, 50), r)
            pygame.draw.rect(surface, (100, 100, 100), r, 2)
            pygame.draw.line(surface, (150, 0, 0), (r.x + 5, r.y + 5), (r.right - 5, r.bottom - 5), 3)
            pygame.draw.line(surface, (150, 0, 0), (r.right - 5, r.y + 5), (r.x + 5, r.bottom - 5), 3)
        else:
            pygame.draw.rect(surface, (20,80,30), r)
            pygame.draw.rect(surface, (40,160,60), r, 2)
            pygame.draw.circle(surface, YELLOW, (r.centerx+10, r.centery), 3)

    def interact(self, player, gs):
        """Nếu đang khoá: hiện cảnh báo và rung màn hình; nếu đã mở: chuyển gs.state sang 'DOOR_PROMPT' để qua màn kế tiếp."""
        if self.locked:
            gs.buff_popup_text = ["LOCKED! Complete objectives!"]
            gs.buff_popup_timer = 120
            gs.shake_intensity = 5
            return
        gs.state = "DOOR_PROMPT"

class WoodenDoor(Interactable):
    """Cửa gỗ ở hành lang an toàn — luôn mở, dẫn vào giao diện Cửa hàng (Shop) để nâng cấp chỉ số."""
    def __init__(self, x, y):
        """Tạo cửa gỗ tại (x, y)."""
        super().__init__(x, y, TILE*2, TILE*2, BROWN)

    def draw(self, surface, camera):
        """Vẽ cửa gỗ kèm tay nắm màu vàng."""
        r = camera.apply(self)
        pygame.draw.rect(surface, (100,60,20), r)
        pygame.draw.rect(surface, (140,90,40), r, 2)
        pygame.draw.line(surface, (60,35,10), (r.centerx, r.y+2),(r.centerx, r.bottom-2), 2)
        pygame.draw.circle(surface, YELLOW, (r.centerx-8, r.centery), 4)

    def interact(self, player, gs):
        """Chuyển gs.state sang 'SHOP' để mở giao diện cửa hàng nâng cấp."""
        gs.state = "SHOP"
