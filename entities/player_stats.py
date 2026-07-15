"""
entities/player_stats.py
--------------------------
Toàn bộ chỉ số nâng cấp được của người chơi, tách riêng khỏi lớp Player theo
nguyên tắc Đóng gói (Encapsulation): Player không tự lưu tốc độ/tầm nhìn mà
uỷ quyền (has-a) cho một đối tượng PlayerStats duy nhất. Muốn nâng cấp chỉ số
trong Cửa hàng, GameEngine chỉ thao tác trên player.stats mà không đụng vào
nội bộ Player.
"""


class PlayerStats:
    """Gộp toàn bộ chỉ số có thể nâng cấp của Player (tốc độ, tầm nhìn, tiếng ồn, khử mùi...)."""
    def __init__(self):
        """Khởi tạo các chỉ số mặc định của người chơi: xu, tốc độ, tầm nhìn nến, bán kính tiếng ồn và hệ số mùi (đều có thể nâng cấp qua Cửa hàng)."""
        self.coins          = 0
        self.speed_level    = 0
        self.speed          = 2.3
        self.candle_upgraded= False
        self.vision_radius  = 6.0
        self.muffler_upgraded = False
        self.noise_radius   = 10.0
        self.stealth_upgraded = False
        self.smell_modifier = 1.0
