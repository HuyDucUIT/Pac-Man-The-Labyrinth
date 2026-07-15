"""
world/map_generator.py
------------------------
Thuật toán sinh mê cung ngẫu nhiên theo kiểu "Drunkard's Walk" (người say
rượu đi ngẫu nhiên): xuất phát từ tâm bản đồ, đục dần các "chunk" hành lang
theo hướng ngẫu nhiên cho tới khi đạt tỉ lệ diện tích mở mong muốn (tăng theo
cấp độ level). Riêng màn 5 (Boss) còn khoét thêm một phòng trung tâm vuông
với 4 cổng ra vào.
"""

import random

import pygame

from config.settings import TILE, MIN_HALL


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
