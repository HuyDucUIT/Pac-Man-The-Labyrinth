"""
engine/audio_manager.py
--------------------------
AudioMixin — một trong 4 Mixin được GameEngine đa kế thừa, đảm nhiệm riêng
phần âm lượng hiệu ứng và lan truyền tiếng động trong game. Tách biệt khỏi
LevelManagerMixin/EventHandlerMixin/RendererMixin theo nguyên tắc SRP: mọi
logic liên quan tới "âm thanh" chỉ nằm ở một file duy nhất.
"""


class AudioMixin:
    """Quản lý âm lượng hiệu ứng và lan truyền tiếng động (make_noise) tới các Ghost."""

    def _update_volume(self):
        """Tính lại âm lượng thực tế cho từng hiệu ứng (step, lever, button, grab, bell, dead) dựa trên global_volume, mỗi loại có hệ số riêng."""
        ov = self.global_volume * 0.8
        if self.sfx_step:   self.sfx_step.set_volume(ov * 0.3)
        if self.sfx_lever:  self.sfx_lever.set_volume(ov * 0.54 * 0.9)
        if self.sfx_button: self.sfx_button.set_volume(ov * 0.48 * 0.5)
        if self.sfx_grab:   self.sfx_grab.set_volume(ov * 0.64)
        if self.sfx_bell:   self.sfx_bell.set_volume(ov * 0.77)
        if self.sfx_dead:   self.sfx_dead.set_volume(ov * 1.0) # Thêm volume cho dead monster

    def make_noise(self, x, y, radius, is_loud):
        """Kích hoạt hiệu ứng hình (nhấp nháy icon loa) và lan truyền tiếng động tới toàn bộ self.bosses; nếu is_loud=True thì rung màn hình và tiếng vang khắp bản đồ (radius vô hạn)."""
        self.speaker_flash_timer = 60
        self.speaker_flash_loud  = is_loud
        if is_loud:
            self.shake_intensity = 30
            radius = 999999
        for b in self.bosses:
            b.hear_noise(x, y, radius, 1.0)
