"""
main.py
--------
Điểm khởi chạy (entry point) của trò chơi. Toàn bộ logic thật sự nằm trong
package engine/ (GameEngine đa kế thừa 4 Mixin); main.py chỉ có nhiệm vụ
khởi tạo và chạy vòng lặp chính.
"""

from engine.game_engine import GameEngine

if __name__ == "__main__":
    game = GameEngine()
    game.run()
