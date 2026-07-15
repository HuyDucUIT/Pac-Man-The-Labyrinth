"""
engine/renderer.py
--------------------
RendererMixin — một trong 4 Mixin được GameEngine đa kế thừa, gom mọi hàm vẽ:
dựng bề mặt tĩnh của bản đồ (tile/tường) một lần khi sinh màn, vẽ hiệu ứng
sương mù/ánh sáng (fog of war) mỗi khung hình, vẽ lớp nền bản đồ, HUD (chỉ số,
icon nghe/nhìn), và giao diện Cửa hàng. Tách khỏi LevelManagerMixin (sinh dữ
liệu) và EventHandlerMixin (xử lý input) theo nguyên tắc SRP.
"""

import math
import random

import pygame

from config.settings import (
    TILE, FPS, BLACK, WHITE, GRAY, RED, YELLOW, MAGENTA,
    SCREEN_WIDTH, SCREEN_HEIGHT,
)
from objects.items import Dot, Candle, Note, Artifact, UnpickableCandle


class RendererMixin:
    """Gom mọi hàm vẽ: bản đồ tĩnh, sương mù/ánh sáng, HUD và giao diện Cửa hàng."""

    def build_visual_surface(self, w, h, walls_list):
        """Dựng một pygame.Surface tĩnh (vẽ một lần) thể hiện toàn bộ tile sàn và tường của bản đồ: phân loại từng ô lưới thành WALL/FLOOR, chọn ngẫu nhiên biến thể sprite tường/sàn/cửa sổ/bụi cây để tăng tính tự nhiên, rồi blit toàn bộ lên surface trả về (dùng lại mỗi khung hình thay vì vẽ lại)."""
        surf = pygame.Surface((w, h))
        surf.fill(BLACK)
        cols = w // TILE
        rows = h // TILE
        
        grid = [['FLOOR' for _ in range(rows)] for _ in range(cols)]
        for wall in walls_list:
            sx, sy = max(0, wall.x // TILE), max(0, wall.y // TILE)
            ex, ey = min(cols, (wall.x + wall.width) // TILE), min(rows, (wall.y + wall.height) // TILE)
            for x in range(sx, ex):
                for y in range(sy, ey):
                    grid[x][y] = 'WALL'
        
        if self.current_level == 5 and hasattr(self, 'center_room_rect') and self.center_room_rect:
            cr = self.center_room_rect
            # Không dọn dẹp biến tường bao thành FLOOR nữa, chỉ clear phần LÕI bên trong
            sx, sy = max(0, (cr.x + TILE*2) // TILE), max(0, (cr.y + TILE*2) // TILE)
            ex, ey = min(cols, (cr.x + cr.width - TILE*2) // TILE), min(rows, (cr.y + cr.height - TILE*2) // TILE)
            for x in range(sx, ex):
                for y in range(sy, ey):
                    grid[x][y] = 'FLOOR'

        visual_grid = [[None for _ in range(rows)] for _ in range(cols)]
        
        for x in range(cols):
            for y in range(rows):
                if grid[x][y] == 'WALL':
                    d = 0
                    while y + d + 1 < rows and grid[x][y + d + 1] == 'WALL':
                        d += 1
                        
                    is_adj_floor = False
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            if dx == 0 and dy == 0: continue
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < cols and 0 <= ny < rows:
                                if grid[nx][ny] == 'FLOOR':
                                    is_adj_floor = True
                                    break
                        if is_adj_floor: break
                    
                    if d <= 1 or is_adj_floor:
                        if d <= 1 and random.random() < 0.05:
                            visual_grid[x][y] = 'WALL_WINDOW'
                        else:
                            r = random.random()
                            if r < 0.7:
                                visual_grid[x][y] = 'WALL1'
                            elif r < 0.9:
                                visual_grid[x][y] = 'WALL2'
                            else:
                                visual_grid[x][y] = 'WALL3'
                    else:
                        visual_grid[x][y] = 'BLACK'
                else:
                    visual_grid[x][y] = 'FLOOR_EMPTY' 
        
        for x in range(cols):
            for y in range(rows):
                if visual_grid[x][y] == 'FLOOR_EMPTY':
                    if random.random() < 0.1:
                        visual_grid[x][y] = 'TILE2'
                    else:
                        visual_grid[x][y] = 'TILE1'

        for x in range(cols):
            for y in range(rows):
                if visual_grid[x][y] in ('TILE1', 'TILE2'):
                    if random.random() < 0.02:
                        bw = random.choice([2, 4, 6])
                        bh = random.choice([3, 4, 6])
                        clear = True
                        
                        for bx in range(-1, bw + 1):
                            for by in range(-1, bh + 1):
                                nx, ny = x + bx, y + by
                                if nx < 0 or nx >= cols or ny < 0 or ny >= rows:
                                    clear = False; break
                                if visual_grid[nx][ny] not in ('TILE1', 'TILE2'):
                                    clear = False; break
                            if not clear: break
                            
                        if clear:
                            for bx in range(bw):
                                for by in range(bh):
                                    visual_grid[x+bx][y+by] = 'BUSH'

        for x in range(cols):
            for y in range(rows):
                px, py = x * TILE, y * TILE
                v = visual_grid[x][y]
                if v == 'TILE1': surf.blit(self.spr_tile1, (px, py))
                elif v == 'TILE2': surf.blit(self.spr_tile2, (px, py))
                elif v == 'WALL1': surf.blit(self.spr_wall1, (px, py))
                elif v == 'WALL2': surf.blit(self.spr_wall2, (px, py))
                elif v == 'WALL3': surf.blit(self.spr_wall3, (px, py))
                elif v == 'WALL_WINDOW': surf.blit(self.spr_wallwindow, (px, py))
                elif v == 'BUSH': surf.blit(self.spr_bush, (px, py))
        return surf

    def render_lighting(self):
        """Tính lại lớp sương mù (fog of war) mỗi khung hình: tô đen toàn màn hình rồi 'đục lỗ' sáng quanh Dot/Candle/Note/Artifact, quanh Player (mở rộng nếu đang cầm nến), quanh mỗi Ghost (kể cả tay đang vươn ra), và quanh UnpickableCandle ở hành lang an toàn."""
        self.fog.fill((*BLACK, 255))
        
        def punch_hole(surface, x, y, radius, inner_alpha=0):
            hole = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            hole.fill((255, 255, 255, 255))
            pygame.draw.circle(hole, (255, 255, 255, inner_alpha), (radius, radius), radius)
            surface.blit(hole, (x-radius, y-radius), special_flags=pygame.BLEND_RGBA_MIN)

        def punch_candle_hole(surface, x, y, radius):
            hole = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            hole.fill((255, 255, 255, 255))
            ring_r = int(radius * 0.8)
            pygame.draw.circle(hole, (255, 255, 255, 127), (radius, radius), radius)
            pygame.draw.circle(hole, (255, 255, 255, 0), (radius, radius), ring_r)
            surface.blit(hole, (x-radius, y-radius), special_flags=pygame.BLEND_RGBA_MIN)

        if self.current_level==5 and hasattr(self, 'altar_obj') and self.altar_obj:
            r = self.camera.apply(self.altar_obj)
            punch_candle_hole(self.fog, r.center[0], r.center[1], int(self.center_room_rect.width * 0.8))

        for item in self.interactables:
            r = self.camera.apply(item)
            if isinstance(item,Dot) and item.active:
                punch_hole(self.fog, r.center[0], r.center[1], 4)
            elif isinstance(item,Candle) and item.active:
                punch_candle_hole(self.fog, r.center[0], r.center[1], int(self.player.stats.vision_radius*TILE))
            elif isinstance(item,Note) and item.active:
                punch_hole(self.fog, r.center[0], r.center[1], int(2.5*TILE))
            elif isinstance(item,Artifact) and item.active:
                punch_hole(self.fog, r.center[0], r.center[1], int(3*TILE))
                
        pr = self.camera.apply(self.player)
        player_radius = self.player.rect.width // 2 + 4
        punch_hole(self.fog, pr.center[0], pr.center[1], player_radius)
        
        if self.player.has_candle:
            punch_candle_hole(self.fog, pr.center[0], pr.center[1], self.player.get_candle_radius())
            
        for b in self.bosses:
            br = self.camera.apply(b)
            punch_hole(self.fog, br.center[0], br.center[1], int(TILE*1.5), 220)
            
            for hx_w, hy_w, hr, _ in b.get_hand_world_positions():
                hand_r = self.camera.apply_rect(pygame.Rect(hx_w, hy_w, 1, 1))
                punch_hole(self.fog, hand_r.x, hand_r.y, int(hr*2.0), 220)
                
        for item in getattr(self,'hall_items',[]):
            if isinstance(item,UnpickableCandle):
                r = self.camera.apply(item)
                punch_hole(self.fog, r.center[0], r.center[1], int(6.0*TILE))
                
        self.game_surface.blit(self.fog, (0,0))

    def draw_world(self):
        """Vẽ lớp nền bản đồ tĩnh (map_surface đã dựng sẵn) lên game_surface theo vị trí camera hiện tại."""
        ox, oy = self.camera.camera.topleft
        self.game_surface.blit(self.map_surface, (ox, oy))

    def draw_hud(self):
        """Vẽ các chỉ số trên màn hình khi chơi: tiến độ Lever/Button (hoặc số Artifact đã đặt ở màn 5), số xu, danh sách giác quan Ghost đã mở khoá, và hai icon loa/mắt báo hiệu tiếng ồn hoặc bị lộ."""
        if self.player.has_note:
            if self.current_level < 5:
                ms = f"Levers: {self.levers_pulled}/{self.target_levers}"
                if self.target_buttons > 0:
                    ms += f" | Buttons: {self.buttons_pressed}/{self.target_buttons}"
            else:
                ms = f"Artifacts: {self.m5_items_placed}/4"
                if self.m5_items_placed==4:
                    ms += f" | SURVIVE: {max(0,self.m5_survival_timer//FPS)}s"
            t1 = self.font.render(
                f"LV: {self.current_level} | {ms} | Coins: {self.player_stats.coins}", True, WHITE)
            
            if self.current_level == 5:
                skills = ["MOVE"]
                if self.m5_hear:  skills.append("HEAR")
                if self.m5_see:   skills.append("SEE")
                if self.m5_smell: skills.append("SMELL")
            elif self.current_level == 4:
                skills = ["MOVE", "HEAR", "SEE", "SMELL", "DUPLICATE"]
            else:
                skills = ["MOVE"]
                if self.current_level >= 2: skills.append("HEAR")
                if self.current_level >= 3: skills.append("SEE")
                if self.current_level >= 4: skills.append("SMELL")

            t2 = self.font.render(f"Ghost: {', '.join(skills)}", True, RED)
            self.screen.blit(t1, (20,20))
            self.screen.blit(t2, (20,48))
            if self.current_level==5 and self.carrying_item:
                ct = self.font.render("Carrying Artifact -> Take to Center Room!", True, MAGENTA)
                self.screen.blit(ct, (20,76))
        sx, sy = SCREEN_WIDTH-50, 20
        self.screen.blit(self.speaker_img, (sx, sy))
        if self.speaker_flash_timer > 0:
            col = RED if self.speaker_flash_loud else GRAY
            pygame.draw.rect(self.screen, col, (sx-2,sy-2,35,28), 2)
            self.speaker_flash_timer -= 1
        ex, ey = sx-70, 20
        self.screen.blit(self.eye_img, (ex, ey))
        if not self.player.is_hidden:
            pygame.draw.rect(self.screen, RED, (ex-2,ey-2,55,28), 2)

    def draw_shop_ui(self):
        """Vẽ toàn bộ giao diện Cửa hàng: tiêu đề, số dư xu, và danh sách 4 mục nâng cấp kèm giá tiền, mục đang chọn được đánh dấu bằng tam giác chỉ."""
        self.screen.fill((15,15,20))
        st = self.player_stats
        title = self.title_font.render("=== MAZE SHOP ===", True, YELLOW)
        coin  = self.font.render(f"Balance: {st.coins} Coins", True, WHITE)
        self.screen.blit(title, (SCREEN_WIDTH//2-title.get_width()//2, 80))
        self.screen.blit(coin,  (SCREEN_WIDTH//2-coin.get_width()//2, 140))
        sc = {0:"90c",1:"140c",2:"190c",3:"250c",4:"MAX"}
        upgrades = [
            (f"Speed (Lv {st.speed_level}/4)", sc[st.speed_level], st.speed_level<4),
            ("Candle +20% Vision",       "110c" if not st.candle_upgraded   else "OWNED", not st.candle_upgraded),
            ("Noise Reducer -20%",       "120c" if not st.muffler_upgraded  else "OWNED", not st.muffler_upgraded),
            ("Anti-smell Stealth -20%",  "150c" if not st.stealth_upgraded  else "OWNED", not st.stealth_upgraded),
        ]
        for i,(name,cost,avail) in enumerate(upgrades):
            col = WHITE if i==self.shop_selected_index else (70,65,60)
            if not avail: col = (70,65,60)
            if i==self.shop_selected_index:
                pygame.draw.polygon(self.screen, WHITE,
                    [(118,240+i*60-8),(130,240+i*60),(118,240+i*60+8)])
            self.screen.blit(self.font.render(name, True, col),  (140, 240+i*60))
            self.screen.blit(self.font.render(cost, True, YELLOW if avail else col), (680, 240+i*60))
        guide = self.font.render("[UP/DOWN] Select  [ENTER] Buy  [ESC] Exit", True, WHITE)
        self.screen.blit(guide, (SCREEN_WIDTH//2-guide.get_width()//2, SCREEN_HEIGHT-100))
