import pygame
import math
import random
import sys
import os
from abc import ABC, abstractmethod

# ================= CẤU HÌNH & HẰNG SỐ =================
SCREEN_WIDTH, SCREEN_HEIGHT = 1024, 768
ZOOM = 1.5  
GAME_WIDTH = int(SCREEN_WIDTH / ZOOM)
GAME_HEIGHT = int(SCREEN_HEIGHT / ZOOM)

BASE_MAP_W, BASE_MAP_H = 3200, 2400
TILE = 32
FPS = 60

# Màu sắc
BLACK = (5, 5, 5)
WHITE = (240, 240, 240)
DARK_GRAY = (30, 30, 30)
GRAY = (120, 120, 120)  
RED = (200, 20, 20)
YELLOW = (255, 220, 0)
ORANGE = (255, 150, 50)
MAGENTA = (255, 0, 255)
GREEN = (0, 200, 0)
BLUE = (0, 150, 255)
BROWN = (139, 69, 19)

# Hàm hỗ trợ tải Asset an toàn
def load_font(name, size):
    variations = [name, name.lower(), name.upper(), "04B_03__.TTF", "04b_03.ttf"]
    for f_name in variations:
        try:
            return pygame.font.Font(f_name, size)
        except:
            pass
    return pygame.font.SysFont("Courier New", size, bold=True)

def load_img(name, scale):
    try:
        return pygame.transform.scale(pygame.image.load(name).convert_alpha(), scale)
    except:
        s = pygame.Surface(scale, pygame.SRCALPHA)
        s.fill(MAGENTA)
        return s

def load_sound(name):
    try:
        return pygame.mixer.Sound(name)
    except:
        return None

# ================= LƯU TRỮ CHỈ SỐ PLAYER =================
class PlayerStats:
    def __init__(self):
        self.coins = 0
        self.speed_level = 0  
        self.speed = 2.0      
        self.candle_upgraded = False  
        self.vision_radius = 6.0      
        self.muffler_upgraded = False 
        self.noise_radius = 10.0      
        self.stealth_upgraded = False 
        self.smell_modifier = 1.0     

# ================= CAMERA =================
class Camera:
    def __init__(self, map_width, map_height):
        self.camera = pygame.Rect(0, 0, map_width, map_height)
        self.map_width = map_width
        self.map_height = map_height
        self.cam_x = 0.0
        self.cam_y = 0.0

    def snap(self, target):
        self.cam_x = -target.rect.centerx + int(GAME_WIDTH / 2)
        self.cam_y = -target.rect.centery + int(GAME_HEIGHT / 2)
        self.update_rect()

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)

    def apply_rect(self, rect):
        return rect.move(self.camera.topleft)

    def update(self, target):
        target_x = -target.rect.centerx + int(GAME_WIDTH / 2)
        target_y = -target.rect.centery + int(GAME_HEIGHT / 2)
        # Giảm hệ số nội suy xuống 0.04 để tăng độ trễ (camera lag) phía sau người chơi
        self.cam_x += (target_x - self.cam_x) * 0.06
        self.cam_y += (target_y - self.cam_y) * 0.06
        self.update_rect()

    def update_rect(self):
        x = min(0, self.cam_x)  
        y = min(0, self.cam_y)  
        x = max(-(self.map_width - GAME_WIDTH), x)  
        y = max(-(self.map_height - GAME_HEIGHT), y)  
        self.camera = pygame.Rect(int(x), int(y), self.map_width, self.map_height)

# ================= OOP: ABSTRACTION & BASE CLASSES =================
class GameObject(ABC):
    def __init__(self, x, y, width, height, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.active = True

    @abstractmethod
    def draw(self, surface, camera):
        pass

class Interactable(GameObject):
    @abstractmethod
    def interact(self, player, game_state):
        pass

class Entity(GameObject):
    """
    Lớp cơ sở cho các đối tượng có thể di chuyển (Player, StalkerBoss).
    Gom nhóm logic xử lý vị trí số thực (float) và va chạm với tường (wall collision).
    """
    def __init__(self, x, y, width, height, color, speed=0.0):
        super().__init__(x, y, width, height, color)
        self.x = float(x)
        self.y = float(y)
        self.speed = speed
        self.current_speed = speed

    def move_and_collide(self, dx, dy, walls, ignore_walls=False):
        """Di chuyển Entity và xử lý va chạm độc lập cho 2 trục X, Y. Trả về True nếu đụng tường."""
        collided = False
        
        # Trục X
        self.x += dx
        self.rect.x = int(self.x)
        if not ignore_walls:
            for w in walls:
                if self.rect.colliderect(w):
                    collided = True
                    if dx > 0: self.rect.right = w.left
                    if dx < 0: self.rect.left = w.right
                    self.x = float(self.rect.x)
                    break

        # Trục Y
        self.y += dy
        self.rect.y = int(self.y)
        if not ignore_walls:
            for w in walls:
                if self.rect.colliderect(w):
                    collided = True
                    if dy > 0: self.rect.bottom = w.top
                    if dy < 0: self.rect.top = w.bottom
                    self.y = float(self.rect.y)
                    break
                    
        return collided

# ================= VẬT PHẨM & CƠ CHẾ TƯƠNG TÁC =================
class Dot(Interactable):
    def __init__(self, x, y):
        super().__init__(x + 12, y + 12, 8, 8, YELLOW)
    def draw(self, surface, camera):
        if self.active: pygame.draw.rect(surface, self.color, camera.apply(self))
    def interact(self, player, game_state):
        if self.active:
            player.stats.coins += 10
            self.active = False
            game_state.make_noise(self.rect.centerx, self.rect.centery, radius=player.stats.noise_radius * TILE, is_loud=False)

class Lever(Interactable):
    def __init__(self, x, y):
        super().__init__(x, y, TILE, TILE, DARK_GRAY)
    def draw(self, surface, camera):
        if self.active:
            rect = camera.apply(self)
            pygame.draw.rect(surface, (80, 80, 80), rect)
            pygame.draw.rect(surface, BLACK, (rect.centerx - 4, rect.y + 4, 8, 24))
            pygame.draw.line(surface, RED, (rect.centerx, rect.y + 8), (rect.centerx, rect.y + 24), 4)
            pygame.draw.circle(surface, RED, (rect.centerx, rect.y + 8), 5)
    def interact(self, player, game_state):
        if self.active:
            self.active = False
            game_state.levers_pulled += 1
            if game_state.sfx_lever: game_state.sfx_lever.play()
            game_state.make_noise(self.rect.centerx, self.rect.centery, radius=0, is_loud=True)

class ButtonInteract(Interactable):
    def __init__(self, x, y):
        super().__init__(x + 4, y + 4, TILE - 8, TILE - 8, BLUE)
        self.hold_progress = 0
        self.required_frames = 120 
    def draw(self, surface, camera):
        if self.active:
            rect = camera.apply(self)
            pygame.draw.rect(surface, (50, 50, 50), rect)
            pct = self.hold_progress / self.required_frames
            h = int((rect.height - 4) * pct)
            pygame.draw.rect(surface, self.color, (rect.x + 2, rect.bottom - 2 - h, rect.width - 4, h))
            pygame.draw.rect(surface, WHITE, (rect.x + 2, rect.y + 2, rect.width - 4, rect.height - 4), 1)
    def interact(self, player, game_state):
        pass 

class Note(Interactable):
    def __init__(self, x, y):
        super().__init__(x + 8, y + 8, 16, 16, WHITE)
    def draw(self, surface, camera):
        if self.active:
            rect = camera.apply(self)
            pygame.draw.rect(surface, self.color, rect)
            pygame.draw.line(surface, BLACK, (rect.x + 3, rect.y + 4), (rect.x + 13, rect.y + 4), 1)
            pygame.draw.line(surface, BLACK, (rect.x + 3, rect.y + 8), (rect.x + 10, rect.y + 8), 1)
            pygame.draw.line(surface, BLACK, (rect.x + 3, rect.y + 12), (rect.x + 13, rect.y + 12), 1)
    def interact(self, player, game_state):
        if self.active:
            player.has_note = True
            self.active = False

class Candle(Interactable):
    def __init__(self, x, y):
        super().__init__(x + 8, y + 8, 16, 16, ORANGE)
    def draw(self, surface, camera):
        if self.active:
            rect = camera.apply(self)
            pygame.draw.rect(surface, self.color, rect)
            pygame.draw.rect(surface, YELLOW, (rect.x + 4, rect.y - 6, 8, 6))
    def interact(self, player, game_state):
        pass

class UnpickableCandle(GameObject):
    def __init__(self, x, y):
        super().__init__(x + 8, y + 8, 16, 16, ORANGE)
    def draw(self, surface, camera):
        rect = camera.apply(self)
        pygame.draw.rect(surface, self.color, rect)
        pygame.draw.rect(surface, YELLOW, (rect.x + 4, rect.y - 6, 8, 6))

class SpecialItem(Interactable):
    def __init__(self, x, y):
        super().__init__(x + 4, y + 4, 24, 24, MAGENTA)
    def draw(self, surface, camera):
        if self.active:
            rect = camera.apply(self)
            pygame.draw.rect(surface, self.color, rect)
            # Bỏ việc đánh số trên SpecialItem
    def interact(self, player, game_state):
        # Trạng thái carrying_item giờ mang giá trị bool
        if self.active and not game_state.carrying_item:
            game_state.carrying_item = True
            self.active = False

class Altar(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y, TILE * 2, TILE * 2, WHITE)
    def draw(self, surface, camera):
        rect = camera.apply(self)
        pygame.draw.rect(surface, (100, 100, 100), rect)
        pygame.draw.rect(surface, WHITE, rect, 2)
        font = load_font("04b_03.ttf", 14)
        txt = font.render("ALTAR", True, WHITE)
        surface.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))

