# 👻 PAC-MAN: The Labyrinth 
**Đồ án môn Lập trình Hướng Đối Tượng (OOP) - UIT**

![Pac-Man Survival](https://img.shields.io/badge/Status-In%20Development-yellow)
![Python](https://img.shields.io/badge/Python-3.x-blue)
![Pygame](https://img.shields.io/badge/Library-Pygame-green)

Pac-Man Survival là một dự án mở rộng từ tựa game Arcade kinh điển, đưa người chơi vào một trải nghiệm **Survival Horror (Kinh dị sinh tồn)**. Người chơi bị tước đi tầm nhìn bởi hệ thống sương mù (Fog of War), phải giải các câu đố trong bóng tối và lẩn trốn sự truy đuổi của những con ma có khả năng Nghe, Nhìn và Đánh hơi xuyên tường.

---

## 📖 MỤC LỤC
1. [Luật chơi & Cơ chế cốt lõi](#1-luật-chơi--cơ-chế-cốt-lõi)
2. [Hệ thống Giác quan của Boss (AI)](#2-hệ-thống-giác-quan-của-boss-ai)
3. [Chỉ số người chơi & Cửa hàng](#3-chỉ-số-người-chơi--cửa-hàng-maze-shop)
4. [Cấu trúc Mã nguồn (Project Architecture)](#4-cấu-trúc-mã-nguồn-project-architecture)
5. [Phân công Nhiệm vụ (Task Assignment)](#5-phân-công-nhiệm-vụ-task-assignment)

---

## 1. LUẬT CHƠI & CƠ CHẾ CỐT LÕI
* **Tiến trình tuyến tính:** Game gồm 4 căn phòng (Màn 1 -> Màn 4). Người chơi phải tìm chìa khóa hoặc gạt đủ cần gạt để mở cửa qua phòng tiếp theo. Không thể quay lại phòng cũ (No Backtracking).
* **Bóng tối & Ánh sáng (Fog of War):** Màn hình bị bao phủ bởi bóng tối. Đứng trong bóng tối (`is_hidden = True`) là cách duy nhất để tránh bị khóa mục tiêu. Nến giúp mở rộng tầm nhìn nhưng sẽ làm lộ vị trí.
* **Ambient Glow:** Các vật thể quan trọng (Hạt tiền, Cửa, Cần gạt) sẽ phát ra quầng sáng siêu nhỏ (Bán kính 1 Tile) để định hướng trong đêm.
* **Kinh tế (Dot Economy):** Mỗi phòng có tối đa **20 hạt tiền (Dots)**. 1 Hạt = 10 Xu. Tối đa kiếm được 600 Xu trước màn cuối. 
* **Cơ chế Reset (Anti-Cheese):** Tính năng "Start Over" (Nhấn ESC) sẽ đưa người chơi về màn 1 và **Reset toàn bộ tiền xu** về 0.

---

## 2. HỆ THỐNG GIÁC QUAN CỦA BOSS (AI)
Trùm (Stalker Boss) có tốc độ di chuyển mặc định là **3.5 px/frame** và **có thể đi xuyên tường** khi truy đuổi. Thử thách tăng dần qua từng màn:
* **Màn 1:** Chỉ có thể di chuyển.
* **Màn 2:** Nghe.
* **Màn 3:** Nghe + Nhìn.
* **Màn 4:** Nghe + Nhìn + Ngửi + Xuất hiện 2 Boss cùng lúc
* **Màn 5:** Nghe + Nhìn + Ngửi + Xuất hiện 2 Boss cùng lúc + Chết

### Thông số Giác quan (Sensory Stats)
| Giác quan | Bán kính kích hoạt | Cơ chế hoạt động (State Machine) |
| :--- | :--- | :--- |
| 👂 **Nghe (Hear)** | **10 Tiles** (Hạt)<br>**20 Tiles** (Cần gạt) | Khi có tiếng động, Boss lưu "Last Known Location" và đâm xuyên tường tới kiểm tra (`INVESTIGATE`). Tới nơi không thấy ai sẽ đi lang thang (`WANDER`). |
| 👁️ **Nhìn (See)** | **8 Tiles** | Chỉ kích hoạt nếu Pac-man đứng ngoài sáng (`is_hidden = False`) và không bị tường che (Line of Sight). Boss sẽ khóa thẳng mục tiêu (`CHASE`). |
| 👃 **Ngửi (Smell)**| **3.5 Tiles** | Dù Pac-man có trốn trong bóng tối tuyệt đối, nếu Boss đi tuần ngang qua sát vách (3.5 ô), nó sẽ đánh hơi thấy, đi chậm lại và lùng sục quanh khu vực đó. |

### Màn cuối đặc biệt (màn 5):
* Lụm 4 vật đặc biệt bỏ vào phòng trung tâm, sau khi lụm từng vật đặc biệt, boss sẽ được buff:
* Vật 1: Boss sẽ Nghe được
* Vật 2: Boss sẽ Nhìn được
* Vật 3: Boss sẽ Ngửi được
* Vật 4: Sinh thêm boss thứ 2
* Sau khi lụm hết, sống sót trong phòng trung tâm cho đến khi boss chết -> End game.
---

## 3. CHỈ SỐ NGƯỜI CHƠI & CỬA HÀNG (MAZE SHOP)
Tốc độ cơ bản của Pac-Man là **2.0 px/frame** (Chậm hơn Boss 1.75 lần). Tầm nhìn cơ bản của Nến là **6 Tiles**. Người chơi phải mạo hiểm ăn hạt (gây tiếng ồn) để lấy xu nâng cấp sinh tồn.

### Bảng giá Nâng cấp (Maze Shop)
| Vật phẩm / Nâng cấp | Chỉ số Thay đổi | Giới hạn | Giá tiền |
| :--- | :--- | :---: | :---: |
| 👟 **Tốc độ Cấp 1** | Tăng lên **2.5 px/frame** | 1 | **60 xu** |
| 👟 **Tốc độ Cấp 2** | Tăng lên **3.0 px/frame** | 1 | **110 xu** |
| 👟 **Tốc độ Cấp 3** | Tăng lên **3.5 px/frame** (Bằng Boss) | 1 | **160 xu** |
| 👟 **Tốc độ Cấp 4** | Tăng lên **4.0 px/frame** (Nhanh hơn Boss) | 1 | **220 xu** |
| 🕯️ **Tầm nhìn Nến** | Bán kính sáng tăng từ 6 -> **7.2 Tiles** (+20%) | 1 | **80 xu** |
| 🔇 **Giảm ồn (Muffler)**| Âm thanh ăn hạt giảm từ 10 -> **8 Tiles** (-20%) | 1 | **90 xu** |
| 🥷 **Khử mùi (Stealth)**| Bán kính ngửi của Boss giảm từ 3.5 -> **2.8 Tiles** (-20%)| 1 | **120 xu** |

---

## 4. CẤU TRÚC MÃ NGUỒN (PROJECT ARCHITECTURE)
Dự án áp dụng thiết kế OOP và tách rời module (Loose Coupling) để tiện làm việc nhóm.

```text
PACMAN-SURVIVAL/
│
├── main.py                  # Điểm khởi chạy (Game Loop Entry)
│
├── core/                    # HỆ THỐNG CỐT LÕI
│   ├── constants.py         # Hằng số (Kích thước, Màu sắc, Stats, Giá tiền)
│   ├── game.py              # FSM (State Machine: Start, Playing, Pause, Shop)
│   ├── map.py               # Xử lý Map 2 Lớp (Tile Layer tĩnh & Object Layer động)
│   └── room_manager.py      # Nạp/Giải phóng bộ nhớ khi chuyển màn
│
├── entities/                # THỰC THỂ & AI
│   ├── entity.py            # Lớp trừu tượng quản lý pixel-movement & collision
│   ├── pacman.py            # Player (Xử lý vận tốc, is_hidden, has_candle)
│   └── stalker_ghost.py     # Boss AI (Thuật toán truy vết Hear/See/Smell)
│
├── interactables/           # VẬT THỂ TƯƠNG TÁC (Đa hình)
│   ├── base.py              # Lớp Interactable gốc (interact())
│   ├── items.py             # Candle (Nến đất), Dot (Hạt tiền)
│   ├── puzzle.py            # Switch (Cần gạt), Note (Manh mối)
│   └── door.py              # Cánh cửa (Trigger chuyển màn / Prompt)
│
├── systems/                 # LOGIC HỆ THỐNG NGẦM
│   ├── objectives.py        # Quản lý tiến trình (Đếm cần gạt, cấp quyền mở cửa)
│   ├── player_state.py      # Global config (Tiền xu, Cấp độ nâng cấp hiện tại)
│   └── sound.py             # Quản lý luồng âm thanh kinh dị
│
└── ui/                      # ĐỒ HỌA & GIAO DIỆN
    ├── lighting.py          # Xử lý Fog of War (BLEND_RGBA_SUB) & Đục lỗ ánh sáng
    ├── hud.py               # HUD, Prompt chỉ dẫn ("Nhấn E để gạt")
    └── shop_maze.py         # Giao diện nâng cấp Shop
```
