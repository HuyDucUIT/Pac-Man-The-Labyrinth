"""
entities/boss.py
------------------
Ghost — đối thủ dạng máy trạng thái
hữu hạn (Finite State Machine) 4 trạng thái: ROAM (lang thang), INVESTIGATE
(đi kiểm tra tiếng động), SMELL_SEARCH (lùng theo mùi), CHASE (truy đuổi).
Ba giác quan Nghe/Nhìn/Ngửi được mở dần theo cấp độ (level) người chơi chọn.
Phần vẽ (draw, get_hand_world_positions) dựng hình thủ tục (procedural) một
nhân dạng đang bước đi với tay vươn về phía trước.
"""

import math
import random

import pygame

from core.game_object import Entity
from config.settings import SCREEN_WIDTH, TILE, BOSS_RED


class Ghost(Entity):
    """Đối thủ dạng FSM 4 trạng thái (ROAM/INVESTIGATE/SMELL_SEARCH/CHASE) với 3 giác quan Nghe/Nhìn/Ngửi mở dần theo cấp độ."""
    def __init__(self, x, y, level):
        """Khởi tạo Ghost tại (x, y) theo cấp độ `level`: bật/tắt các giác quan can_hear/can_see/can_smell tương ứng, trạng thái FSM ban đầu là ROAM."""
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
        """Ghi đè trực tiếp 3 giác quan (dùng riêng cho màn 5, khi người chơi lần lượt mở khoá kỹ năng Boss qua từng Artifact)."""
        self.can_hear              = hear
        self.can_see               = see
        self.can_see_through_walls = see
        self.can_smell             = smell

    def update(self, player, walls, map_w, map_h, gs):
        """Hàm cập nhật chính mỗi khung hình: kiểm tra điều kiện chuyển trạng thái FSM (thấy/nghe/ngửi thấy người chơi), sau đó gọi _move_to() để di chuyển theo trạng thái hiện tại và giới hạn Boss trong biên bản đồ."""
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
                nx = random.randint(TILE * 3, map_w - TILE * 4)
                ny = random.randint(TILE * 3, map_h - TILE * 4)
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
        """Kiểm tra đường ngắm (line-of-sight) tới người chơi bằng cách dò từng điểm trên đoạn thẳng nối hai tâm, trả về False nếu bị tường chắn. Nếu Boss đã có khả năng nhìn xuyên tường thì luôn trả về True."""
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
        """Được AudioMixin gọi khi có tiếng động phát ra; nếu Boss có thể nghe và không đang CHASE, chuyển sang INVESTIGATE và ghi nhớ vị trí phát ra tiếng động."""
        if self.can_hear and self.state != "CHASE":
            if math.hypot(x-self.rect.centerx, y-self.rect.centery) <= radius*noise_mod:
                self.state = "INVESTIGATE"
                self.target_pos = (x, y)

    def _move_to(self, walls, ignore, gs):
        """Di chuyển Boss về phía target_pos theo nhịp bước chân (move/pause frames) và tốc độ nhân hệ số riêng cho từng trạng thái FSM, đồng thời phát âm thanh bước chân theo khoảng cách tới người chơi."""
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
        """Tính toạ độ thế giới của hai bàn tay Boss (dùng khi vẽ hiệu ứng tay vươn ra tóm người chơi lúc jumpscare)."""
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
        """Đẩy Boss và entity khác (thường là Player) ra xa nhau nếu khoảng cách nhỏ hơn bán kính tối thiểu, tránh việc hai hình tròn chồng lấn."""
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
        """Dựng hình thủ tục (procedural) toàn bộ nhân dạng Boss: thân, mắt, miệng răng nanh và hai tay vươn theo nhịp bước đi, vẽ lên một canvas tạm rồi blit vào surface chính."""
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
                (ecx-eye_r, eye_y3-int(eye_r*1.1), eye_r*2, int(eye_r*2.8)))
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
