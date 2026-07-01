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

# ================= TILEMAP TEXTURE CACHE =================
def load_sprite_scaled(name, scale=TILE):
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

# ================= MAP DEFINITIONS (Drunkard's Walk) =================
MIN_HALL = 3

def build_level_walls(level: int, map_w: int, map_h: int) -> tuple:
    walls = []
    cols = map_w // TILE
    rows = map_h // TILE
    center_room_rect = None

    CHUNK = MIN_HALL
    chunk_cols = cols // CHUNK
    chunk_rows = rows // CHUNK

    grid = [[True for _ in range(chunk_rows)] for _ in range(chunk_cols)]

    target_floor_chunks = int(chunk_cols * chunk_rows * (0.35 + level * 0.04))
    floor_count = 0

    cx, cy = chunk_cols // 2, chunk_rows // 2
    grid[cx][cy] = False
    floor_count += 1

    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    while floor_count < target_floor_chunks:
        dx, dy = random.choice(directions)
        step_len = random.randint(1, 4)
        
        for _ in range(step_len):
            nx, ny = cx + dx, cy + dy
            if 1 <= nx < chunk_cols - 1 and 1 <= ny < chunk_rows - 1:
                cx, cy = nx, ny
                if grid[cx][cy]:
                    grid[cx][cy] = False
                    floor_count += 1
            else:
                break

    for y in range(chunk_rows):
        start_x = -1
        for x in range(chunk_cols):
            if grid[x][y]:
                if start_x == -1:
                    start_x = x
            else:
                if start_x != -1:
                    px = start_x * CHUNK * TILE
                    py = y * CHUNK * TILE
                    pw = (x - start_x) * CHUNK * TILE
                    ph = CHUNK * TILE
                    walls.append(pygame.Rect(px, py, pw, ph))
                    start_x = -1
        
        if start_x != -1:
            px = start_x * CHUNK * TILE
            py = y * CHUNK * TILE
            pw = (chunk_cols - start_x) * CHUNK * TILE
            ph = CHUNK * TILE
            walls.append(pygame.Rect(px, py, pw, ph))

    walls.append(pygame.Rect(0, 0, map_w, TILE*3))
    walls.append(pygame.Rect(0, map_h-TILE*3, map_w, TILE*3))
    walls.append(pygame.Rect(0, 0, TILE*3, map_h))
    walls.append(pygame.Rect(map_w-TILE*3, 0, TILE*3, map_h))

    if level == 5:
        rw = int(map_w * 0.30)
        rh = int(map_h * 0.30)
        rx = (map_w - rw) // 2
        ry = (map_h - rh) // 2
        center_room_rect = pygame.Rect(rx, ry, rw, rh)

        # Tránh block cửa phòng giữa bằng cách clear tường ngẫu nhiên trong phạm vi rộng hơn phòng
        clearance_rect = center_room_rect.inflate(TILE*6, TILE*6)
        walls = [w for w in walls if not w.colliderect(clearance_rect)]

        gate = TILE * 3
        walls.append(pygame.Rect(rx, ry, (rw - gate) // 2, TILE*2))
        walls.append(pygame.Rect(rx + (rw + gate) // 2, ry, (rw - gate) // 2, TILE*2))
        walls.append(pygame.Rect(rx, ry+rh-TILE*2, (rw - gate) // 2, TILE*2))
        walls.append(pygame.Rect(rx + (rw + gate) // 2, ry+rh-TILE*2, (rw - gate) // 2, TILE*2))
        walls.append(pygame.Rect(rx, ry, TILE*2, (rh - gate) // 2))
        walls.append(pygame.Rect(rx, ry + (rh + gate) // 2, TILE*2, (rh - gate) // 2))
        walls.append(pygame.Rect(rx+rw-TILE*2, ry, TILE*2, (rh - gate) // 2))
        walls.append(pygame.Rect(rx+rw-TILE*2, ry + (rh + gate) // 2, TILE*2, (rh - gate) // 2))

    walls = [w for w in walls
             if w.right <= map_w and w.bottom <= map_h
             and w.x >= 0 and w.y >= 0
             and w.width > 0 and w.height > 0]

    return walls, center_room_rect

# ================= HÀM HỖ TRỢ =================
def load_font(name, size):
    for f in [name, name.lower(), "assets/04B_03__.TTF", "assets/04b_03.ttf"]:
        try: return pygame.font.Font(f, size)
        except: pass
    return pygame.font.SysFont("Courier New", size, bold=True)

def load_img(name, scale):
    try: return pygame.transform.scale(pygame.image.load(name).convert_alpha(), scale)
    except:
        s = pygame.Surface(scale, pygame.SRCALPHA); s.fill(MAGENTA); return s

def load_sound(name):
    try: return pygame.mixer.Sound(name)
    except: return None

# ================= PLAYER STATS =================
class PlayerStats:
    def __init__(self):
        self.coins          = 0
        self.speed_level    = 0
        self.speed          = 2.3
        self.candle_upgraded= False
        self.vision_radius  = 6.0
        self.muffler_upgraded = False
        self.noise_radius   = 10.0
        self.stealth_upgraded = False
        self.smell_modifier = 1.0

# ================= CAMERA =================
class Camera:
    def __init__(self, map_width, map_height):
        self.map_width  = map_width
        self.map_height = map_height
        self.cam_x = 0.0
        self.cam_y = 0.0
        self.camera = pygame.Rect(0, 0, map_width, map_height)

    def snap(self, target):
        self.cam_x = -target.rect.centerx + GAME_WIDTH  // 2
        self.cam_y = -target.rect.centery + GAME_HEIGHT // 2
        self.update_rect()

    def apply(self, entity):   return entity.rect.move(self.camera.topleft)
    def apply_rect(self, r):   return r.move(self.camera.topleft)

    def update(self, target):
        tx = -target.rect.centerx + GAME_WIDTH  // 2
        ty = -target.rect.centery + GAME_HEIGHT // 2
        self.cam_x += (tx - self.cam_x) * 0.06
        self.cam_y += (ty - self.cam_y) * 0.06
        self.update_rect()

    def update_rect(self):
        x = min(0, max(-(self.map_width  - GAME_WIDTH),  self.cam_x))
        y = min(0, max(-(self.map_height - GAME_HEIGHT), self.cam_y))
        self.camera = pygame.Rect(int(x), int(y), self.map_width, self.map_height)

# ================= OOP BASE =================
class GameObject(ABC):
    def __init__(self, x, y, w, h, color):
        self.rect   = pygame.Rect(x, y, w, h)
        self.color  = color
        self.active = True

    @abstractmethod
    def draw(self, surface, camera): pass

class Interactable(GameObject):
    @abstractmethod
    def interact(self, player, game_state): pass

class Entity(GameObject):
    def __init__(self, x, y, w, h, color, speed=0.0):
        super().__init__(x, y, w, h, color)
        self.x, self.y = float(x), float(y)
        self.speed = self.current_speed = speed

    def move_and_collide(self, dx, dy, walls, ignore_walls=False):
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

# ================= VẬT PHẨM =================
class Dot(Interactable):
    def __init__(self, x, y):
        super().__init__(x+12, y+12, 8, 8, YELLOW)
        self._pulse = random.uniform(0, math.pi*2)

    def draw(self, surface, camera):
        if not self.active: return
        self._pulse += 0.08
        r = camera.apply(self)
        glow = pygame.Surface((24,24), pygame.SRCALPHA)
        alpha = int(60 + 40 * math.sin(self._pulse))
        pygame.draw.circle(glow, (*YELLOW, alpha), (12,12), 10)
        surface.blit(glow, (r.centerx-12, r.centery-12))
        pygame.draw.rect(surface, YELLOW, r)

    def interact(self, player, gs):
        if self.active:
            player.stats.coins += 10
            self.active = False
            gs.make_noise(self.rect.centerx, self.rect.centery,
                          radius=player.stats.noise_radius*TILE, is_loud=False)

class Lever(Interactable):
    def __init__(self, x, y):
        super().__init__(x, y, TILE, TILE, DARK_GRAY)
        self.pulled = False

    def draw(self, surface, camera):
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
        if not self.pulled:
            self.pulled = True
            gs.levers_pulled += 1
            if gs.sfx_lever: gs.sfx_lever.play()
            gs.make_noise(self.rect.centerx, self.rect.centery, radius=0, is_loud=True)

class ButtonInteract(Interactable):
    def __init__(self, x, y):
        super().__init__(x+4, y+4, TILE-8, TILE-8, BLUE)
        self.hold_progress  = 0
        self.required_frames = 120

    def draw(self, surface, camera):
        if not self.active: return
        r = camera.apply(self)
        pygame.draw.rect(surface, (40,40,60), r)
        pct = self.hold_progress / self.required_frames
        h   = int((r.height-4)*pct)
        pygame.draw.rect(surface, (80,120,220),
                         (r.x+2, r.bottom-2-h, r.width-4, h))
        pygame.draw.rect(surface, (100,140,255), r, 1)

    def interact(self, player, gs): pass

class Note(Interactable):
    def __init__(self, x, y):
        super().__init__(x+8, y+8, 16, 16, WHITE)

    def draw(self, surface, camera):
        if not self.active: return
        r = camera.apply(self)
        pygame.draw.rect(surface, (230,225,210), r)
        pygame.draw.rect(surface, (180,170,150), r, 1)
        for ly in [r.y+4, r.y+8, r.y+12]:
            pygame.draw.line(surface, (80,70,60), (r.x+3, ly), (r.x+13, ly), 1)

    def interact(self, player, gs):
        if self.active:
            player.has_note = True
            self.active = False

class Candle(Interactable):
    def __init__(self, x, y):
        super().__init__(x+8, y+8, 16, 16, ORANGE)
        self._flicker = random.uniform(0, math.pi*2)

    def draw(self, surface, camera):
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

    def interact(self, player, gs): pass

class UnpickableCandle(GameObject):
    def __init__(self, x, y):
        super().__init__(x+8, y+8, 16, 16, ORANGE)
        self._flicker = random.uniform(0, math.pi*2)

    def draw(self, surface, camera):
        self._flicker += 0.10
        r = camera.apply(self)
        pygame.draw.rect(surface, (220,200,170), (r.x+4, r.y+4, 8, 10))
        pygame.draw.rect(surface, (180,160,130), (r.x+4, r.y+4, 8, 10), 1)
        pygame.draw.line(surface, (80,60,40), (r.centerx, r.y+4),(r.centerx, r.y+2), 1)
        flicker_x = int(math.sin(self._flicker)*2)
        fx = r.centerx + flicker_x; fy = r.y - 2
        pygame.draw.ellipse(surface, (255,200,50), (fx-3, fy-6, 6, 8))
        pygame.draw.ellipse(surface, (255,240,120),(fx-2, fy-4, 4, 5))

class SpecialItem(Interactable):
    def __init__(self, x, y):
        super().__init__(x+4, y+4, 24, 24, MAGENTA)
        self._bob = random.uniform(0, math.pi*2)

    def draw(self, surface, camera):
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
        if self.active and not gs.carrying_item:
            gs.carrying_item = True
            self.active = False

class Altar(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y, TILE*2, TILE*2, WHITE)

    def draw(self, surface, camera):
        r = camera.apply(self)
        pygame.draw.rect(surface, (80,72,60), r)
        pygame.draw.rect(surface, (120,108,90), r, 2)
        font = load_font("assets/04b_03.ttf", 12)
        t = font.render("ALTAR", True, (200,190,170))
        surface.blit(t, (r.centerx-t.get_width()//2, r.centery-t.get_height()//2))

class GreenDoor(Interactable):
    def __init__(self, x, y):
        super().__init__(x, y, TILE*2, TILE*2, GREEN)
        self.locked = True

    def draw(self, surface, camera):
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
        if self.locked:
            gs.buff_popup_text = ["LOCKED! Complete objectives!"]
            gs.buff_popup_timer = 120
            gs.shake_intensity = 5
            return
        gs.state = "DOOR_PROMPT"

class WoodenDoor(Interactable):
    def __init__(self, x, y):
        super().__init__(x, y, TILE*2, TILE*2, BROWN)

    def draw(self, surface, camera):
        r = camera.apply(self)
        pygame.draw.rect(surface, (100,60,20), r)
        pygame.draw.rect(surface, (140,90,40), r, 2)
        pygame.draw.line(surface, (60,35,10), (r.centerx, r.y+2),(r.centerx, r.bottom-2), 2)
        pygame.draw.circle(surface, YELLOW, (r.centerx-8, r.centery), 4)

    def interact(self, player, gs):
        gs.state = "SHOP"

# ================= PLAYER =================
class Player(Entity):
    def __init__(self, x, y, stats):
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
        return int(self.stats.vision_radius * TILE)

    def draw(self, surface, camera):
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

# ================= STALKER BOSS =================
class StalkerBoss(Entity):
    def __init__(self, x, y, level):
        super().__init__(x, y, TILE, TILE, BOSS_RED, 3.5)
        self.level = level
        self.state = "ROAM"
        self.target_pos   = None

        self.can_phase              = True
        self.can_hear               = level >= 2
        self.can_see                = level >= 3
        self.can_see_through_walls  = level >= 3
        self.can_smell              = level >= 4

        self.smell_timer  = 0
        self.dir_x = self.dir_y = 0
        self.is_large     = False
        self.grabbing     = False
        
        self.step_phase = "PAUSE"
        self.step_timer = 0
        self.anim_time  = 0.0

    def update_skills_m5(self, hear, see, smell):
        self.can_hear              = hear
        self.can_see               = see
        self.can_see_through_walls = see
        self.can_smell             = smell

    def update(self, player, walls, map_w, map_h, gs):
        if self.state == "CHASE":
            if player.is_hidden or not self.check_los(player, walls):
                self.state = "INVESTIGATE"
            else:
                self.target_pos = player.rect.center
        
        if self.state != "CHASE":
            if self.can_see and not player.is_hidden:
                d = math.hypot(player.rect.centerx-self.rect.centerx,
                               player.rect.centery-self.rect.centery)
                if d <= 8*TILE and self.check_los(player, walls):
                    self.state = "CHASE"
                    self.target_pos = player.rect.center

            if self.can_smell and self.state != "CHASE":
                d = math.hypot(player.rect.centerx-self.rect.centerx,
                               player.rect.centery-self.rect.centery)
                if d <= 3.5*TILE*player.stats.smell_modifier:
                    self.state = "SMELL_SEARCH"
                    self.target_pos = player.rect.center
                    self.smell_timer = 120

        if self.state == "ROAM":
            if not self.target_pos or random.random() < 0.02:
                nx = max(TILE*3, min(map_w-TILE*4, self.rect.centerx+random.randint(-400,400)))
                ny = max(TILE*3, min(map_h-TILE*4, self.rect.centery+random.randint(-400,400)))
                self.target_pos = (nx, ny)

        elif self.state == "INVESTIGATE":
            if self.target_pos:
                if math.hypot(self.target_pos[0]-self.rect.centerx,
                              self.target_pos[1]-self.rect.centery) < 15:
                    self.state = "ROAM"; self.target_pos = None

        elif self.state == "SMELL_SEARCH":
            self.smell_timer -= 1
            if self.smell_timer <= 0:
                self.state = "ROAM"; self.target_pos = None

        elif self.state == "CHASE":
            if self.can_see_through_walls:
                self.target_pos = player.rect.center

        if self.target_pos:
            self._move_to(walls, ignore=True, gs=gs)

        self.x = max(TILE * 3.0, min(float(map_w - TILE * 4.0), self.x))
        self.y = max(TILE * 3.0, min(float(map_h - TILE * 4.0), self.y))
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

    def check_los(self, player, walls):
        if self.can_see_through_walls:
            return True
        s, e = self.rect.center, player.rect.center
        d = math.hypot(e[0]-s[0], e[1]-s[1])
        if d == 0: return True
        for i in range(1, int(d/8)):
            t = i/(int(d/8))
            p = pygame.Rect(int(s[0]+(e[0]-s[0])*t)-2,
                            int(s[1]+(e[1]-s[1])*t)-2, 4, 4)
            for w in walls:
                if p.colliderect(w): return False
        return True

    def hear_noise(self, x, y, radius, noise_mod):
        if self.can_hear and self.state != "CHASE":
            if math.hypot(x-self.rect.centerx, y-self.rect.centery) <= radius*noise_mod:
                self.state = "INVESTIGATE"
                self.target_pos = (x, y)

    def _move_to(self, walls, ignore, gs):
        tx, ty = self.target_pos
        dx, dy = tx-self.rect.centerx, ty-self.rect.centery
        d = math.hypot(dx, dy)
        
        if self.state == "CHASE":
            move_frames = 10
            pause_frames = 10
            speed_mult = 2.2
        elif self.state == "INVESTIGATE":
            move_frames = 12
            pause_frames = 18
            speed_mult = 1.8
        else:
            move_frames = 15
            pause_frames = 35
            speed_mult = 1.4

        self.step_timer -= 1
        if self.step_timer <= 0:
            if self.step_phase == "PAUSE":
                self.step_phase = "MOVE"
                self.step_timer = move_frames
                if gs.sfx_stomp:
                    pd = math.hypot(self.rect.centerx-gs.player.rect.centerx,
                                    self.rect.centery-gs.player.rect.centery)
                    vol = max(0.0, 1.0 - pd/(SCREEN_WIDTH*0.9))
                    # Stomp base vol 0.5 * Overall 0.8 * Stomp giảm thêm 30% (0.7) = 0.28
                    gs.sfx_stomp.set_volume(vol * 0.28 * gs.global_volume)
                    gs.sfx_stomp.play()
            else:
                self.step_phase = "PAUSE"
                self.step_timer = pause_frames

        if self.step_phase == "MOVE" and d > 0:
            actual_speed = self.speed * speed_mult
            if d > actual_speed:
                nx = dx/d*actual_speed
                ny = dy/d*actual_speed
            else:
                nx, ny = dx, dy
            
            hit = self.move_and_collide(nx, ny, walls, ignore)
            if hit and self.state == "ROAM": self.target_pos = None
            self.dir_x = 1 if nx>0 else (-1 if nx<0 else 0)
            self.dir_y = 1 if ny>0 else (-1 if ny<0 else 0)
            
            self.anim_time += math.pi / move_frames
        else:
            if self.state == "ROAM" and d <= self.speed: 
                self.target_pos = None

    def get_hand_world_positions(self):
        sm = 1.5 if self.is_large else 1.0
        rv = int((TILE//2-2)*sm)
        head_r = int(rv * 2.6)

        wt = getattr(self, "anim_time", 0.0)

        move_x = float(self.dir_x)
        move_y = float(self.dir_y)
        mag = math.hypot(move_x, move_y)
        if mag == 0: move_x, move_y = 1.0, 0.0
        else:        move_x /= mag; move_y /= mag

        amx = getattr(self, "_arm_smx", move_x)
        amy = getattr(self, "_arm_smy", move_y)
        sm_mag = math.hypot(amx, amy)
        if sm_mag > 0.001: amx, amy = amx/sm_mag, amy/sm_mag
        else:              amx, amy = move_x, move_y

        arm_len    = int(head_r * 2.0)
        hand_r2    = int(head_r * 0.36)
        walk_cycle = -math.cos(wt)
        cx, cy = self.rect.centerx, self.rect.centery

        results = []
        for side, arm_phase in [(-1, 1.0), (1, -1.0)]:
            sh_x = side * int(head_r * 0.70)
            sh_y = int(head_r * 0.90)
            sway = walk_cycle * arm_phase
            extend_t = sway * 0.5 + 0.5
            near_x = side*head_r*0.55
            near_y = head_r*1.15
            far_x  = sh_x + amx*arm_len + side*head_r*0.40
            far_y  = sh_y + amy*arm_len + head_r*0.30
            hx = near_x + (far_x-near_x)*extend_t
            hy = near_y + (far_y-near_y)*extend_t
            results.append((cx+hx, cy+hy, hand_r2, extend_t))
        return results

    def resolve_overlap(self, other):
        dx = self.rect.centerx-other.rect.centerx
        dy = self.rect.centery-other.rect.centery
        d  = math.hypot(dx, dy)
        md = TILE*1.5 if self.is_large else TILE
        if d < md:
            if d == 0: dx,dy,d = random.choice([-1,1]),random.choice([-1,1]),1.414
            pf = (md-d)/2
            self.x += dx/d*pf; self.y += dy/d*pf
            other.x -= dx/d*pf; other.y -= dy/d*pf
            self.rect.topleft  = (int(self.x),  int(self.y))
            other.rect.topleft = (int(other.x), int(other.y))

    def draw(self, surface, camera):
        r  = camera.apply(self)
        sm = 1.5 if self.is_large else 1.0
        rv = int((TILE//2-2)*sm)
        x, y = r.centerx, r.centery
        c = self.color

        wt = getattr(self, "anim_time", 0.0)
        bob  = math.sin(wt * 2) * int(2 * sm)

        head_r = int(rv * 2.6)
        cw  = head_r * 6
        ch2 = head_r * 6
        canvas = pygame.Surface((cw, ch2), pygame.SRCALPHA)
        cx, cy = cw // 2, ch2 // 2

        dark  = (max(0,c[0]-85), max(0,c[1]-85), max(0,c[2]-85))
        shade = (max(0,c[0]-40), max(0,c[1]-40), max(0,c[2]-40))

        body_cx = cx
        body_cy = cy + bob

        n = 32
        body_pts = []
        for i in range(n):
            a = -math.pi/2 + i * (2*math.pi/n)
            s_a = math.sin(a)
            rad = head_r if s_a <= 0 else head_r * (1.0 - s_a * 0.12)
            body_pts.append((body_cx + math.cos(a)*rad,
                             body_cy + s_a * rad * 1.12))
        pygame.draw.polygon(canvas, (*c, 232), body_pts)
        hl = pygame.Surface((cw, ch2), pygame.SRCALPHA)
        for i in range(n):
            a = -math.pi/2 + i * (2*math.pi/n)
            s_a = math.sin(a)
            rad = head_r if s_a <= 0 else head_r * (1.0 - s_a * 0.12)
            if math.cos(a) > 0.2:
                px2 = body_cx + math.cos(a)*rad*0.82
                py2 = body_cy + s_a*rad*1.12*0.85
                pygame.draw.circle(hl, (*dark, 50), (int(px2),int(py2)), max(3,int(head_r*0.42)))
        canvas.blit(hl,(0,0))
        pygame.draw.polygon(canvas, (*dark, 210), body_pts, 2)

        eye_r  = int(head_r * 0.33)
        eye_dx = int(head_r * 0.38)
        eye_y3 = body_cy - int(head_r * 0.22)
        for sgn in (-1, 1):
            ecx = body_cx + sgn * eye_dx
            pygame.draw.ellipse(canvas, (12,3,3,255),
                (ecx-eye_r, eye_y3-int(eye_r*1.1), eye_r*2, int(eye_r*2.2)))
            pygame.draw.circle(canvas, (210,195,195,160),
                (ecx-int(eye_r*0.22), eye_y3-int(eye_r*0.30)),
                max(1,int(eye_r*0.26)))

        mouth_w = int(head_r * 1.85)
        mouth_h = int(head_r * 0.62)
        myr     = body_cy + int(head_r * 0.40)
        mr = pygame.Rect(body_cx-mouth_w//2, myr-mouth_h//2, mouth_w, mouth_h)
        radius = mouth_h // 2
        pygame.draw.rect(canvas, (10,3,3,255), mr, border_radius=radius)
        pygame.draw.rect(canvas, (*dark,255), mr, 2, border_radius=radius)

        n_t = 8
        inner_pad = radius // 2
        usable_l = mr.left + inner_pad
        usable_w = mouth_w - inner_pad*2
        tw3  = usable_w / n_t
        th_up = int(mouth_h * 0.46)
        th_dn = int(mouth_h * 0.40)
        for i in range(n_t):
            tx0    = usable_l + i*tw3
            tx_end = tx0 + tw3 - 2
            tx_mid = (tx0 + tx_end) / 2
            pygame.draw.polygon(canvas, (238,232,220,255),
                [(tx0, mr.top+3),(tx_end, mr.top+3),(tx_mid, mr.top+3+th_up)])
            bx0    = usable_l + (i+0.5)*tw3
            bx_end = bx0 + tw3 - 2
            bx_mid = (bx0 + bx_end) / 2
            if bx_end <= mr.right - inner_pad:
                pygame.draw.polygon(canvas, (218,210,198,255),
                    [(bx0, mr.bottom-3),(bx_end, mr.bottom-3),(bx_mid, mr.bottom-3-th_dn)])

        move_x = float(self.dir_x)
        move_y = float(self.dir_y)
        mag = math.hypot(move_x, move_y)
        if mag == 0: move_x, move_y = 1.0, 0.0
        else:        move_x /= mag; move_y /= mag

        if not hasattr(self, "_arm_smx"):
            self._arm_smx, self._arm_smy = move_x, move_y
        lerp = 0.10
        self._arm_smx += (move_x - self._arm_smx) * lerp
        self._arm_smy += (move_y - self._arm_smy) * lerp
        sm_mag = math.hypot(self._arm_smx, self._arm_smy)
        if sm_mag > 0.001:
            amx, amy = self._arm_smx/sm_mag, self._arm_smy/sm_mag
        else:
            amx, amy = move_x, move_y
        turn_amt = max(0.0, min(1.0, math.hypot(move_x-amx, move_y-amy) * 1.6))

        arm_len = int(head_r * 2.0)
        arm_w   = max(4, int(head_r * 0.42))
        hand_r2 = int(head_r * 0.36)

        walk_cycle = -math.cos(wt)   
        is_grabbing = getattr(self, "grabbing", False)
        for side, arm_phase in [(-1, 1.0), (1, -1.0)]:
            sh_x = body_cx + side * int(head_r * 0.70)   
            sh_y = body_cy + int(head_r * 0.90)          
            pygame.draw.circle(canvas, (*c,235), (int(sh_x),int(sh_y)), int(arm_w*0.75))

            sway = walk_cycle * arm_phase           
            extend_t = sway * 0.5 + 0.5             

            near_x = body_cx + side*head_r*0.55
            near_y = body_cy + head_r*1.15
            far_x = sh_x + amx*arm_len + side*head_r*0.40
            far_y = sh_y + amy*arm_len + head_r*0.30

            hx = near_x + (far_x-near_x)*extend_t
            hy = near_y + (far_y-near_y)*extend_t

            elbow_out = head_r * (0.80 - 0.12*extend_t) + turn_amt*head_r*0.12
            mid_x = (sh_x+hx)/2 + side*elbow_out
            mid_y = (sh_y+hy)/2 - head_r*0.12*(1.0-extend_t)

            n_seg = 10
            curve_pts = []
            for si in range(n_seg+1):
                t = si / n_seg
                bx = (1-t)**2*sh_x + 2*(1-t)*t*mid_x + t**2*hx
                by = (1-t)**2*sh_y + 2*(1-t)*t*mid_y + t**2*hy
                curve_pts.append((bx, by))
            for si in range(n_seg):
                p0 = (int(curve_pts[si][0]),   int(curve_pts[si][1]))
                p1 = (int(curve_pts[si+1][0]), int(curve_pts[si+1][1]))
                taper = arm_w if si < n_seg*0.6 else max(arm_w-3, int(arm_w*0.78))
                pygame.draw.line(canvas, (*shade,240), p0, p1, taper+3)
            for si in range(n_seg):
                p0 = (int(curve_pts[si][0]),   int(curve_pts[si][1]))
                p1 = (int(curve_pts[si+1][0]), int(curve_pts[si+1][1]))
                taper = arm_w if si < n_seg*0.6 else max(arm_w-3, int(arm_w*0.78))
                pygame.draw.line(canvas, (*c,232), p0, p1, taper)
                pygame.draw.circle(canvas, (*c,232), p0, taper//2)

            hand = (int(hx), int(hy))
            hand_dir_a = math.atan2(curve_pts[-1][1]-curve_pts[-3][1],
                                     curve_pts[-1][0]-curve_pts[-3][0])

            pygame.draw.circle(canvas, (*c,235), hand, int(hand_r2*0.85))

            palm_r = int(hand_r2*0.95)
            pygame.draw.circle(canvas, (*c,240), hand, palm_r)
            pygame.draw.circle(canvas, (*dark,200), hand, palm_r, 2)

            finger_len = int(head_r * 0.62)
            finger_w   = max(3, int(arm_w*0.40))
            if is_grabbing:
                curl_len = finger_len * 0.30
                for fi in range(4):
                    fa = hand_dir_a + (fi-1.5)*0.55
                    fx0 = hx + math.cos(fa)*palm_r*0.55
                    fy0 = hy + math.sin(fa)*palm_r*0.55
                    fx1 = hx + math.cos(fa)*(palm_r*0.55+curl_len)
                    fy1 = hy + math.sin(fa)*(palm_r*0.55+curl_len)
                    pygame.draw.line(canvas, (*dark,235), (int(fx0),int(fy0)), (int(fx1),int(fy1)), finger_w+1)
                    pygame.draw.circle(canvas, (*c,240), (int(fx1),int(fy1)), finger_w//2+1)
                pygame.draw.circle(canvas, (*dark,200), hand, palm_r, 3)
            else:
                for fi in range(4):
                    fa = hand_dir_a + (fi-1.5)*0.24
                    fx0 = hx + math.cos(fa)*palm_r*0.5
                    fy0 = hy + math.sin(fa)*palm_r*0.5
                    fx1 = hx + math.cos(fa)*(palm_r*0.5+finger_len)
                    fy1 = hy + math.sin(fa)*(palm_r*0.5+finger_len)
                    pygame.draw.line(canvas, (*c,235), (int(fx0),int(fy0)), (int(fx1),int(fy1)), finger_w)
                    pygame.draw.circle(canvas, (*c,235), (int(fx1),int(fy1)), finger_w//2)
                    pygame.draw.line(canvas, (*dark,160), (int(fx0),int(fy0)), (int(fx1),int(fy1)), 1)
                ta = hand_dir_a - side*0.85
                tx0 = hx + math.cos(ta)*palm_r*0.40
                ty0 = hy + math.sin(ta)*palm_r*0.40
                tx1 = hx + math.cos(ta)*(palm_r*0.40+finger_len*0.55)
                ty1 = hy + math.sin(ta)*(palm_r*0.40+finger_len*0.55)
                pygame.draw.line(canvas, (*c,235), (int(tx0),int(ty0)), (int(tx1),int(ty1)), finger_w+1)
                pygame.draw.circle(canvas, (*c,235), (int(tx1),int(ty1)), finger_w//2+1)

        surface.blit(canvas, (x - cx, y - cy))

# ================= GAME ENGINE =================
class GameEngine:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        pygame.mixer.set_reserved(2)
        
        self.screen       = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Pac-man The Labyrinth")

        self.game_surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
        self.fog          = pygame.Surface((GAME_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
        
        self.spr_tile1      = load_sprite_scaled("assets/tile1.png")
        self.spr_tile2      = load_sprite_scaled("assets/tile2.png")
        self.spr_wall1      = load_sprite_scaled("assets/wall1.png")
        self.spr_wall2      = load_sprite_scaled("assets/wall2.png")
        self.spr_wall3      = load_sprite_scaled("assets/wall3.png")
        self.spr_wallwindow = load_sprite_scaled("assets/wallwindow.png")
        self.spr_bush       = load_sprite_scaled("assets/bush.png")

        self.clock       = pygame.time.Clock()
        self.font        = load_font("assets/04b_03.ttf", 20)
        self.title_font  = load_font("assets/04b_03.ttf", 44)
        self.small_title_font = load_font("assets/04b_03.ttf", 30)
        self.popup_font  = load_font("assets/04b_03.ttf", 22)

        self.player_stats     = PlayerStats()
        self.level_start_coins= 0
        self.current_level    = 1
        self.state            = "MENU"
        self.shop_selected_index = 0

        self.sfx_step   = load_sound("assets/playerStep.wav")
        self.sfx_stomp  = load_sound("assets/heavy stomp.wav")
        self.sfx_lever  = load_sound("assets/breaker.wav")
        self.sfx_button = load_sound("assets/breaker alarm.wav")
        self.sfx_grab   = load_sound("assets/grab.wav")
        self.sfx_bell   = load_sound("assets/subtleBell.wav") # Thêm âm thanh bell
        self.sfx_dead   = load_sound("assets/dead monster.wav") # Thêm âm thanh dead monster
        
        self.snd_ambience = load_sound("assets/ambience.wav")
        self.snd_chase    = load_sound("assets/chase.wav")
        self.chan_amb = pygame.mixer.Channel(0)
        self.chan_chs = pygame.mixer.Channel(1)
        self.vol_amb  = 0.0
        self.vol_chs  = 0.0

        self.eye_img     = load_img("assets/eye.png",     (51,24))
        self.speaker_img = load_img("assets/speaker.png", (31,24))

        self.speaker_flash_timer = 0
        self.speaker_flash_loud  = False
        self.shake_intensity     = 0

        self.hand_grab_timer = 0
        self.hand_grab_boss  = None

        self.show_level_choices = False
        self.btn_labyrinth = pygame.Rect(SCREEN_WIDTH//2-150, 300, 300, 50)
        self.btn_choose    = pygame.Rect(SCREEN_WIDTH//2-150, 370, 300, 50)
        self.btn_lvls      = [
            pygame.Rect(SCREEN_WIDTH//2-190, 440, 60, 50),
            pygame.Rect(SCREEN_WIDTH//2-120, 440, 60, 50),
            pygame.Rect(SCREEN_WIDTH//2-50,  440, 60, 50),
            pygame.Rect(SCREEN_WIDTH//2+20,  440, 60, 50),
            pygame.Rect(SCREEN_WIDTH//2+90,  440, 100, 50),
        ]
        self.btn_classic   = pygame.Rect(SCREEN_WIDTH//2-150, 440, 300, 50)
        
        self.btn_continue  = pygame.Rect(SCREEN_WIDTH//2-150, 400, 300, 50)
        self.btn_exit_pause= pygame.Rect(SCREEN_WIDTH//2-150, 470, 300, 50)
        
        self.vol_rect      = pygame.Rect(SCREEN_WIDTH//2-150, 520, 300, 20)
        self.global_volume = 1.0
        self._update_volume()

        self.buff_popup_text  = []
        self.buff_popup_timer = 0

        self.jumpscare_timer = 0
        self.jumpscare_phase = "flash"

    def _update_volume(self):
        ov = self.global_volume * 0.8
        if self.sfx_step:   self.sfx_step.set_volume(ov * 0.3)
        if self.sfx_lever:  self.sfx_lever.set_volume(ov * 0.54 * 0.9)
        if self.sfx_button: self.sfx_button.set_volume(ov * 0.48 * 0.5)
        if self.sfx_grab:   self.sfx_grab.set_volume(ov * 0.64)
        if self.sfx_bell:   self.sfx_bell.set_volume(ov * 0.77)
        if self.sfx_dead:   self.sfx_dead.set_volume(ov * 1.0) # Thêm volume cho dead monster

    def build_visual_surface(self, w, h, walls_list):
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

    def get_valid_spawn_pos(self, obj_w, obj_h):
        for _ in range(500):
            tx = random.randint(3, (self.map_w//TILE)-4)*TILE
            ty = random.randint(3, (self.map_h//TILE)-4)*TILE
            r  = pygame.Rect(tx, ty, obj_w, obj_h)
            if r.collidelist(self.walls) == -1:
                door_rect = pygame.Rect(TILE*2, TILE*2, TILE*5, TILE*4)
                if r.colliderect(door_rect):
                    continue
                center_rect = pygame.Rect(self.map_w//2 - TILE*3, self.map_h//2 - TILE*2,
                                          TILE*8, TILE*4)
                if r.colliderect(center_rect):
                    continue
                if self.current_level==5 and hasattr(self,'center_room_rect') and self.center_room_rect:
                    if r.colliderect(self.center_room_rect): continue
                return tx, ty
        return TILE*6, TILE*6

    def get_spaced_spawn_pos(self, obj_w, obj_h, existing_points, min_dist):
        for _ in range(500):
            tx, ty = self.get_valid_spawn_pos(obj_w, obj_h)
            valid = True
            for px, py in existing_points:
                if math.hypot(tx - px, ty - py) < min_dist:
                    valid = False
                    break
            if valid:
                return tx, ty
        return self.get_valid_spawn_pos(obj_w, obj_h)

    def _find_safe_spawn(self, target_x, target_y, size=TILE):
        r = pygame.Rect(target_x, target_y, size, size)
        if r.collidelist(self.walls) == -1:
            return target_x, target_y
        for radius in range(1, 30):
            for dx in range(-radius, radius+1):
                for dy in range(-radius, radius+1):
                    if abs(dx) != radius and abs(dy) != radius:
                        continue
                    tx = target_x + dx * TILE
                    ty = target_y + dy * TILE
                    if tx < TILE*3 or ty < TILE*3:
                        continue
                    if tx + size > self.map_w - TILE*3 or ty + size > self.map_h - TILE*3:
                        continue
                    r = pygame.Rect(tx, ty, size, size)
                    if r.collidelist(self.walls) == -1:
                        return tx, ty
        return target_x, target_y

    def generate_map(self):
        self.walls, self.center_room_rect = build_level_walls(self.current_level, self.map_w, self.map_h)

    def reset_game(self, next_level=False, keep_stats=False):
        if not keep_stats:
            if not next_level:
                self.player_stats = PlayerStats()
            self.level_start_coins = self.player_stats.coins
        else:
            self.player_stats.coins = self.level_start_coins

        self.m5_doors_closed  = False
        self.buff_popup_timer = 0
        self.green_door_unlocked = False

        scales = {1:0.65, 2:0.7, 3:0.8, 4:1.0, 5:1.25}
        sc = scales[self.current_level]
        self.map_w = int(BASE_MAP_W*sc)
        self.map_h = int(BASE_MAP_H*sc)

        self.camera = Camera(self.map_w, self.map_h)
        self.generate_map()
        self.map_surface = self.build_visual_surface(self.map_w, self.map_h, self.walls)

        center_x = self.map_w // 2
        center_y = self.map_h // 2
        spawn_x, spawn_y = self._find_safe_spawn(center_x, center_y, TILE)
        self.player = Player(spawn_x, spawn_y, self.player_stats)

        boss_count = 2 if self.current_level==4 else 1
        self.bosses = []
        for i in range(boss_count):
            bx = TILE * 6
            by = TILE * 6 if i == 0 else self.map_h - TILE * 7
            bx, by = self._find_safe_spawn(bx, by, TILE)
            b = StalkerBoss(bx, by, self.current_level)
            self.bosses.append(b)

        self.interactables   = []
        self.levers_pulled   = 0
        self.buttons_pressed = 0
        self.door_spawned    = False

        self.m5_hear = self.m5_see = self.m5_smell = False
        self.carrying_item  = False
        self.m5_items_placed= 0
        self.m5_survival_timer = 30*FPS

        level_reqs = {1:(2,0), 2:(3,0), 3:(3,1), 4:(4,3), 5:(0,0)}
        self.target_levers, self.target_buttons = level_reqs[self.current_level]

        dot_counts    = {1:30, 2:40, 3:50, 4:60, 5:40}
        candle_counts = {1:8,  2:8,  3:14, 4:16, 5:5} # Màn 5 sẽ sinh thêm 4 cây gần Artifact = Tổng 9 cây nến

        for _ in range(dot_counts[self.current_level]):
            x, y = self.get_valid_spawn_pos(TILE, TILE)
            self.interactables.append(Dot(x, y))

        for _ in range(candle_counts[self.current_level]):
            x, y = self.get_valid_spawn_pos(TILE, TILE)
            self.interactables.append(Candle(x, y))

        existing_objs = []
        for _ in range(self.target_levers):
            x, y = self.get_spaced_spawn_pos(TILE, TILE, existing_objs, GAME_WIDTH // 2)
            self.interactables.append(Lever(x, y))
            existing_objs.append((x, y))

        for _ in range(self.target_buttons):
            x, y = self.get_spaced_spawn_pos(TILE, TILE, existing_objs, GAME_WIDTH // 2)
            self.interactables.append(ButtonInteract(x, y))
            existing_objs.append((x, y))

        if self.current_level < 5:
            door_x = TILE * 5
            door_y = TILE * 5
            door_x, door_y = self._find_safe_spawn(door_x, door_y, TILE*2)
            self.interactables.append(GreenDoor(door_x, door_y))
            self.door_spawned = True

        if self.current_level == 5:
            altar_x = self.center_room_rect.centerx - TILE
            altar_y = self.center_room_rect.centery - TILE
            altar_x, altar_y = self._find_safe_spawn(altar_x, altar_y, TILE*2)
            self.altar_obj = Altar(altar_x, altar_y)
            
            cols = self.map_w // TILE
            rows = self.map_h // TILE
            corners = [
                (5 * TILE, 5 * TILE),                         
                ((cols - 6) * TILE, 5 * TILE),                
                (5 * TILE, (rows - 6) * TILE),                
                ((cols - 6) * TILE, (rows - 6) * TILE)        
            ]
            for cx, cy in corners:
                sx, sy = self._find_safe_spawn(cx, cy, TILE)
                self.interactables.append(SpecialItem(sx, sy))
                # Đảm bảo có ít nhất 1 cây nến ở gần Artifact
                csx, csy = self._find_safe_spawn(sx + TILE*2, sy, TILE)
                self.interactables.append(Candle(csx, csy))
        else:
            self.altar_obj = None

        note_x = self.player.rect.x + TILE * 2
        note_y = self.player.rect.y
        note_x, note_y = self._find_safe_spawn(note_x, note_y, TILE)
        self.interactables.append(Note(note_x, note_y))

        candle_x = self.player.rect.x - TILE * 3
        candle_y = self.player.rect.y
        candle_x, candle_y = self._find_safe_spawn(candle_x, candle_y, TILE)
        self.interactables.append(Candle(candle_x, candle_y))

        self.camera.snap(self.player)
        self.state = "LEVEL_INTRO"

    def enter_hallway(self):
        self.state = "HALLWAY"
        self.hall_w, self.hall_h = 1200, 400
        self.camera = Camera(self.hall_w, self.hall_h)
        self.hall_walls = [
            pygame.Rect(0,0,self.hall_w,TILE*3),
            pygame.Rect(0,self.hall_h-TILE*3,self.hall_w,TILE*3),
            pygame.Rect(0,0,TILE*3,self.hall_h),
            pygame.Rect(self.hall_w-TILE*3,0,TILE*3,self.hall_h),
        ]
        self.player.x = 150.0; self.player.y = 200.0
        self.player.rect.topleft = (150, 200)
        self.hall_items = [
            WoodenDoor(550, 200-TILE),
            GreenDoor(1050, 200-TILE),
            UnpickableCandle(510, 200),
        ]
        self.hall_items[1].locked = False
        self.camera.snap(self.player)
        self.hall_surface = self.build_visual_surface(self.hall_w, self.hall_h, self.hall_walls)

    def make_noise(self, x, y, radius, is_loud):
        self.speaker_flash_timer = 60
        self.speaker_flash_loud  = is_loud
        if is_loud:
            self.shake_intensity = 30
            radius = 999999
        for b in self.bosses:
            b.hear_noise(x, y, radius, 1.0)

    def handle_events(self):
        mp = pygame.mouse.get_pos()
        mb = pygame.mouse.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if self.state == "MENU" and event.type == pygame.MOUSEBUTTONDOWN:
                if self.btn_labyrinth.collidepoint(mp):
                    self.current_level = 1
                    self.reset_game(next_level=False)
                elif self.btn_choose.collidepoint(mp):
                    self.show_level_choices = not self.show_level_choices
                elif self.show_level_choices:
                    for i, btn in enumerate(self.btn_lvls):
                        if btn.collidepoint(mp):
                            lvl = i + 1
                            self.player_stats = PlayerStats()
                            if lvl == 1:
                                self.current_level = 1
                                self.reset_game(next_level=False)
                            else:
                                coins_map = {2: 250, 3: 400, 4: 600, 5: 900}
                                self.player_stats.coins = coins_map[lvl]
                                self.shop_target_level = lvl
                                self.state = "SHOP"

            if event.type == pygame.KEYDOWN:
                if self.state == "LEVEL_INTRO" and event.key == pygame.K_SPACE:
                    self.state = "PLAYING"

                elif self.state == "JUMPSCARE":
                    if self.jumpscare_phase == "dead" and self.jumpscare_timer > 75:
                        if event.key == pygame.K_SPACE:
                            self.reset_game(next_level=False, keep_stats=True)
                        elif event.key == pygame.K_ESCAPE:
                            self.state = "MENU"

                elif self.state == "VICTORY_SCREEN":
                    if event.key in (pygame.K_ESCAPE, pygame.K_SPACE):
                        self.state = "MENU"

                elif self.state == "DOOR_PROMPT":
                    if event.key == pygame.K_y:
                        self.enter_hallway()
                    elif event.key == pygame.K_n:
                        self.state = "PLAYING"
                        self.player.x -= 40

                elif self.state == "SHOP":
                    if event.key == pygame.K_UP:
                        self.shop_selected_index = (self.shop_selected_index-1)%4
                    elif event.key == pygame.K_DOWN:
                        self.shop_selected_index = (self.shop_selected_index+1)%4
                    elif event.key == pygame.K_RETURN:
                        self.buy_shop_upgrade()
                    elif event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                        if hasattr(self, 'shop_target_level') and self.shop_target_level is not None:
                            self.current_level = self.shop_target_level
                            self.reset_game(next_level=True, keep_stats=True)
                            self.shop_target_level = None
                        else:
                            self.state = "HALLWAY"

                elif self.state in ("PLAYING","HALLWAY"):
                    if event.key == pygame.K_ESCAPE:
                        self.prev_state = self.state
                        self.state = "PAUSED"

                    if event.key == pygame.K_e:
                        items = self.hall_items if self.state=="HALLWAY" else self.interactables
                        did = False

                        for item in items:
                            if isinstance(item,(Note,Lever,GreenDoor,WoodenDoor)) \
                                    and item.active and self.player.rect.colliderect(item.rect):
                                item.interact(self.player, self)
                                did = True
                                break

                        if self.current_level==5 and self.state=="PLAYING" and not did:
                            if hasattr(self, 'altar_obj') and self.altar_obj is not None:
                                if self.player.rect.colliderect(self.altar_obj.rect) and self.carrying_item:
                                    if self.sfx_bell: self.sfx_bell.play()
                                    self.m5_items_placed += 1
                                    buff = []
                                    if self.m5_items_placed==1:
                                        self.m5_hear=True
                                        self.m5_smell=True
                                        buff = ["Ghost can HEAR", "Ghost can SMELL"]
                                    elif self.m5_items_placed==2:
                                        self.m5_see=True
                                        buff = ["Ghost can SEE"]
                                    elif self.m5_items_placed==3:
                                        nb = StalkerBoss(self.bosses[0].rect.x,
                                                        self.bosses[0].rect.y, 5)
                                        nb.can_phase              = True
                                        nb.can_hear               = self.m5_hear
                                        nb.can_see                = self.m5_see
                                        nb.can_see_through_walls  = self.m5_see
                                        nb.can_smell              = self.m5_smell
                                        self.bosses.append(nb)
                                        buff = ["Ghost can DUPLICATE"]
                                    elif self.m5_items_placed==4:
                                        for b in self.bosses:
                                            b.speed *= 0.75
                                            b.current_speed = min(b.current_speed, b.speed)
                                        buff = ["Ghost is SLOW", "TRAPPED! SURVIVE 30s!"]
                                        
                                    self.buff_popup_text  = buff
                                    self.buff_popup_timer = 180 if self.m5_items_placed < 4 else 240
                                    self.shake_intensity  = 30
                                    self.carrying_item    = False
                                    did = True
                                    self.make_noise(self.player.rect.centerx,
                                                    self.player.rect.centery, 0, True)

                        if not did and self.state=="PLAYING":
                            if self.player.has_candle:
                                self.player.has_candle = False
                                if self.sfx_grab:
                                    self.sfx_grab.play()
                                self.interactables.append(
                                    Candle(self.player.rect.x, self.player.rect.y))
                                self._update_player_visibility()
                            else:
                                for item in self.interactables:
                                    if isinstance(item,Candle) and item.active \
                                            and self.player.rect.colliderect(item.rect):
                                        self.player.has_candle = True
                                        item.active = False
                                        if self.sfx_grab:
                                            self.sfx_grab.play()
                                        break
                
                elif self.state == "PAUSED":
                    if event.key == pygame.K_ESCAPE:
                        self.state = self.prev_state

            if self.state == "PAUSED" and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.btn_continue.collidepoint(mp):
                    self.state = self.prev_state
                elif self.btn_exit_pause.collidepoint(mp):
                    self.state = "MENU"

        if self.state in ("MENU", "PAUSED") and mb[0] and self.vol_rect.collidepoint(mp):
            self.global_volume = max(0.0,min(1.0,(mp[0]-self.vol_rect.x)/self.vol_rect.width))
            self._update_volume()
            if self.state == "PAUSED":
                any_chase = any(b.state=="CHASE" for b in getattr(self, 'bosses', []))
                ov = self.global_volume * 0.8
                base_music_vol = ov * 0.38
                self.vol_amb = 0.0 if any_chase else base_music_vol
                self.vol_chs = base_music_vol if any_chase else 0.0
                if hasattr(self, 'chan_amb'): self.chan_amb.set_volume(self.vol_amb)
                if hasattr(self, 'chan_chs'): self.chan_chs.set_volume(self.vol_chs)

    def buy_shop_upgrade(self):
        st = self.player_stats
        if self.shop_selected_index == 0:
            costs  = {0:90,1:140,2:190,3:250}
            speeds = {1:2.875, 2:3.45, 3:4.025, 4:4.6}
            if st.speed_level < 4 and st.coins >= costs[st.speed_level]:
                st.coins -= costs[st.speed_level]; st.speed_level += 1
                st.speed = speeds[st.speed_level]
        elif self.shop_selected_index == 1:
            if not st.candle_upgraded and st.coins >= 110:
                st.coins -= 110; st.candle_upgraded = True; st.vision_radius = 7.2
        elif self.shop_selected_index == 2:
            if not st.muffler_upgraded and st.coins >= 120:
                st.coins -= 120; st.muffler_upgraded = True; st.noise_radius = 8.0
        elif self.shop_selected_index == 3:
            if not st.stealth_upgraded and st.coins >= 150:
                st.coins -= 150; st.stealth_upgraded = True; st.smell_modifier = 0.8

    def update(self):
        keys = pygame.key.get_pressed()
        self._update_player_visibility()
        if self.state == "PLAYING":
            if self.hand_grab_timer > 0:
                self.hand_grab_timer -= 1
                if self.hand_grab_timer <= 0:
                    if self.hand_grab_boss is not None:
                        self.hand_grab_boss.grabbing = False
                        self.hand_grab_boss = None
                    self.jumpscare_timer = 0
                    self.jumpscare_phase = "flash"
                    self.state = "JUMPSCARE"
                return

            self.player.move(keys, self.walls, self)
            self.camera.update(self.player)

            holding_e = keys[pygame.K_e]
            btn_found = False

            for item in self.interactables:
                if isinstance(item,Dot) and item.active and self.player.rect.colliderect(item.rect):
                    item.interact(self.player, self)
                elif isinstance(item,SpecialItem) and item.active \
                        and self.player.rect.colliderect(item.rect):
                    item.interact(self.player, self)
                elif isinstance(item,ButtonInteract) and item.active \
                        and self.player.rect.colliderect(item.rect):
                    btn_found = True
                    if holding_e:
                        item.hold_progress += 1
                        if item.hold_progress >= item.required_frames:
                            item.active = False
                            self.buttons_pressed += 1
                            if self.sfx_button: self.sfx_button.play()
                            self.make_noise(item.rect.centerx,item.rect.centery,0,True)
                    else:
                        item.hold_progress = 0

            if not (btn_found and holding_e):
                for item in self.interactables:
                    if isinstance(item,ButtonInteract) and item.active:
                        item.hold_progress = 0

            self.interactables = [i for i in self.interactables if i.active or isinstance(i, Lever)]

            for boss in self.bosses:
                if self.current_level==5:
                    boss.update_skills_m5(self.m5_hear, self.m5_see, self.m5_smell)

                boss.update(self.player, self.walls, self.map_w, self.map_h, self)

                if self.player.rect.colliderect(boss.rect):
                    self.jumpscare_timer = 0
                    self.jumpscare_phase = "flash"
                    self.state = "JUMPSCARE"

                if self.hand_grab_timer <= 0 and self.state == "PLAYING":
                    for hx_w, hy_w, hr, extend_t in boss.get_hand_world_positions():
                        hand_rect = pygame.Rect(hx_w-hr, hy_w-hr, hr*2, hr*2)
                        if self.player.rect.colliderect(hand_rect):
                            boss.grabbing      = True
                            self.hand_grab_boss = boss
                            self.hand_grab_timer = 35   
                            if self.sfx_grab:
                                self.sfx_grab.play()
                            break

            if self.hand_grab_timer <= 0:
                for i,b in enumerate(self.bosses):
                    for j in range(i+1, len(self.bosses)):
                        b.resolve_overlap(self.bosses[j])

            any_chase = any(b.state=="CHASE" for b in self.bosses)
            ov = self.global_volume * 0.8
            base_music_vol = ov * 0.38
            target_amb = 0.0 if any_chase else base_music_vol
            target_chs = base_music_vol if any_chase else 0.0

            self.vol_amb += (target_amb - self.vol_amb) * 0.05
            self.vol_chs += (target_chs - self.vol_chs) * 0.05

            if not self.chan_amb.get_busy() and self.snd_ambience: self.chan_amb.play(self.snd_ambience, loops=-1)
            if not self.chan_chs.get_busy() and self.snd_chase: self.chan_chs.play(self.snd_chase, loops=-1)

            if self.chan_amb: self.chan_amb.set_volume(self.vol_amb)
            if self.chan_chs: self.chan_chs.set_volume(self.vol_chs)

            if self.current_level < 5:
                if self.door_spawned and not self.green_door_unlocked:
                    if self.levers_pulled >= self.target_levers \
                            and self.buttons_pressed >= self.target_buttons:
                        for item in self.interactables:
                            if isinstance(item, GreenDoor):
                                item.locked = False
                        self.green_door_unlocked = True
                        if self.sfx_button:
                            self.sfx_button.play()
                        self.buff_popup_text = ["GREEN DOOR UNLOCKED! Go to top-left!"]
                        self.buff_popup_timer = 180
                        self.shake_intensity = 20

            if self.current_level == 5:
                if self.m5_items_placed == 4 and not self.m5_doors_closed:
                    self.m5_doors_closed = True
                    rx, ry = self.center_room_rect.x, self.center_room_rect.y
                    rw, rh = self.center_room_rect.w, self.center_room_rect.h
                    gate = TILE * 3
                    self.walls += [
                        pygame.Rect(rx+(rw-gate)//2, ry,          gate, TILE),
                        pygame.Rect(rx+(rw-gate)//2, ry+rh-TILE,  gate, TILE),
                        pygame.Rect(rx,              ry+(rh-gate)//2, TILE, gate),
                        pygame.Rect(rx+rw-TILE,      ry+(rh-gate)//2, TILE, gate),
                    ]
                    self.map_surface = self.build_visual_surface(self.map_w, self.map_h, self.walls)
                    
                    spawn_positions = [
                        (rx + TILE * 2, ry + rh // 2 - TILE // 2),
                        (rx + rw - TILE * 3, ry + rh // 2 - TILE // 2)
                    ]
                    for i, b in enumerate(self.bosses):
                        sx, sy = spawn_positions[i % len(spawn_positions)]
                        b.x, b.y = float(sx), float(sy)
                        b.rect.topleft = (int(sx), int(sy))
                        b.state = "CHASE"
                        b.can_phase = True
                        b.can_see_through_walls = True
                    self.shake_intensity  = 40

                if self.m5_items_placed == 4:
                    self.m5_survival_timer -= 1
                    if self.m5_survival_timer <= 0:
                        self.state = "VICTORY_SCREEN"

    def _update_player_visibility(self):
        px, py = self.player.rect.centerx, self.player.rect.centery
        if self.player.has_candle:
            self.player.is_hidden = False
            return
        if self.state in ("HALLWAY", "PAUSED") and getattr(self, 'prev_state', self.state) == "HALLWAY":
            for item in getattr(self, 'hall_items', []):
                if isinstance(item, UnpickableCandle):
                    d = math.hypot(px - item.rect.centerx, py - item.rect.centery)
                    if d <= 6.0 * TILE:
                        self.player.is_hidden = False
                        return
            self.player.is_hidden = True
            return
        
        if self.current_level == 5 and hasattr(self, 'altar_obj') and self.altar_obj:
            dx = px - self.altar_obj.rect.centerx
            dy = py - self.altar_obj.rect.centery
            if math.hypot(dx, dy) <= (self.center_room_rect.width * 0.8):
                self.player.is_hidden = False
                return

        candle_radius = self.player.stats.vision_radius * TILE
        for item in self.interactables:
            if isinstance(item, Candle) and item.active:
                d = math.hypot(px - item.rect.centerx, py - item.rect.centery)
                if d <= candle_radius:
                    self.player.is_hidden = False
                    return
        for item in self.interactables:
            if isinstance(item, Note) and item.active:
                d = math.hypot(px - item.rect.centerx, py - item.rect.centery)
                if d <= 2.5 * TILE:
                    self.player.is_hidden = False
                    return
        for item in self.interactables:
            if isinstance(item, SpecialItem) and item.active:
                d = math.hypot(px - item.rect.centerx, py - item.rect.centery)
                if d <= 3 * TILE:
                    self.player.is_hidden = False
                    return
        self.player.is_hidden = True

    def render_lighting(self):
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
            elif isinstance(item,SpecialItem) and item.active:
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
        ox, oy = self.camera.camera.topleft
        self.game_surface.blit(self.map_surface, (ox, oy))

    def draw_hud(self):
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
                if self.m5_items_placed >= 3: skills.append("DUPLICATE")
                if self.m5_items_placed >= 4: skills.append("SLOW")
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

    def run(self):
        while True:
            self.handle_events()
            sx = sy = 0

            # Xử lý tắt nhạc khi không còn ở trạng thái cho phép nhạc
            if self.state not in ("PLAYING", "HALLWAY", "PAUSED"):
                if hasattr(self, 'chan_amb') and self.chan_amb.get_busy(): self.chan_amb.stop()
                if hasattr(self, 'chan_chs') and self.chan_chs.get_busy(): self.chan_chs.stop()
                self.vol_amb = 0.0; self.vol_chs = 0.0

            if self.state in ("PLAYING", "PAUSED"):
                md = min((math.hypot(b.rect.centerx-self.player.rect.centerx,
                                     b.rect.centery-self.player.rect.centery)
                          for b in self.bosses), default=9999)
                td = SCREEN_WIDTH//2
                total = int(self.shake_intensity + (max(0, td-md)/td*8 if md<td else 0))
                if total and self.state == "PLAYING":
                    sx = random.randint(-total, total)
                    sy = random.randint(-total, total)
                if self.shake_intensity > 0 and self.state == "PLAYING": self.shake_intensity -= 1

            if self.state == "MENU":
                self.screen.fill((10,10,10))
                title = self.title_font.render("Pac-man The Labyrinth", True, RED)
                self.screen.blit(title,(SCREEN_WIDTH//2-title.get_width()//2, 150))
                
                self.btn_classic.y = 510 if self.show_level_choices else 440
                self.vol_rect.y = 590 if self.show_level_choices else 520

                for btn,lbl in [(self.btn_labyrinth, "Labyrinth Mode"),
                                (self.btn_choose,    "Choose Level"),
                                (self.btn_classic,   "Classic Mode")]:
                    pygame.draw.rect(self.screen, (40,35,30), btn)
                    pygame.draw.rect(self.screen, (80,70,60), btn, 1)
                    t = self.font.render(lbl, True, WHITE)
                    self.screen.blit(t,(btn.centerx-t.get_width()//2,
                                        btn.centery-t.get_height()//2))

                if self.show_level_choices:
                    lbls = ["1", "2", "3", "4", "Final"]
                    for i, btn in enumerate(self.btn_lvls):
                        pygame.draw.rect(self.screen, (40,35,30), btn)
                        pygame.draw.rect(self.screen, (80,70,60), btn, 1)
                        t = self.font.render(lbls[i], True, WHITE)
                        self.screen.blit(t, (btn.centerx-t.get_width()//2, btn.centery-t.get_height()//2))

                vl = self.font.render("Volume:", True, WHITE)
                self.screen.blit(vl, (self.vol_rect.x-100, self.vol_rect.y))
                pygame.draw.rect(self.screen, GRAY, self.vol_rect)
                pygame.draw.rect(self.screen, GREEN,
                    (self.vol_rect.x, self.vol_rect.y,
                     int(self.vol_rect.width*self.global_volume), self.vol_rect.height))

            elif self.state == "LEVEL_INTRO":
                self.screen.fill(BLACK)
                lt = self.title_font.render(f"Level {self.current_level} / 5", True, WHITE)
                self.screen.blit(lt,(SCREEN_WIDTH//2-lt.get_width()//2, 200))
                abilities = [("MOVE", True)]
                if self.current_level == 5:
                    abilities.append(("DIE", True))
                elif self.current_level == 4:
                    abilities.append(("HEAR",  True))
                    abilities.append(("SEE",   True))
                    abilities.append(("SMELL", True))
                    abilities.append(("DUPLICATE", True))
                else:
                    abilities.append(("HEAR",  self.current_level >= 2))
                    abilities.append(("SEE",   self.current_level >= 3))
                    abilities.append(("SMELL", self.current_level >= 4))
                for i,(ab,unlocked) in enumerate(abilities):
                    if unlocked:
                        p    = self.title_font.render("Ghost can ", True, WHITE)
                        ab_t = self.title_font.render(ab, True, RED)
                        tw   = p.get_width()+ab_t.get_width()
                        xb   = SCREEN_WIDTH//2-tw//2
                        y    = 300+i*50
                        pygame.draw.polygon(self.screen,WHITE,
                            [(xb-40,y+p.get_height()//2-12),
                             (xb-28,y+p.get_height()//2),
                             (xb-40,y+p.get_height()//2+12)])
                        self.screen.blit(p,  (xb,y))
                        self.screen.blit(ab_t,(xb+p.get_width(),y))
                pr = self.font.render("Press SPACE to Start", True, DARK_GRAY)
                self.screen.blit(pr,(SCREEN_WIDTH//2-pr.get_width()//2, SCREEN_HEIGHT-100))

            elif self.state in ("PLAYING", "HALLWAY", "PAUSED"):
                active_state = self.state if self.state != "PAUSED" else getattr(self, 'prev_state', "PLAYING")

                if active_state == "PLAYING":
                    if self.state == "PLAYING":
                        self.update()
                    self.game_surface.fill(BLACK)
                    self.draw_world()
                    if self.current_level==5:
                        if hasattr(self, 'altar_obj') and self.altar_obj is not None:
                            self.altar_obj.draw(self.game_surface, self.camera)
                    for item in self.interactables:
                        item.draw(self.game_surface, self.camera)
                    self._update_player_visibility()
                    self.player.draw(self.game_surface, self.camera)
                    
                    for b in self.bosses: b.draw(self.game_surface, self.camera)
                    
                    self.render_lighting()

                    scaled = pygame.transform.scale(self.game_surface,(SCREEN_WIDTH,SCREEN_HEIGHT))
                    self.screen.blit(scaled,(sx,sy))
                    self.draw_hud()
                    
                    if self.buff_popup_timer > 0:
                        lines = self.buff_popup_text if isinstance(self.buff_popup_text, list) else [self.buff_popup_text]
                        rendered_lines = [self.popup_font.render(l, True, YELLOW) for l in lines]
                        max_w = max(r.get_width() for r in rendered_lines)
                        total_h = sum(r.get_height() for r in rendered_lines)
                        pad = 8
                        bg_rect = pygame.Rect(
                            SCREEN_WIDTH//2 - max_w//2 - pad,
                            75,
                            max_w + pad*2,
                            total_h + pad*2
                        )
                        pygame.draw.rect(self.screen, (20, 20, 20), bg_rect)
                        pygame.draw.rect(self.screen, YELLOW, bg_rect, 2)
                        cy = 75 + pad
                        for r in rendered_lines:
                            self.screen.blit(r, (SCREEN_WIDTH//2 - r.get_width()//2, cy))
                            cy += r.get_height() + 2
                        
                        if self.state == "PLAYING":
                            self.buff_popup_timer -= 1

                elif active_state == "HALLWAY":
                    if self.state == "HALLWAY":
                        keys = pygame.key.get_pressed()
                        self.player.move(keys, self.hall_walls, self)
                        self.camera.update(self.player)
                        for item in self.hall_items:
                            if isinstance(item,GreenDoor) and self.player.rect.colliderect(item.rect):
                                self.current_level += 1
                                self.reset_game(next_level=True); break
                                
                    self.game_surface.fill(BLACK)
                    ox, oy = self.camera.camera.topleft
                    self.game_surface.blit(self.hall_surface, (ox, oy))
                    
                    for item in self.hall_items:
                        item.draw(self.game_surface, self.camera)
                    self._update_player_visibility()
                    self.player.draw(self.game_surface, self.camera)
                    self.render_lighting()
                    scaled = pygame.transform.scale(self.game_surface,(SCREEN_WIDTH,SCREEN_HEIGHT))
                    self.screen.blit(scaled,(0,0))
                    t1 = self.font.render("SAFE HALLWAY - Wooden door: SHOP", True, GREEN)
                    t2 = self.font.render(f"Coins: {self.player_stats.coins}", True, YELLOW)
                    self.screen.blit(t1,(SCREEN_WIDTH//2-t1.get_width()//2, 30))
                    self.screen.blit(t2,(20,30))

                if self.state == "PAUSED":
                    dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                    dim.fill((0, 0, 0, 150))
                    self.screen.blit(dim, (0, 0))
                    
                    p_title = self.title_font.render("Game paused", True, WHITE)
                    self.screen.blit(p_title, (SCREEN_WIDTH//2-p_title.get_width()//2, 200))
                    
                    for btn,lbl in [(self.btn_continue,"Continue"), (self.btn_exit_pause,"Exit")]:
                        pygame.draw.rect(self.screen, (40,35,30), btn)
                        pygame.draw.rect(self.screen, (80,70,60), btn, 1)
                        t = self.font.render(lbl, True, WHITE)
                        self.screen.blit(t,(btn.centerx-t.get_width()//2, btn.centery-t.get_height()//2))
                        
                    vl = self.font.render("Volume:", True, WHITE)
                    self.screen.blit(vl, (self.vol_rect.x-100, self.vol_rect.y))
                    pygame.draw.rect(self.screen, GRAY, self.vol_rect)
                    pygame.draw.rect(self.screen, GREEN,
                        (self.vol_rect.x, self.vol_rect.y,
                         int(self.vol_rect.width*self.global_volume), self.vol_rect.height))

            elif self.state == "DOOR_PROMPT":
                self.screen.fill((15,5,5))
                box = pygame.Rect(162,234,700,300)
                pygame.draw.rect(self.screen,(40,35,30),box)
                pygame.draw.rect(self.screen,GREEN,box,3)
                for txt,y,col in [
                    ("PROCEED TO THE NEXT LEVEL?", 280, WHITE),
                    ("[Y] Proceed         [N] Stay",360, YELLOW),
                    ("Note: Uncollected dots disappear!", 440, RED),
                ]:
                    t = self.font.render(txt,True,col)
                    self.screen.blit(t,(SCREEN_WIDTH//2-t.get_width()//2, y))

            elif self.state == "SHOP":
                self.draw_shop_ui()

            elif self.state == "JUMPSCARE":
                # Phát âm thanh 1 lần khi bắt đầu jumpscare
                if self.jumpscare_timer == 0 and getattr(self, 'sfx_dead', None):
                    self.sfx_dead.play()
                    
                self.jumpscare_timer += 1
                t = self.jumpscare_timer

                # Phase 1: flash trắng chói (0-5 frame)
                if t <= 5:
                    self.jumpscare_phase = "flash"
                    self.screen.fill((int(255*(1-t/5)),)*3)

                # Phase 2: mặt ma lao thẳng vào (6-50 frame)
                elif t <= 50:
                    self.jumpscare_phase = "face"
                    self.screen.fill((0,0,0))
                    progress = (t-6)/44.0
                    ease     = 1.0-(1.0-progress)**2.5
                    size     = max(10, int(SCREEN_HEIGHT*0.12 + ease*SCREEN_HEIGHT*1.5))
                    shake_x  = random.randint(-12,12) if t>15 else 0
                    shake_y  = random.randint(-10,10) if t>15 else 0

                    # nhiễu tĩnh
                    if t < 35:
                        for _ in range(int(600*(1-progress*0.6))):
                            nx2 = random.randint(0,SCREEN_WIDTH-1)
                            ny2 = random.randint(0,SCREEN_HEIGHT-1)
                            nv  = random.randint(60,200)
                            self.screen.set_at((nx2,ny2),(nv,nv,nv))

                    # vẽ mặt
                    cs   = size
                    face = pygame.Surface((cs,cs), pygame.SRCALPHA)
                    fc   = cs//2
                    br2  = cs//2-2
                    rng2 = random.Random(42)

                    # thân oval méo
                    n_body = 40
                    body_pts = []
                    for i in range(n_body):
                        a   = -math.pi/2+i*(2*math.pi/n_body)
                        jit = 1.0+math.sin(a*3.7+t*0.3)*0.06
                        body_pts.append((
                            int(fc+math.cos(a)*br2*jit),
                            int(fc+math.sin(a)*br2*1.15*jit)))
                    pygame.draw.polygon(face,(140,8,8,240),body_pts)
                    pygame.draw.polygon(face,(80,0,0,255),body_pts,3)

                    # mắt bất đối xứng + tia máu
                    eye_r = max(3,br2//5)
                    for sgn,ey_off in [(-1,-br2//10),(1,br2//8)]:
                        ecx = fc+sgn*br2//3
                        ecy = fc-br2//8+ey_off
                        pygame.draw.ellipse(face,(0,0,0,255),
                            (ecx-eye_r, ecy-int(eye_r*1.4), eye_r*2, int(eye_r*2.8)))
                        for va_deg in range(0,360,45):
                            va  = math.radians(va_deg)
                            pygame.draw.line(face,(180,0,0,160),
                                (ecx+int(math.cos(va)*eye_r),   ecy+int(math.sin(va)*eye_r*1.4)),
                                (ecx+int(math.cos(va)*eye_r*1.9),ecy+int(math.sin(va)*eye_r*1.4*1.9)),1)
                        pygame.draw.circle(face,(230,220,210,200),(ecx,ecy),max(1,eye_r//3))

                    # miệng + răng
                    mw = int(br2*1.5); mh = int(br2*0.65); mcy = fc+br2//3
                    mr = pygame.Rect(fc-mw//2, mcy-mh//2, mw, mh)
                    pygame.draw.ellipse(face,(5,0,0,255),mr)
                    pygame.draw.ellipse(face,(60,0,0,255),mr,2)
                    n_t2 = 7; tw5 = mw//n_t2
                    th_list = [int(mh*(0.4+rng2.uniform(0,0.45))) for _ in range(n_t2)]
                    for i in range(n_t2):
                        tx3 = fc-mw//2+i*tw5+2; th2 = th_list[i]
                        pygame.draw.polygon(face,(235,225,210,255),
                            [(tx3,mcy-mh//2+2),(tx3+tw5-4,mcy-mh//2+2),(tx3+(tw5-4)//2,mcy-mh//2+2+th2)])
                    for i in range(n_t2-1):
                        tx3 = fc-mw//2+i*tw5+tw5//2+2
                        th2 = int(mh*rng2.uniform(0.2,0.38))
                        pygame.draw.polygon(face,(215,205,190,255),
                            [(tx3,mcy+mh//2-2),(tx3+tw5-6,mcy+mh//2-2),(tx3+(tw5-6)//2,mcy+mh//2-2-th2)])

                    # vết nứt
                    rng3 = random.Random(99)
                    for _ in range(5):
                        cx3 = fc+rng3.randint(-br2//2,br2//2)
                        cy3 = fc+rng3.randint(-br2//2,br2//2)
                        cl  = rng3.randint(br2//6,br2//3)
                        ca  = rng3.uniform(0,math.pi)
                        pygame.draw.line(face,(60,0,0,200),(cx3,cy3),
                            (cx3+int(math.cos(ca)*cl),cy3+int(math.sin(ca)*cl)),2)

                    self.screen.blit(face,(SCREEN_WIDTH//2-cs//2+shake_x,
                                          SCREEN_HEIGHT//2-cs//2+shake_y))

                    # overlay đỏ đập nhịp
                    ov = pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT),pygame.SRCALPHA)
                    ov.fill((160,0,0,int(40+abs(math.sin(t*0.5))*80)))
                    self.screen.blit(ov,(0,0))

                    # scan lines
                    if t < 30:
                        for sy2 in range(0,SCREEN_HEIGHT,4):
                            pygame.draw.line(self.screen,(0,0,0),(0,sy2),(SCREEN_WIDTH,sy2),1)

                # Phase 3: đỏ máu + text (51+)
                else:
                    self.jumpscare_phase = "dead"
                    fade_t = min(1.0,(t-51)/15.0)
                    self.screen.fill((int(60+100*fade_t),0,0))
                    if t < 70:
                        for _ in range(100):
                            self.screen.set_at(
                                (random.randint(0,SCREEN_WIDTH-1),
                                 random.randint(0,SCREEN_HEIGHT-1)),
                                (random.randint(80,160),0,0))
                    if t > 62:
                        a2 = min(255,int((t-62)*14))
                        js_s = self.title_font.render("YOU GOT CAUGHT!",True,(0,0,0))
                        pr_s = self.font.render("SPACE: Respawn  |  ESC: Menu",True,(0,0,0))
                        js_s.set_alpha(a2); pr_s.set_alpha(a2)
                        self.screen.blit(js_s,(SCREEN_WIDTH//2-js_s.get_width()//2,SCREEN_HEIGHT//2-50))
                        self.screen.blit(pr_s,(SCREEN_WIDTH//2-pr_s.get_width()//2,SCREEN_HEIGHT//2+20))

            elif self.state == "VICTORY_SCREEN":
                self.screen.fill((20,40,20))
                vt = self.title_font.render("VICTORY! ESCAPED", True, YELLOW)
                pr = self.font.render("SPACE/ESC -> Main Menu", True, WHITE)
                self.screen.blit(vt,(SCREEN_WIDTH//2-vt.get_width()//2, SCREEN_HEIGHT//2-50))
                self.screen.blit(pr,(SCREEN_WIDTH//2-pr.get_width()//2, SCREEN_HEIGHT//2+20))

            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = GameEngine()
    game.run()
