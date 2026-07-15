"""
engine/event_handler.py
--------------------------
EventHandlerMixin — một trong 4 Mixin được GameEngine đa kế thừa, đảm nhiệm
đọc toàn bộ input (bàn phím, chuột) và chuyển đổi self.state của game theo
đúng máy trạng thái tổng thể (MENU -> LEVEL_INTRO -> PLAYING -> ... xem
Chương 3, mục 3.3). Cũng xử lý việc mua nâng cấp trong Cửa hàng.
"""

import sys

import pygame

from entities.player_stats import PlayerStats
from objects.items import Note, Candle
from objects.mechanisms import Lever
from objects.doors import GreenDoor, WoodenDoor


class EventHandlerMixin:
    """Đọc input bàn phím/chuột, chuyển đổi self.state, và xử lý mua nâng cấp trong Shop."""

    def handle_events(self):
        """Vòng lặp pygame.event.get() chính: xử lý click chuột ở MENU/PAUSED, và các phím tắt theo từng self.state (SPACE ở LEVEL_INTRO, Y/N ở DOOR_PROMPT, mũi tên+ENTER ở SHOP, phím E để tương tác vật thể/nhặt-thả nến ở PLAYING/HALLWAY, ESC để Pause/tiếp tục), đồng thời kéo-thả thanh chỉnh âm lượng bằng chuột."""
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
                                        buff = ["Ghost can HEAR"]
                                    elif self.m5_items_placed==2:
                                        self.m5_see=True
                                        buff = ["Ghost can SEE"]
                                    elif self.m5_items_placed==3:
                                        self.m5_smell=True
                                        buff = ["Ghost can SMELL"]
                                    elif self.m5_items_placed==4:
                                        buff = ["TRAPPED! SURVIVE 30s!"]
                                        
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
        """Trừ xu và áp dụng nâng cấp tương ứng với self.shop_selected_index (tốc độ / tầm nhìn nến / giảm ồn / khử mùi) nếu người chơi đủ xu và chưa mua tối đa."""
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
