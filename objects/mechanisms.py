"""
objects/mechanisms.py
------------------------
Các cơ chế mở khoá trong mê cung: Lever (cần gạt, kéo tức thời) và
ButtonInteract (nút bấm, phải giữ phím E đủ lâu). Cả hai đều kế thừa
Interactable và được GameEngine đếm số lượng đã kích hoạt để quyết định khi
nào mở GreenDoor.
"""

import math

import pygame

from core.game_object import Interactable
from config.settings import TILE, DARK_GRAY, BLUE


class Lever(Interactable):
    """Cần gạt — kéo một lần là kích hoạt vĩnh viễn (pulled=True), tăng biến đếm levers_pulled và phát tiếng động lớn."""
    def __init__(self, x, y):
        """Tạo cần gạt tại (x, y), mặc định ở trạng thái chưa kéo (pulled=False)."""
        super().__init__(x, y, TILE, TILE, DARK_GRAY)
        self.pulled = False

    def draw(self, surface, camera):
        """Vẽ cần gạt dạng cơ khí (đế, rãnh trượt, thân cần, núm) đổi màu đỏ/xanh theo trạng thái pulled."""
        r = camera.apply(self)
        # Đế
        base_rect = pygame.Rect(r.x+3, r.y+r.height-10, r.width-6, 10)
        pygame.draw.rect(surface, (45,40,35), base_rect, border_radius=3)
        pygame.draw.rect(surface, (80,72,62), base_rect, 1, border_radius=3)
        pygame.draw.line(surface, (100,90,78),
                         (base_rect.x+2, base_rect.y+1),
                         (base_rect.right-2, base_rect.y+1), 1)
        # Rãnh trượt
        slot_x = r.centerx - 2
        pivot_y = r.y + r.height - 10
        pygame.draw.rect(surface, (20,18,15), (slot_x, pivot_y-4, 4, 10), border_radius=2)
        # Thân cần gạt
        arm_len   = r.height - 14
        angle_deg = -135 if self.pulled else -45
        angle_rad = math.radians(angle_deg)
        tip_x = r.centerx + int(math.cos(angle_rad) * arm_len)
        tip_y = pivot_y    + int(math.sin(angle_rad) * arm_len)
        arm_color = (0,160,60)  if self.pulled else (180,40,40)
        arm_dark  = (0,90,35)   if self.pulled else (100,20,20)
        pygame.draw.line(surface, arm_dark,  (r.centerx, pivot_y), (tip_x, tip_y), 6)
        pygame.draw.line(surface, arm_color, (r.centerx, pivot_y), (tip_x, tip_y), 4)
        # Núm
        knob_color = (0,220,80)   if self.pulled else (220,60,60)
        knob_shine = (80,255,140) if self.pulled else (255,130,130)
        pygame.draw.circle(surface, arm_dark,   (tip_x, tip_y), 7)
        pygame.draw.circle(surface, knob_color, (tip_x, tip_y), 6)
        pygame.draw.circle(surface, knob_shine, (tip_x-2, tip_y-2), 2)
        # Vít xoay
        pygame.draw.circle(surface, (55,50,45), (r.centerx, pivot_y), 4)
        pygame.draw.circle(surface, (90,82,70), (r.centerx, pivot_y), 3)
        # Label
        font_tiny = pygame.font.SysFont("Courier New", 8, bold=True)
        lbl_col   = (0,200,70) if self.pulled else (180,50,50)
        lbl = font_tiny.render("ON" if self.pulled else "OFF", True, lbl_col)
        surface.blit(lbl, (r.centerx - lbl.get_width()//2, r.y+2))

    def interact(self, player, gs):
        """Nếu chưa kéo: đặt pulled=True, tăng levers_pulled, phát âm thanh và tiếng động lớn để Ghost có thể nghe thấy."""
        if not self.pulled:
            self.pulled = True
            gs.levers_pulled += 1
            if gs.sfx_lever: gs.sfx_lever.play()
            gs.make_noise(self.rect.centerx, self.rect.centery, radius=0, is_loud=True)

class ButtonInteract(Interactable):
    """Nút bấm — phải giữ phím E liên tục 120 khung hình (2 giây ở 60 FPS) mới kích hoạt; bản thân không tự xử lý logic, GameEngine đọc hold_progress mỗi khung hình."""
    def __init__(self, x, y):
        """Tạo nút bấm tại (x, y) với tiến trình giữ phím (hold_progress) ban đầu bằng 0, cần đạt 120 khung hình để kích hoạt."""
        super().__init__(x+4, y+4, TILE-8, TILE-8, BLUE)
        self.hold_progress  = 0
        self.required_frames = 120

    def draw(self, surface, camera):
        """Vẽ nút bấm dạng thanh nạp (progress bar) theo tỉ lệ hold_progress/required_frames, nếu vẫn còn active."""
        if not self.active: return
        r = camera.apply(self)
        pygame.draw.rect(surface, (40,40,60), r)
        pct = self.hold_progress / self.required_frames
        h   = int((r.height-4)*pct)
        pygame.draw.rect(surface, (80,120,220),
                         (r.x+2, r.bottom-2-h, r.width-4, h))
        pygame.draw.rect(surface, (100,140,255), r, 1)

    def interact(self, player, gs):
        """Không xử lý gì (pass) — tiến trình giữ phím được cộng dồn ở EventHandlerMixin, không phải ở đây."""
        pass