class GreenDoor(Interactable):
    def __init__(self, x, y):
        super().__init__(x, y, TILE * 2, TILE * 2, GREEN)
    def draw(self, surface, camera):
        rect = camera.apply(self)
        pygame.draw.rect(surface, self.color, rect)
        pygame.draw.rect(surface, WHITE, rect, 2)
    def interact(self, player, game_state):
        game_state.state = "DOOR_PROMPT"

class WoodenDoor(Interactable):
    def __init__(self, x, y):
        super().__init__(x, y, TILE * 2, TILE * 2, BROWN)
    def draw(self, surface, camera):
        rect = camera.apply(self)
        pygame.draw.rect(surface, self.color, rect)
        pygame.draw.rect(surface, BLACK, (rect.x + rect.width//2 - 2, rect.y, 4, rect.height))
        pygame.draw.circle(surface, YELLOW, (rect.x + 12, rect.centery), 4)
    def interact(self, player, game_state):
        game_state.state = "SHOP"

# ================= PLAYER (PAC-MAN) =================
class Player(Entity):
    def __init__(self, x, y, stats):
        super().__init__(x, y, TILE - 4, TILE - 4, YELLOW, stats.speed)
        self.stats = stats
        self.has_candle = False
        self.has_note = False  
        self.is_hidden = True 
        
        self.facing_angle = 0  
        self.mouth_angle = 0
        self.mouth_speed = 4
        self.mouth_dir = 1
        self.step_timer = 0

    def move(self, keys, walls, game_state):
        dx, dy = 0, 0
        self.speed = self.stats.speed # Lấy speed hiện tại từ stats
        
        if keys[pygame.K_w] or keys[pygame.K_UP]: dy -= self.speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy += self.speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx -= self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += self.speed

        if dx != 0 or dy != 0:
            self.facing_angle = math.degrees(math.atan2(-dy, dx))
            if self.facing_angle < 0:
                self.facing_angle += 360

            self.mouth_angle += self.mouth_speed * self.mouth_dir
            if self.mouth_angle >= 45:
                self.mouth_angle = 45
                self.mouth_dir = -1
            elif self.mouth_angle <= 0:
                self.mouth_angle = 0
                self.mouth_dir = 1
                
            self.step_timer -= 1
            if self.step_timer <= 0:
                if game_state.sfx_step: game_state.sfx_step.play()
                self.step_timer = 19
        else:
            self.mouth_angle = 0 

        # Delegate xử lý di chuyển và va chạm cho Entity
        self.move_and_collide(dx, dy, walls, ignore_walls=False)

    def get_candle_radius(self): 
        return int(self.stats.vision_radius * TILE)
    
    def draw(self, surface, camera):
        rect = camera.apply(self)
        center = rect.center
        radius = self.rect.width // 2
        draw_color = self.color if not self.is_hidden else GRAY
        
        if self.mouth_angle > 0:
            points = [center]
            start_angle = self.facing_angle + self.mouth_angle
            end_angle = self.facing_angle + 360 - self.mouth_angle
            steps = 30 
            
            for i in range(steps + 1):
                ang = math.radians(start_angle + i * (end_angle - start_angle) / steps)
                px = center[0] + radius * math.cos(ang)
                py = center[1] - radius * math.sin(ang)
                points.append((px, py))
                
            pygame.draw.polygon(surface, draw_color, points)
        else:
            pygame.draw.circle(surface, draw_color, center, radius)

# ================= AI: SENSORY BOSS STATE MACHINE =================
class StalkerBoss(Entity):
    def __init__(self, x, y, level):
        super().__init__(x, y, TILE, TILE, RED, 3.5)
        self.level = level
        self.state = "ROAM" 
        self.target_pos = None

        self.can_hear = level >= 2
        self.can_see = level >= 3
        self.can_smell = level >= 4
        self.smell_timer = 0
        
        self.dir_x = 0
        self.dir_y = 0
        self.stomp_timer = 0
        self.is_large = False 

    def update_skills_m5(self, hear, see, smell):
        self.can_hear = hear
        self.can_see = see
        self.can_smell = smell

    def update(self, player, walls, map_w, map_h, game_state):
        if self.state == "CHASE":
            if player.is_hidden or not self.check_line_of_sight(player, walls):
                self.state = "INVESTIGATE"
            else:
                self.current_speed = self.speed  
                self.target_pos = (player.rect.centerx, player.rect.centery)
        
        if self.state != "CHASE":
            if self.can_see and not player.is_hidden:
                dist_to_player = math.hypot(player.rect.centerx - self.rect.centerx, player.rect.centery - self.rect.centery)
                if dist_to_player <= 8 * TILE:
                    if self.check_line_of_sight(player, walls):
                        self.state = "CHASE"
                        self.target_pos = (player.rect.centerx, player.rect.centery)

            if self.can_smell and self.state != "CHASE":
                dist_to_player = math.hypot(player.rect.centerx - self.rect.centerx, player.rect.centery - self.rect.centery)
                limit = 3.5 * TILE * player.stats.smell_modifier
                if dist_to_player <= limit:
                    self.state = "SMELL_SEARCH"
                    self.target_pos = (player.rect.centerx, player.rect.centery)
                    self.smell_timer = 120  

        if self.state == "ROAM":
            self.current_speed = self.speed * 0.6  
            if not self.target_pos or random.random() < 0.02:
                nx = max(TILE, min(map_w - TILE, self.rect.centerx + random.randint(-400, 400)))
                ny = max(TILE, min(map_h - TILE, self.rect.centery + random.randint(-400, 400)))
                self.target_pos = (nx, ny)

        elif self.state == "INVESTIGATE":
            self.current_speed = self.speed  
            if self.target_pos:
                dist = math.hypot(self.target_pos[0] - self.rect.centerx, self.target_pos[1] - self.rect.centery)
                if dist < 15:  
                    self.state = "ROAM"
                    self.target_pos = None

        elif self.state == "SMELL_SEARCH":
            self.current_speed = self.speed * 0.4  
            self.smell_timer -= 1
            if self.smell_timer <= 0:
                self.state = "ROAM"
                self.target_pos = None

        if self.target_pos:
            ignore_walls = (self.state in ["INVESTIGATE", "CHASE"])
            self._move_towards_target(walls, ignore_walls, game_state)

    def check_line_of_sight(self, player, walls):
        start = self.rect.center
        end = player.rect.center
        dist = math.hypot(end[0] - start[0], end[1] - start[1])
        if dist == 0: return True
        steps = int(dist / 8)
        for i in range(1, steps):
            t = i / steps
            cx = int(start[0] + (end[0] - start[0]) * t)
            cy = int(start[1] + (end[1] - start[1]) * t)
            point_rect = pygame.Rect(cx - 2, cy - 2, 4, 4)
            for w in walls:
                if point_rect.colliderect(w):
                    return False
        return True

    def hear_noise(self, x, y, radius, noise_modifier):
        if self.can_hear and self.state != "CHASE":
            dist = math.hypot(x - self.rect.centerx, y - self.rect.centery)
            if dist <= radius * noise_modifier:
                self.state = "INVESTIGATE"
                self.target_pos = (x, y)

    def _move_towards_target(self, walls, ignore_walls, game_state):
        tx, ty = self.target_pos
        dx, dy = tx - self.rect.centerx, ty - self.rect.centery
        dist = math.hypot(dx, dy)

        if dist > self.current_speed:
            nx = (dx / dist) * self.current_speed
            ny = (dy / dist) * self.current_speed
            
            hit_wall = self.move_and_collide(nx, ny, walls, ignore_walls)
            if hit_wall and self.state == "ROAM":
                self.target_pos = None
            
            self.dir_x = 1 if nx > 0 else (-1 if nx < 0 else 0)
            self.dir_y = 1 if ny > 0 else (-1 if ny < 0 else 0)
            
            self.stomp_timer -= 1
            if self.stomp_timer <= 0:
                if game_state.sfx_stomp:
                    player_dist = math.hypot(self.rect.centerx - game_state.player.rect.centerx, self.rect.centery - game_state.player.rect.centery)
                    vol_scale = max(0.0, 1.0 - (player_dist / SCREEN_WIDTH))
                    game_state.sfx_stomp.set_volume(vol_scale * 0.12 * game_state.global_volume)
                    game_state.sfx_stomp.play()
                
                self.stomp_timer = 25 if self.state == "CHASE" else 60
        else:
            if self.state == "ROAM": self.target_pos = None

    def resolve_overlap(self, other_boss):
        """Xử lý đẩy tách nhau ra nếu hai con Ghost trùng vị trí (Hitbox collision)"""
        dx = self.rect.centerx - other_boss.rect.centerx
        dy = self.rect.centery - other_boss.rect.centery
        dist = math.hypot(dx, dy)
        
        min_dist = TILE * 1.5 if self.is_large else TILE
        if dist < min_dist:
            if dist == 0:
                dx, dy = random.choice([-1, 1]), random.choice([-1, 1])
                dist = 1.414
            push_force = (min_dist - dist) / 2
            px = (dx / dist) * push_force
            py = (dy / dist) * push_force
            
            self.x += px; self.y += py
            other_boss.x -= px; other_boss.y -= py
            
            self.rect.x, self.rect.y = int(self.x), int(self.y)
            other_boss.rect.x, other_boss.rect.y = int(other_boss.x), int(other_boss.y)

    def draw(self, surface, camera):
        rect = camera.apply(self)
        scale_mod = 1.5 if self.is_large else 1.0
        r = int((TILE // 2 - 2) * scale_mod)
        x, y = rect.centerx, rect.centery
        draw_color = self.color

        glow = pygame.Surface((r*4, r*4), pygame.SRCALPHA)
        glow_c = (draw_color[0], draw_color[1], draw_color[2], 40)
        pygame.draw.circle(glow, glow_c, (r*2, r*2), r*2)
        surface.blit(glow, (x - r*2, y - r*2 - int(2*scale_mod)))

        pygame.draw.circle(surface, draw_color, (x, y - int(2*scale_mod)), r)
        pygame.draw.rect(surface, draw_color, (x - r, y - int(2*scale_mod), r * 2, r + int(2*scale_mod)))

        lighter = tuple(min(255, ch + 70) for ch in draw_color)
        pygame.draw.arc(surface, lighter,
                        pygame.Rect(x - r, y - int(2*scale_mod) - r, r*2, r*2),
                        0, math.pi, 2)

        wave_t = pygame.time.get_ticks() / 300.0
        seg_w = (r * 2) / 4
        for i in range(4):
            sx = x - r + i * seg_w
            wave = math.sin(wave_t + i * 1.0) * (2 * scale_mod)
            pts = [
                (sx, y + r),
                (sx + seg_w / 2, y + r - int(4*scale_mod) + wave),
                (sx + seg_w, y + r),
                (sx + seg_w, y),
                (sx, y),
            ]
            pygame.draw.polygon(surface, draw_color, pts)

        eo = int(8 * scale_mod)
        ew = int(6 * scale_mod)
        eh = int(8 * scale_mod)
        pygame.draw.ellipse(surface, WHITE, (x - eo, y - eo, ew, eh))
        pygame.draw.ellipse(surface, WHITE, (x + int(2*scale_mod), y - eo, ew, eh))
        
        px_off = int(self.dir_x * 2 * scale_mod)
        py_off = int(self.dir_y * 2 * scale_mod)
        pygame.draw.circle(surface, (0, 0, 180), (x - int(5*scale_mod) + px_off, y - int(4*scale_mod) + py_off), max(1, int(3*scale_mod)))
        pygame.draw.circle(surface, (0, 0, 180), (x + int(5*scale_mod) + px_off, y - int(4*scale_mod) + py_off), max(1, int(3*scale_mod)))
        pygame.draw.circle(surface, WHITE, (x - int(4*scale_mod) + px_off, y - int(5*scale_mod) + py_off), max(1, int(1*scale_mod)))
        pygame.draw.circle(surface, WHITE, (x + int(6*scale_mod) + px_off, y - int(5*scale_mod) + py_off), max(1, int(1*scale_mod)))

# ================= QUẢN LÝ TIẾN TRÌNH GAME ENGINE =================
class GameEngine:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Pac-man The Labyrinth")
        
        self.game_surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
        self.fog = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
        
        self.clock = pygame.time.Clock()
        self.font = load_font("04b_03.ttf", 20)
        self.title_font = load_font("04b_03.ttf", 44)
        self.small_title_font = load_font("04b_03.ttf", 30) 
        
        self.player_stats = PlayerStats()
        self.level_start_coins = 0 
        self.current_level = 1
        self.state = "MENU"
        self.shop_selected_index = 0
        
        self.sfx_step = load_sound("playerStep.wav")
        self.sfx_stomp = load_sound("heavy stomp.wav")
        self.sfx_lever = load_sound("breaker.wav")
        self.sfx_button = load_sound("breaker alarm.wav")
        self.sfx_grab = load_sound("grab.wav")
        
        self.eye_img = load_img("eye.png", (51, 24))
        self.speaker_img = load_img("speaker.png", (31, 24))
        
        self.speaker_flash_timer = 0
        self.speaker_flash_loud = False
        
        self.shake_intensity = 0
        
        self.current_bgm = None
        self.bgm_fading = False
        self.fade_timer = 0
        
        self.btn_labyrinth = pygame.Rect(SCREEN_WIDTH//2 - 150, 400, 300, 50)
        self.btn_classic = pygame.Rect(SCREEN_WIDTH//2 - 150, 470, 300, 50)
        
        self.vol_rect = pygame.Rect(SCREEN_WIDTH//2 - 150, 580, 300, 20)
        self.global_volume = 1.0
        self._update_volume()
        
        self.buff_popup_text = ""
        self.buff_popup_timer = 0

    def _update_volume(self):
        if self.sfx_step: self.sfx_step.set_volume(self.global_volume * 0.3825)
        if self.sfx_lever: self.sfx_lever.set_volume(self.global_volume * 0.54) 
        if self.sfx_button: self.sfx_button.set_volume(self.global_volume * 0.48) 
        if self.sfx_grab: self.sfx_grab.set_volume(self.global_volume * 0.8)
        
        pygame.mixer.music.set_volume(self.global_volume * 0.38)

    def get_valid_spawn_pos(self, obj_w, obj_h):
        while True:
            tx = random.randint(1, (self.map_w // TILE) - 2) * TILE
            ty = random.randint(1, (self.map_h // TILE) - 2) * TILE
            rect = pygame.Rect(tx, ty, obj_w, obj_h)
            if rect.collidelist(self.walls) == -1:
                if self.current_level == 5 and hasattr(self, 'center_room_rect'):
                    if rect.colliderect(self.center_room_rect):
                        continue
                return tx, ty

    def generate_map(self):
        self.walls = []
        self.walls.append(pygame.Rect(0, 0, self.map_w, TILE))
        self.walls.append(pygame.Rect(0, self.map_h - TILE, self.map_w, TILE))
        self.walls.append(pygame.Rect(0, 0, TILE, self.map_h))
        self.walls.append(pygame.Rect(self.map_w - TILE, 0, TILE, self.map_h))

        if self.current_level == 5:
            rw = int(self.map_w * 0.63)
            rh = int(self.map_h * 0.63)
            rx = (self.map_w - rw) // 2
            ry = (self.map_h - rh) // 2
            self.center_room_rect = pygame.Rect(rx, ry, rw, rh)

            gate_size = TILE * 3
            self.walls.append(pygame.Rect(rx, ry, (rw - gate_size) // 2, TILE))
            self.walls.append(pygame.Rect(rx + (rw + gate_size) // 2, ry, (rw - gate_size) // 2, TILE))
            self.walls.append(pygame.Rect(rx, ry + rh - TILE, (rw - gate_size) // 2, TILE))
            self.walls.append(pygame.Rect(rx + (rw + gate_size) // 2, ry + rh - TILE, (rw - gate_size) // 2, TILE))
            self.walls.append(pygame.Rect(rx, ry, TILE, (rh - gate_size) // 2))
            self.walls.append(pygame.Rect(rx, ry + (rh + gate_size) // 2, TILE, (rh - gate_size) // 2))
            self.walls.append(pygame.Rect(rx + rw - TILE, ry, TILE, (rh - gate_size) // 2))
            self.walls.append(pygame.Rect(rx + rw - TILE, ry + (rh + gate_size) // 2, TILE, (rh - gate_size) // 2))
        else:
            center_x, center_y = self.map_w // 2, self.map_h // 2
            for x in range(TILE * 4, self.map_w - TILE * 4, TILE * 10):
                for y in range(TILE * 4, self.map_h - TILE * 4, TILE * 8):
                    if abs(x - center_x) < TILE * 6 and abs(y - center_y) < TILE * 6:
                        continue
                    if random.random() > 0.15: 
                        w = random.choice([TILE * 2, TILE * 4, TILE * 6])
                        h = random.choice([TILE * 2, TILE * 4])
                        self.walls.append(pygame.Rect(x, y, w, h))

    def reset_game(self, next_level=False, keep_stats=False):
        if not keep_stats:
            if not next_level:
                self.player_stats = PlayerStats()
            self.level_start_coins = self.player_stats.coins
        else:
            self.player_stats.coins = self.level_start_coins

        self.m5_doors_closed = False
        self.buff_popup_timer = 0
        
        scales = {1: 0.5, 2: 0.6, 3: 0.8, 4: 1.0, 5: 0.8}
        current_scale = scales[self.current_level]
        self.map_w = int(BASE_MAP_W * current_scale)
        self.map_h = int(BASE_MAP_H * current_scale)
        
        self.camera = Camera(self.map_w, self.map_h)
        self.generate_map()
        
        self.player = Player(self.map_w // 2, self.map_h // 2, self.player_stats)
        
        boss_count = 2 if self.current_level == 4 else 1
        self.bosses = [StalkerBoss(TILE * 8, TILE * 8, self.current_level) for _ in range(boss_count)]
        
        self.interactables = []
        self.levers_pulled = 0
        self.buttons_pressed = 0
        self.door_spawned = False
        
        self.m5_hear = False
        self.m5_see = False
        self.m5_smell = False
        self.carrying_item = False 
        self.m5_items_placed = 0
        self.m5_survival_timer = 60 * FPS 

        level_reqs = {1: (2, 0), 2: (3, 0), 3: (3, 1), 4: (4, 3), 5: (0, 0)}
        self.target_levers, self.target_buttons = level_reqs[self.current_level]

        dot_counts = {1: 30, 2: 40, 3: 50, 4: 60, 5: 40}
        for _ in range(dot_counts[self.current_level]):
            x, y = self.get_valid_spawn_pos(TILE, TILE)
            self.interactables.append(Dot(x, y))

        # Tùy chỉnh số lượng nến sinh ra ở Level 3 (+75%) và Level 4 (+100%)
        candle_counts = {1: 8, 2: 8, 3: 14, 4: 16, 5: 8}
        num_candles = candle_counts[self.current_level]
        for _ in range(num_candles):
            x, y = self.get_valid_spawn_pos(TILE, TILE)
            self.interactables.append(Candle(x, y))

        for _ in range(self.target_levers):
            x, y = self.get_valid_spawn_pos(TILE, TILE)
            self.interactables.append(Lever(x, y))

        for _ in range(self.target_buttons):
            x, y = self.get_valid_spawn_pos(TILE, TILE)
            self.interactables.append(ButtonInteract(x, y))

        if self.current_level == 5:
            self.altar_obj = Altar(self.map_w // 2 - TILE, self.map_h // 2 - TILE)
            corners = [(TILE * 3, TILE * 3), (self.map_w - TILE * 4, TILE * 3), 
                       (TILE * 3, self.map_h - TILE * 4), (self.map_w - TILE * 4, self.map_h - TILE * 4)]
            # Không đánh số Item nữa
            for pos in corners:
                self.interactables.append(SpecialItem(pos[0], pos[1]))

        self.interactables.append(Candle(self.map_w // 2 - TILE * 2, self.map_h // 2))
        self.interactables.append(Note(self.map_w // 2 + TILE * 2, self.map_h // 2))
        
        self.camera.snap(self.player)
        self.state = "LEVEL_INTRO"

    def enter_hallway(self):
        self.state = "HALLWAY"
        self.hall_w, self.hall_h = 1200, 400
        self.camera = Camera(self.hall_w, self.hall_h)
        
        self.hall_walls = [
            pygame.Rect(0, 0, self.hall_w, TILE),
            pygame.Rect(0, self.hall_h - TILE, self.hall_w, TILE),
            pygame.Rect(0, 0, TILE, self.hall_h),
            pygame.Rect(self.hall_w - TILE, 0, TILE, self.hall_h)
        ]
        self.player.x, self.player.y = 100.0, 200.0
        self.player.rect.topleft = (int(self.player.x), int(self.player.y))
        
        self.hall_items = [
            WoodenDoor(550, 200 - TILE), 
            GreenDoor(1050, 200 - TILE),
            UnpickableCandle(510, 200)
        ]
        self.camera.snap(self.player)

    def make_noise(self, x, y, radius, is_loud):
        self.speaker_flash_timer = 60
        self.speaker_flash_loud = is_loud
        
        if is_loud: 
            self.shake_intensity = 30  
            radius = 999999 
            
        for b in self.bosses:
            b.hear_noise(x, y, radius, 1.0)

    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
                
            if self.state == "MENU":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.btn_labyrinth.collidepoint(mouse_pos):
                        self.reset_game(next_level=False)
                    elif self.btn_classic.collidepoint(mouse_pos):
                        pass 
            
            if event.type == pygame.KEYDOWN:
                if self.state == "LEVEL_INTRO":
                    if event.key == pygame.K_SPACE:
                        self.state = "PLAYING"
                        
                elif self.state == "JUMPSCARE":
                    if event.key == pygame.K_SPACE:
                        self.reset_game(next_level=False, keep_stats=True)
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "MENU"

                elif self.state == "VICTORY_SCREEN":
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_SPACE:
                        self.state = "MENU"
                        
                elif self.state == "DOOR_PROMPT":
                    if event.key == pygame.K_y: 
                        self.enter_hallway()
                    elif event.key == pygame.K_n: 
                        self.state = "PLAYING"
                        self.player.x -= 40  

                elif self.state == "SHOP":
                    if event.key == pygame.K_UP:
                        self.shop_selected_index = (self.shop_selected_index - 1) % 4
                    elif event.key == pygame.K_DOWN:
                        self.shop_selected_index = (self.shop_selected_index + 1) % 4
                    elif event.key == pygame.K_RETURN:
                        self.buy_shop_upgrade()
                    elif event.key == pygame.K_ESCAPE or event.key == pygame.K_BACKSPACE:
                        self.state = "HALLWAY" 

                elif self.state in ["PLAYING", "HALLWAY"]:
                    if event.key == pygame.K_ESCAPE:
                        self.state = "MENU"
                        
                    if event.key == pygame.K_e:
                        items_list = self.hall_items if self.state == "HALLWAY" else self.interactables
                        interacted_with_obj = False
                        
                        for item in items_list:
                            if isinstance(item, (Note, Lever, GreenDoor, WoodenDoor)) and item.active and self.player.rect.colliderect(item.rect):
                                item.interact(self.player, self)
                                interacted_with_obj = True
                                break

                            if self.current_level == 5 and self.state == "PLAYING":
                                if self.player.rect.colliderect(self.altar_obj.rect) and self.carrying_item:
                                    self.m5_items_placed += 1
                                    buff_name = ""
                                    
                                    # Kích hoạt buff theo thứ tự đặt vào
                                    if self.m5_items_placed == 1: 
                                        self.m5_hear = True
                                        buff_name = "Ghost can HEAR"
                                    elif self.m5_items_placed == 2: 
                                        self.m5_see = True
                                        buff_name = "Ghost can SEE"
                                    elif self.m5_items_placed == 3: 
                                        self.m5_smell = True
                                        buff_name = "Ghost can SMELL"
                                    elif self.m5_items_placed == 4:
                                        new_boss = StalkerBoss(self.bosses[0].rect.x, self.bosses[0].rect.y, 5)
                                        self.bosses.append(new_boss)
                                        buff_name = "Ghost can DUPLICATE & Ghosts are LARGE"
                                    
                                    self.buff_popup_text = buff_name
                                    self.buff_popup_timer = 180
                                    self.shake_intensity = 30
                                    
                                    self.carrying_item = False
                                    interacted_with_obj = True
                                    self.make_noise(self.player.rect.centerx, self.player.rect.centery, 0, True)
                                    break
                                
                        if not interacted_with_obj and self.state == "PLAYING":
                            if self.player.has_candle:
                                self.player.has_candle = False
                                if self.sfx_grab: self.sfx_grab.play()
                                self.interactables.append(Candle(self.player.rect.x, self.player.rect.y))
                            else:
                                for item in self.interactables:
                                    if isinstance(item, Candle) and item.active and self.player.rect.colliderect(item.rect):
                                        self.player.has_candle = True
                                        item.active = False
                                        if self.sfx_grab: self.sfx_grab.play()
                                        break 
                                        
        if self.state == "MENU" and mouse_pressed[0]:
            if self.vol_rect.collidepoint(mouse_pos):
                self.global_volume = (mouse_pos[0] - self.vol_rect.x) / self.vol_rect.width
                self.global_volume = max(0.0, min(1.0, self.global_volume))
                self._update_volume()

    def buy_shop_upgrade(self):
        stats = self.player_stats
        if self.shop_selected_index == 0: 
            speed_costs = {0: 90, 1: 140, 2: 190, 3: 250}
            speed_values = {1: 2.5, 2: 3.0, 3: 3.5, 4: 4.0}
            if stats.speed_level < 4:
                cost = speed_costs[stats.speed_level]
                if stats.coins >= cost:
                    stats.coins -= cost
                    stats.speed_level += 1
                    stats.speed = speed_values[stats.speed_level]

        elif self.shop_selected_index == 1: 
            if not stats.candle_upgraded and stats.coins >= 110:
                stats.coins -= 110
                stats.candle_upgraded = True
                stats.vision_radius = 7.2

        elif self.shop_selected_index == 2: 
            if not stats.muffler_upgraded and stats.coins >= 120:
                stats.coins -= 120
                stats.muffler_upgraded = True
                stats.noise_radius = 8.0

        elif self.shop_selected_index == 3: 
            if not stats.stealth_upgraded and stats.coins >= 150:
                stats.coins -= 150
                stats.stealth_upgraded = True
                stats.smell_modifier = 0.8

    def update(self):
        keys = pygame.key.get_pressed()
        
        if self.state == "PLAYING":
            self.player.move(keys, self.walls, self)
            self.camera.update(self.player)

            holding_e = keys[pygame.K_e]
            button_found_this_frame = False
            
            for item in self.interactables:
                if isinstance(item, Dot) and item.active and self.player.rect.colliderect(item.rect):
                    item.interact(self.player, self)
                elif isinstance(item, SpecialItem) and item.active and self.player.rect.colliderect(item.rect):
                    item.interact(self.player, self)
                elif isinstance(item, ButtonInteract) and item.active and self.player.rect.colliderect(item.rect):
                    button_found_this_frame = True
                    if holding_e:
                        item.hold_progress += 1
                        if item.hold_progress >= item.required_frames:
                            item.active = False
                            self.buttons_pressed += 1
                            if self.sfx_button: self.sfx_button.play()
                            self.make_noise(item.rect.centerx, item.rect.centery, 0, is_loud=True)
                    else:
                        item.hold_progress = 0 

            if not button_found_this_frame or not holding_e:
                for item in self.interactables:
                    if isinstance(item, ButtonInteract) and item.active:
                        item.hold_progress = 0

            self.interactables = [i for i in self.interactables if i.active]
            
            for boss in self.bosses:
                if self.current_level == 5:
                    boss.update_skills_m5(self.m5_hear, self.m5_see, self.m5_smell)
                
                boss.update(self.player, self.walls, self.map_w, self.map_h, self)
                if self.player.rect.colliderect(boss.rect):
                    self.state = "JUMPSCARE"

            for i, boss in enumerate(self.bosses):
                for j in range(i + 1, len(self.bosses)):
                    boss.resolve_overlap(self.bosses[j])

            any_chase = any(b.state == "CHASE" for b in self.bosses)
            target_bgm = "chase.wav" if any_chase else "ambience.wav"
            
            if self.current_bgm != target_bgm:
                if self.current_bgm is None:
                    self.current_bgm = target_bgm
                    self.bgm_fading = False
                    try:
                        pygame.mixer.music.load(self.current_bgm)
                        pygame.mixer.music.play(-1)
                        pygame.mixer.music.set_volume(self.global_volume * 0.38)
                    except: pass
                elif target_bgm == "ambience.wav":
                    if not self.bgm_fading:
                        pygame.mixer.music.fadeout(2000) 
                        self.bgm_fading = True
                        self.fade_timer = pygame.time.get_ticks()
                    elif pygame.time.get_ticks() - self.fade_timer > 2000:
                        self.current_bgm = target_bgm
                        self.bgm_fading = False
                        try:
                            pygame.mixer.music.load(self.current_bgm)
                            pygame.mixer.music.play(-1)
                            pygame.mixer.music.set_volume(self.global_volume * 0.38)
                        except: pass
                else:
                    self.current_bgm = target_bgm
                    self.bgm_fading = False
                    try:
                        pygame.mixer.music.load(self.current_bgm)
                        pygame.mixer.music.play(-1)
                        pygame.mixer.music.set_volume(self.global_volume * 0.38)
                    except: pass

            self.player.is_hidden = True
            if self.player.has_candle:
                self.player.is_hidden = False
            else:
                for item in self.interactables:
                    if isinstance(item, Candle) and item.active:
                        d = math.hypot(self.player.rect.centerx - item.rect.centerx, self.player.rect.centery - item.rect.centery)
                        if d <= int(self.player.stats.vision_radius * TILE):
                            self.player.is_hidden = False
                            break

            if self.current_level == 5 and self.center_room_rect.colliderect(self.player.rect):
                self.player.is_hidden = False

            if self.current_level < 5:
                if not self.door_spawned and self.levers_pulled >= self.target_levers and self.buttons_pressed >= self.target_buttons:
                    corners = [(TILE, TILE), (self.map_w - TILE * 3, TILE), 
                               (TILE, self.map_h - TILE * 3), (self.map_w - TILE * 3, self.map_h - TILE * 3)]
                    cx, cy = random.choice(corners)
                    self.interactables.append(GreenDoor(cx, cy))
                    self.door_spawned = True
            else:
                if self.m5_items_placed == 4 and not self.m5_doors_closed:
                    self.m5_doors_closed = True
                    rx = self.center_room_rect.x
                    ry = self.center_room_rect.y
                    rw = self.center_room_rect.w
                    rh = self.center_room_rect.h
                    gate_size = TILE * 3
                    self.walls.append(pygame.Rect(rx + (rw - gate_size) // 2, ry, gate_size, TILE))
                    self.walls.append(pygame.Rect(rx + (rw - gate_size) // 2, ry + rh - TILE, gate_size, TILE))
                    self.walls.append(pygame.Rect(rx, ry + (rh - gate_size) // 2, TILE, gate_size))
                    self.walls.append(pygame.Rect(rx + rw - TILE, ry + (rh - gate_size) // 2, TILE, gate_size))
                    
                    for boss in self.bosses:
                        boss.is_large = True
                        
                if self.m5_items_placed == 4:
                    self.m5_survival_timer -= 1
                    if self.m5_survival_timer <= 0:
                        self.state = "VICTORY_SCREEN"

        elif self.state == "HALLWAY":
            self.player.move(keys, self.hall_walls, self)
            self.camera.update(self.player)
            for item in self.hall_items:
                if isinstance(item, GreenDoor) and self.player.rect.colliderect(item.rect):
                    self.current_level += 1
                    self.reset_game(next_level=True)
                    break

    def render_lighting(self):
        self.fog.fill(BLACK)
        self.fog.set_colorkey(MAGENTA)

        if self.current_level == 5:
            pygame.draw.rect(self.fog, MAGENTA, self.camera.apply_rect(self.center_room_rect))

        for item in self.interactables:
            rect = self.camera.apply(item)
            if isinstance(item, Dot) and item.active:
                pygame.draw.circle(self.fog, MAGENTA, rect.center, 4) 
            elif isinstance(item, Candle) and item.active:
                pygame.draw.circle(self.fog, MAGENTA, rect.center, int(self.player.stats.vision_radius * TILE))
            elif isinstance(item, Note) and item.active:
                pygame.draw.circle(self.fog, MAGENTA, rect.center, int(2.5 * TILE))
            elif isinstance(item, SpecialItem) and item.active:
                pygame.draw.circle(self.fog, MAGENTA, rect.center, int(3 * TILE))

        player_rect = self.camera.apply(self.player)
        
        if self.player.has_candle:
            pygame.draw.circle(self.fog, MAGENTA, player_rect.center, self.player.get_candle_radius())
        else:
            pygame.draw.circle(self.fog, MAGENTA, player_rect.center, self.player.rect.width // 2)

        for boss in self.bosses:
            boss_rect = self.camera.apply(boss)
            pygame.draw.circle(self.fog, MAGENTA, boss_rect.center, TILE)
            
        for item in getattr(self, 'hall_items', []):
            if isinstance(item, UnpickableCandle):
                rect = self.camera.apply(item)
                pygame.draw.circle(self.fog, MAGENTA, rect.center, int(6.0 * TILE))

        self.game_surface.blit(self.fog, (0, 0))

    def draw_hud(self):
        if self.player.has_note:
            if self.current_level < 5:
                mission_str = f"Levers: {self.levers_pulled}/{self.target_levers}"
                if self.target_buttons > 0:
                    mission_str += f" | Buttons: {self.buttons_pressed}/{self.target_buttons}"
            else:
                mission_str = f"Artifacts Placed: {self.m5_items_placed}/4"
                if self.m5_items_placed == 4:
                    mission_str += f" | SURVIVE: {max(0, self.m5_survival_timer // FPS)}s"

            text = self.font.render(f"LV: {self.current_level} | {mission_str} | Coins: {self.player_stats.coins}", True, WHITE)
            
            skills = []
            if self.current_level == 5:
                skills.append("MOVE")
                skills.append("DIE")
                if self.m5_hear: skills.append("HEAR")
                if self.m5_see: skills.append("SEE")
                if self.m5_smell: skills.append("SMELL")
                if self.m5_items_placed >= 4:
                    skills.append("DUPLICATE")
                    skills.append("LARGE")
            else:
                skills.append("MOVE")
                if self.current_level >= 2: skills.append("HEAR")
                if self.current_level >= 3: skills.append("SEE")
                if self.current_level >= 4: skills.append("SMELL")
                
            skill_text = self.font.render(f"Ghost abilities: {', '.join(skills)}", True, RED)
            
            self.screen.blit(text, (20, 20))
            self.screen.blit(skill_text, (20, 50))
            
            if self.current_level == 5 and self.carrying_item:
                carried_txt = self.font.render("Carrying Artifact - Go to Center Room!", True, MAGENTA)
                self.screen.blit(carried_txt, (20, 80))
        
        spk_x, spk_y = SCREEN_WIDTH - 50, 20
        self.screen.blit(self.speaker_img, (spk_x, spk_y))
        if self.speaker_flash_timer > 0:
            flash_color = RED if self.speaker_flash_loud else GRAY
            pygame.draw.rect(self.screen, flash_color, (spk_x-2, spk_y-2, 31+4, 24+4), 2)
            self.speaker_flash_timer -= 1
            
        eye_x, eye_y = spk_x - 70, 20
        self.screen.blit(self.eye_img, (eye_x, eye_y))
        if not self.player.is_hidden:
            pygame.draw.rect(self.screen, (255, 0, 0), (eye_x-2, eye_y-2, 51+4, 24+4), 2)

    def draw_shop_ui(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((15, 15, 20))
        self.screen.blit(overlay, (0, 0))
        
        stats = self.player_stats
        title = self.title_font.render("=== MAZE SHOP ===", True, YELLOW)
        coin_txt = self.font.render(f"Your Balance: {stats.coins} Coins", True, WHITE)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 80))
        self.screen.blit(coin_txt, (SCREEN_WIDTH//2 - coin_txt.get_width()//2, 140))

        speed_costs = {0: "90 coins", 1: "140 coins", 2: "190 coins", 3: "250 coins", 4: "MAX"}
        cost_sp = speed_costs[stats.speed_level]
        
        upgrades = [
            (f"Movement Speed (Level {stats.speed_level}/4)", f"Price: {cost_sp}", stats.speed_level < 4),
            ("Candle Vision (+20%)", "Price: 110 coins" if not stats.candle_upgraded else "PURCHASED", not stats.candle_upgraded),
            ("Dot Eating Noise Reduction (-20%)", "Price: 120 coins" if not stats.muffler_upgraded else "PURCHASED", not stats.muffler_upgraded),
            ("Anti-smell Stealth (-20%)", "Price: 150 coins" if not stats.stealth_upgraded else "PURCHASED", not stats.stealth_upgraded)
        ]

        start_y = 240
        for i, (name, cost_str, available) in enumerate(upgrades):
            color = WHITE if i == self.shop_selected_index else DARK_GRAY
            if not available: color = (100, 100, 100)
            
            if i == self.shop_selected_index:
                tri_size = 8
                tri_x = 130
                tri_y = start_y + i * 60 + 10
                pygame.draw.polygon(self.screen, WHITE, [
                    (tri_x, tri_y - tri_size),
                    (tri_x + tri_size, tri_y),
                    (tri_x, tri_y + tri_size)
                ])
                item_txt = self.font.render(name, True, WHITE)
            else:
                item_txt = self.font.render(name, True, color)
                
            val_txt = self.font.render(cost_str, True, YELLOW if available else color)
            
            self.screen.blit(item_txt, (150, start_y + i * 60))
            self.screen.blit(val_txt, (700, start_y + i * 60))

        guide_txt = self.font.render("[UP/DOWN] Select | [ENTER] Buy | [ESC] Exit Shop", True, WHITE)
        self.screen.blit(guide_txt, (SCREEN_WIDTH//2 - guide_txt.get_width()//2, SCREEN_HEIGHT - 120))

    def run(self):
        while True:
            self.handle_events()
            
            sx, sy = 0, 0
            if self.state == "PLAYING":
                min_dist = 9999
                for b in self.bosses:
                    d = math.hypot(b.rect.centerx - self.player.rect.centerx, b.rect.centery - self.player.rect.centery)
                    min_dist = min(min_dist, d)
                
                trigger_dist = SCREEN_WIDTH // 2
                prox_shake = 0
                if min_dist < trigger_dist:
                    prox_shake = (trigger_dist - min_dist) / trigger_dist * 8
                    
                total_shake = int(self.shake_intensity + prox_shake)
                if total_shake > 0:
                    sx = random.randint(-total_shake, total_shake)
                    sy = random.randint(-total_shake, total_shake)
                    
                if self.shake_intensity > 0:
                    self.shake_intensity -= 1
            
            if self.state == "MENU":
                self.screen.fill((10, 10, 10))
                title = self.title_font.render("Pac-man The Labyrinth", True, RED)
                self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 200))
                
                pygame.draw.rect(self.screen, DARK_GRAY, self.btn_labyrinth)
                pygame.draw.rect(self.screen, DARK_GRAY, self.btn_classic)
                
                lab_txt = self.font.render("Labyrinth Mode", True, WHITE)
                cls_txt = self.font.render("Classic Mode", True, WHITE)
                
                self.screen.blit(lab_txt, (self.btn_labyrinth.centerx - lab_txt.get_width()//2, self.btn_labyrinth.centery - lab_txt.get_height()//2))
                self.screen.blit(cls_txt, (self.btn_classic.centerx - cls_txt.get_width()//2, self.btn_classic.centery - cls_txt.get_height()//2))
                
                vol_label = self.font.render("Volume:", True, WHITE)
                self.screen.blit(vol_label, (self.vol_rect.x - 100, self.vol_rect.y))
                pygame.draw.rect(self.screen, GRAY, self.vol_rect)
                pygame.draw.rect(self.screen, GREEN, (self.vol_rect.x, self.vol_rect.y, int(self.vol_rect.width * self.global_volume), self.vol_rect.height))
                
            elif self.state == "LEVEL_INTRO":
                self.screen.fill(BLACK)
                level_text = self.title_font.render(f"Level {self.current_level} / 5", True, WHITE)
                self.screen.blit(level_text, (SCREEN_WIDTH//2 - level_text.get_width()//2, 200))
                
                ability_list = [("MOVE", True)]
                if self.current_level == 5:
                    ability_list.append(("DIE", True))
                else:
                    ability_list.append(("HEAR", self.current_level >= 2))
                    ability_list.append(("SEE", self.current_level >= 3))
                    ability_list.append(("SMELL", self.current_level >= 4))
                
                start_y = 300
                spacing = 50
                for i, (ab_name, unlocked) in enumerate(ability_list):
                    if unlocked:
                        prefix_txt = self.title_font.render("Ghost can ", True, WHITE)
                        ab_txt = self.title_font.render(ab_name, True, RED)
                        
                        total_w = prefix_txt.get_width() + ab_txt.get_width()
                        x_base = SCREEN_WIDTH // 2 - total_w // 2
                        y_pos = start_y + i * spacing
                        
                        tri_size = 12
                        tri_x = x_base - 40
                        tri_y = y_pos + prefix_txt.get_height() // 2
                        pygame.draw.polygon(self.screen, WHITE, [
                            (tri_x, tri_y - tri_size),
                            (tri_x + tri_size, tri_y),
                            (tri_x, tri_y + tri_size)
                        ])
                        
                        self.screen.blit(prefix_txt, (x_base, y_pos))
                        self.screen.blit(ab_txt, (x_base + prefix_txt.get_width(), y_pos))
                        
                prompt = self.font.render("Press SPACE to Start", True, DARK_GRAY)
                self.screen.blit(prompt, (SCREEN_WIDTH//2 - prompt.get_width()//2, SCREEN_HEIGHT - 100))

            elif self.state == "PLAYING":
                self.update()
                self.game_surface.fill((15, 15, 15))
                
                if self.current_level == 5:
                    pygame.draw.rect(self.game_surface, (25, 20, 20), self.camera.apply_rect(self.center_room_rect))
                    self.altar_obj.draw(self.game_surface, self.camera)
                
                for w in self.walls:
                    pygame.draw.rect(self.game_surface, DARK_GRAY, self.camera.apply_rect(w))

                for item in self.interactables:
                    item.draw(self.game_surface, self.camera)
                    
                self.player.draw(self.game_surface, self.camera)
                for boss in self.bosses:
                    boss.draw(self.game_surface, self.camera)

                self.render_lighting()
                scaled_surface = pygame.transform.scale(self.game_surface, (SCREEN_WIDTH, SCREEN_HEIGHT))
                self.screen.blit(scaled_surface, (sx, sy)) 
                self.draw_hud()
                
                if self.buff_popup_timer > 0:
                    popup_surf = self.small_title_font.render(self.buff_popup_text, True, YELLOW)
                    self.screen.blit(popup_surf, (SCREEN_WIDTH // 2 - popup_surf.get_width() // 2, 80))
                    self.buff_popup_timer -= 1

            elif self.state == "DOOR_PROMPT":
                self.screen.fill((15, 5, 5))
                box_rect = pygame.Rect(162, 234, 700, 300)
                pygame.draw.rect(self.screen, DARK_GRAY, box_rect)
                pygame.draw.rect(self.screen, GREEN, box_rect, 4)
                
                prompt_t1 = self.font.render("PROCEED TO THE NEXT LEVEL?", True, WHITE)
                prompt_t2 = self.font.render("[Y] Proceed         [N] Stay", True, YELLOW)
                warn_t = self.font.render("Note: Uncollected dots disappear!", True, RED)
                
                self.screen.blit(prompt_t1, (SCREEN_WIDTH//2 - prompt_t1.get_width()//2, 280))
                self.screen.blit(prompt_t2, (SCREEN_WIDTH//2 - prompt_t2.get_width()//2, 360))
                self.screen.blit(warn_t, (SCREEN_WIDTH//2 - warn_t.get_width()//2, 440))

            elif self.state == "HALLWAY":
                self.update()
                self.game_surface.fill((15, 15, 15)) 
                
                for w in self.hall_walls:
                    pygame.draw.rect(self.game_surface, DARK_GRAY, self.camera.apply_rect(w))
                for item in self.hall_items:
                    item.draw(self.game_surface, self.camera)
                
                self.player.draw(self.game_surface, self.camera)
                self.render_lighting() 
                
                scaled_surface = pygame.transform.scale(self.game_surface, (SCREEN_WIDTH, SCREEN_HEIGHT))
                self.screen.blit(scaled_surface, (0, 0))
                
                txt = self.font.render("SAFE HALLWAY - Enter wooden door for SHOP", True, GREEN)
                coin_txt = self.font.render(f"Coins: {self.player_stats.coins}", True, YELLOW)
                self.screen.blit(txt, (SCREEN_WIDTH//2 - txt.get_width()//2, 30))
                self.screen.blit(coin_txt, (20, 30))

            elif self.state == "SHOP":
                self.draw_shop_ui()

            elif self.state == "JUMPSCARE":
                self.screen.fill(RED)
                js_text = self.title_font.render("YOU GOT CAUGHT!", True, BLACK)
                prompt = self.font.render("Press SPACE to Respawn | ESC to Menu", True, BLACK)
                self.screen.blit(js_text, (SCREEN_WIDTH//2 - js_text.get_width()//2, SCREEN_HEIGHT//2 - 50))
                self.screen.blit(prompt, (SCREEN_WIDTH//2 - prompt.get_width()//2, SCREEN_HEIGHT//2 + 20))

            elif self.state == "VICTORY_SCREEN":
                self.screen.fill((20, 40, 20))
                v_text = self.title_font.render("VICTORY! ESCAPED", True, YELLOW)
                prompt = self.font.render("SPACE/ESC to Main Menu", True, WHITE)
                self.screen.blit(v_text, (SCREEN_WIDTH//2 - v_text.get_width()//2, SCREEN_HEIGHT//2 - 50))
                self.screen.blit(prompt, (SCREEN_WIDTH//2 - prompt.get_width()//2, SCREEN_HEIGHT//2 + 20))

            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = GameEngine()
    game.run()