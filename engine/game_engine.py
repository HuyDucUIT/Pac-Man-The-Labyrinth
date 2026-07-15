"""
engine/game_engine.py
------------------------
GameEngine — lớp điều phối trung tâm của toàn bộ trò chơi. Áp dụng kỹ thuật
Mixin (đa kế thừa có chủ đích): thay vì nhồi mọi logic vào một class khổng
lồ, GameEngine kế thừa từ 4 Mixin chuyên trách riêng biệt:

    LevelManagerMixin  — sinh bản đồ, spawn thực thể, reset màn chơi
    EventHandlerMixin  — đọc input, chuyển đổi state, mua nâng cấp
    AudioMixin         — âm lượng và lan truyền tiếng động
    RendererMixin      — mọi hàm vẽ (bản đồ, sương mù, HUD, Shop)

Bản thân GameEngine chỉ còn giữ lại đúng 4 việc cốt lõi: khởi tạo tài nguyên
(__init__), cập nhật logic mỗi khung hình (update), tính trạng thái ẩn/lộ của
người chơi (_update_player_visibility), và vòng lặp chính (run) — nơi vẽ toàn
bộ giao diện theo state hiện tại rồi lật khung hình lên màn hình.
"""

import math
import random
import sys

import pygame

from config.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, GAME_WIDTH, GAME_HEIGHT,
    TILE, FPS, BLACK, WHITE, GRAY, RED, YELLOW, GREEN, DARK_GRAY, MAGENTA,
)
from core.asset_loader import load_sprite_scaled, load_font, load_img, load_sound
from core.camera import Camera
from entities.player_stats import PlayerStats
from objects.items import Dot, Candle, Note, Artifact, UnpickableCandle
from objects.mechanisms import Lever, ButtonInteract
from objects.doors import GreenDoor, WoodenDoor

from engine.level_manager import LevelManagerMixin
from engine.event_handler import EventHandlerMixin
from engine.audio_manager import AudioMixin
from engine.renderer import RendererMixin


class GameEngine(LevelManagerMixin, EventHandlerMixin, AudioMixin, RendererMixin):
    """
    Lớp điều phối trung tâm: đa kế thừa 4 Mixin (sinh màn, sự kiện, âm thanh,
    vẽ) và tự giữ lại 4 việc cốt lõi (khởi tạo, update, tính is_hidden, vòng
    lặp run chính của trò chơi).
    """

    def __init__(self):
        """Khởi tạo pygame/mixer, cửa sổ, các surface vẽ (game_surface, fog), toàn bộ sprite/font/âm thanh (qua asset_loader), chỉ số người chơi ban đầu, các nút bấm Menu/Pause, thanh âm lượng, và các biến trạng thái hiệu ứng (rung màn hình, tay Boss tóm, popup buff, jumpscare)."""
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
        
        # --- Main Menu Buttons ---
        self.btn_labyrinth = pygame.Rect(SCREEN_WIDTH//2-150, 350, 300, 50)
        self.btn_choose    = pygame.Rect(SCREEN_WIDTH//2-150, 420, 300, 50)
        self.btn_lvls      = [
            pygame.Rect(SCREEN_WIDTH//2-190, 490, 60, 50),
            pygame.Rect(SCREEN_WIDTH//2-120, 490, 60, 50),
            pygame.Rect(SCREEN_WIDTH//2-50,  490, 60, 50),
            pygame.Rect(SCREEN_WIDTH//2+20,  490, 60, 50),
            pygame.Rect(SCREEN_WIDTH//2+90,  490, 100, 50),
        ]
        
        # --- Pause Menu Buttons ---
        self.btn_continue  = pygame.Rect(SCREEN_WIDTH//2-150, 360, 300, 50)
        self.btn_exit_pause= pygame.Rect(SCREEN_WIDTH//2-150, 430, 300, 50)
        
        self.vol_rect      = pygame.Rect(SCREEN_WIDTH//2-150, 520, 300, 20)
        self.global_volume = 1.0
        self._update_volume()

        self.buff_popup_text  = []
        self.buff_popup_timer = 0

        self.jumpscare_timer = 0
        self.jumpscare_phase = "flash"

    def update(self):
        """Cập nhật logic một khung hình khi self.state == 'PLAYING': di chuyển Player, xử lý tương tác Dot/Artifact/ButtonInteract khi chạm, dọn vật phẩm đã dùng, cập nhật từng Ghost (kể cả kiểm tra va chạm/tóm người chơi dẫn tới JUMPSCARE), hoà trộn nhạc nền theo trạng thái truy đuổi, và kiểm tra điều kiện mở GreenDoor hoặc kích hoạt/thắng màn Boss (màn 5)."""
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
                elif isinstance(item,Artifact) and item.active \
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
                    self.shake_intensity  = 40

                if self.m5_items_placed == 4:
                    self.m5_survival_timer -= 1
                    if self.m5_survival_timer <= 0:
                        self.state = "VICTORY_SCREEN"

    def _update_player_visibility(self):
        """Tính cờ player.is_hidden dựa trên nhiều điều kiện theo thứ tự ưu tiên: đang cầm nến (luôn lộ), đứng gần UnpickableCandle ở hành lang, đứng gần bàn thờ ở màn 5, hoặc đứng trong bán kính chiếu sáng của Candle/Note/Artifact đang active trong màn chơi hiện tại."""
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
            if isinstance(item, Artifact) and item.active:
                d = math.hypot(px - item.rect.centerx, py - item.rect.centery)
                if d <= 3 * TILE:
                    self.player.is_hidden = False
                    return
        self.player.is_hidden = True

    def run(self):
        """Vòng lặp chính của trò chơi (game loop): xử lý input, tính hiệu ứng rung màn hình, rồi vẽ toàn bộ giao diện tương ứng với self.state hiện tại (MENU, LEVEL_INTRO, PLAYING/HALLWAY/PAUSED, DOOR_PROMPT, SHOP, JUMPSCARE nhiều pha, VICTORY_SCREEN), cuối cùng lật khung hình lên màn hình và giữ nhịp FPS."""
        while True:
            if self.state == "MENU" and getattr(self, 'show_level_choices', False):
                self.vol_rect.y = 580  # Đẩy thanh volume xuống dưới các nút level
            else:
                self.vol_rect.y = 520  # Trả về vị trí mặc định
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
                
                for btn,lbl in [(self.btn_labyrinth, "Labyrinth Mode"),
                                (self.btn_choose,    "Choose Level")]:
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
