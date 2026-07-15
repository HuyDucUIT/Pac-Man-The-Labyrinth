"""
engine/level_manager.py
--------------------------
LevelManagerMixin — một trong 4 Mixin được GameEngine đa kế thừa, đảm nhiệm
sinh bản đồ, spawn (đặt vị trí) mọi thực thể/vật phẩm cho mỗi màn chơi, và
reset trạng thái khi bắt đầu màn mới hoặc khi người chơi chết. Đây là phần
"khởi tạo lại thế giới" — tách khỏi phần "chạy vòng lặp" (GameEngine) và
"vẽ" (RendererMixin) theo nguyên tắc SRP.
"""

import math
import random

import pygame

from config.settings import TILE, BASE_MAP_W, BASE_MAP_H, FPS, GAME_WIDTH
from core.camera import Camera
from world.map_generator import build_level_walls
from entities.player import Player
from entities.player_stats import PlayerStats
from entities.boss import Ghost
from objects.items import Dot, Candle, Note, Artifact, UnpickableCandle
from objects.mechanisms import Lever, ButtonInteract
from objects.doors import Altar, GreenDoor, WoodenDoor


class LevelManagerMixin:
    """Sinh bản đồ, spawn thực thể/vật phẩm, và reset trạng thái màn chơi."""

    def get_valid_spawn_pos(self, obj_w, obj_h):
        """Thử tối đa 500 lần chọn ngẫu nhiên một vị trí (tx, ty) không va chạm tường và không rơi vào vùng cửa chính/phòng trung tâm; trả về TILE*6,TILE*6 nếu không tìm được."""
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
        """Giống get_valid_spawn_pos nhưng đảm bảo vị trí mới cách tất cả các điểm đã có (existing_points) tối thiểu min_dist — dùng để rải đều Lever/Button, tránh dồn cụm."""
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
        """Từ một toạ độ mục tiêu, dò theo hình xoáy ốc (vòng bán kính tăng dần) để tìm ô gần nhất không va chạm tường và nằm trong biên bản đồ."""
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
        """Sinh danh sách tường mới cho self.current_level bằng build_level_walls(), lưu vào self.walls và self.center_room_rect."""
        self.walls, self.center_room_rect = build_level_walls(self.current_level, self.map_w, self.map_h)

    def reset_game(self, next_level=False, keep_stats=False):
        """Thiết lập lại toàn bộ trạng thái cho một màn chơi mới: tính kích thước bản đồ theo hệ số scale của level, sinh tường, tạo Camera/Player/Ghost, rải Dot/Candle/Lever/Button/GreenDoor (hoặc Altar+Artifact riêng cho màn 5), rồi đưa game về trạng thái LEVEL_INTRO."""
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
            b = Ghost(bx, by, self.current_level)
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
                self.interactables.append(Artifact(sx, sy))
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
        """Chuyển sang một 'hành lang an toàn' thu nhỏ (giữa 2 màn) chứa WoodenDoor (vào Shop) và GreenDoor (qua màn kế tiếp), dùng Camera/bản đồ riêng biệt với màn chính."""
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
