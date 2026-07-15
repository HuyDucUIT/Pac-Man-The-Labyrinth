# 👻 PAC-MAN: The Labyrinth
**Đồ án môn Lập trình Hướng Đối Tượng (OOP) - UIT**

![Pac-Man Survival](https://img.shields.io/badge/Status-In%20Development-yellow)
![Python](https://img.shields.io/badge/Python-3.x-blue)
![Pygame](https://img.shields.io/badge/Library-Pygame-green)

Pac-Man Survival là một dự án mở rộng từ tựa game Arcade kinh điển, đưa người chơi vào một trải nghiệm **Survival Horror**. Người chơi bị tước đi tầm nhìn bởi hệ thống sương mù, phải tìm các vật mục tiêu trong bóng tối và lẩn trốn sự truy đuổi của những con ma có khả năng Nghe, Nhìn và Đánh hơi.

---

## 📖 MỤC LỤC
1. [Luật chơi & Cơ chế cốt lõi](#1-luật-chơi--cơ-chế-cốt-lõi)
2. [Hệ thống Giác quan của Boss (AI)](#2-hệ-thống-giác-quan-của-boss-ai)
3. [Chỉ số người chơi & Cửa hàng](#3-chỉ-số-người-chơi--cửa-hàng-maze-shop)

---

## 1. LUẬT CHƠI & CƠ CHẾ CỐT LÕI
* **Tiến trình tuyến tính:** Game gồm 4 căn phòng tiêu chuẩn (Màn 1 -> Màn 4) và 1 phòng Đặc biệt (Màn 5). Người chơi phải tìm và kích hoạt đủ số lượng Cần gạt / Nút bấm theo yêu cầu để mở Cửa Xanh qua phòng tiếp theo.
* **Bóng tối & Ánh sáng (Fog of War):** Màn hình bị bao phủ bởi bóng tối. Đứng trong bóng tối (`is_hidden = True`) là cách duy nhất để tránh bị khóa mục tiêu. Cầm Nến giúp mở rộng tầm nhìn nhưng sẽ làm lộ vị trí.
* **Ambient Glow:** Các vật thể quan trọng (Hạt tiền, Nến, Ghi chú) sẽ phát ra quầng sáng nhỏ hoặc đục lỗ sương mù để định hướng trong đêm.
* **Kinh tế:** Số lượng hạt tiền (Dots) tăng dần theo từng màn (30, 40, 50, 60 hạt cho các màn 1-4). 1 Hạt = 10 Xu. Tối đa kiếm được khoảng 1800 Xu trước khi bước vào màn cuối.

---

## 2. HỆ THỐNG GIÁC QUAN CỦA BOSS (AI)
Ghost có tốc độ di chuyển mặc định là **3.5 px/frame** và **có thể đi xuyên tường** khi rơi vào trạng thái truy đuổi (`CHASE`). Thử thách tăng dần qua từng màn:
* **Màn 1:** Boss chỉ có thể đi lang thang vô định (`ROAM`).
* **Màn 2:** Có khả năng Nghe.
* **Màn 3:** Khả năng Nghe + Nhìn.
* **Màn 4:** Nghe + Nhìn + Ngửi + Xuất hiện 2 Boss cùng lúc.

### Thông số Giác quan (Sensory Stats)
| Giác quan | Bán kính kích hoạt | Cơ chế hoạt động (State Machine) |
| :--- | :--- | :--- |
| 👂 **Nghe (Hear)** | **10 Tiles** (Hạt)<br>**Toàn bản đồ** (Cần gạt/Nút) | Khi có tiếng động, Boss lưu "Last Known Location" và tới kiểm tra (`INVESTIGATE`). Tới nơi không thấy ai sẽ đi lang thang (`ROAM`). |
| 👁️ **Nhìn (See)** | **8 Tiles** | Chỉ kích hoạt nếu Pac-man đứng trong sáng (`is_hidden = False`). Ghost sẽ khóa thẳng mục tiêu (`CHASE`). |
| 👃 **Ngửi (Smell)**| **3.5 Tiles** | Dù Pac-Man có trốn trong bóng tối tuyệt đối, nếu Ghost đi tuần ngang qua sát vách (3.5 ô), nó sẽ đánh hơi thấy (`SMELL_SEARCH`), lùng sục quanh khu vực đó trong 1 khoảng thời gian. |

### Màn cuối đặc biệt (Màn 5):
Nhiệm vụ của người chơi là nhặt 4 vật phẩm đặc biệt (Artifacts) ở 4 góc bản đồ và mang về bàn thờ trung tâm. Mỗi lần đặt thành công 1 vật phẩm, Boss sẽ được "tiến hóa" (Buff):
* **Vật 1:** Mở khóa khả năng **Nghe**.
* **Vật 2:** Mở khóa khả năng **Nhìn**.
* **Vật 3:** Mở khóa khả năng **Ngửi**.
* **Vật 4:** Nhốt người chơi và Ghost trong phòng trung tâm. Người chơi phải **sống sót sinh tồn trong 30 giây** để giành chiến thắng.

---

## 3. CHỈ SỐ NGƯỜI CHƠI & CỬA HÀNG (MAZE SHOP)
Tốc độ cơ bản của Pac-Man là **2.3 px/frame** (Chậm hơn Boss). Tầm nhìn cơ bản của Nến là **6 Tiles**. Người chơi phải mạo hiểm đi nhặt hạt tiền (phát ra tiếng ồn) để lấy xu nâng cấp trong Cửa hàng (xuất hiện qua Cánh cửa Gỗ ở hành lang an toàn).

### Bảng giá Nâng cấp (Maze Shop)
| Vật phẩm / Nâng cấp | Chỉ số Thay đổi | Giới hạn | Giá tiền |
| :--- | :--- | :---: | :---: |
| 👟 **Tốc độ Cấp 1** | Tăng lên **2.875 px/frame** | 1 | **90 xu** |
| 👟 **Tốc độ Cấp 2** | Tăng lên **3.45 px/frame** (~ Bằng Boss) | 1 | **140 xu** |
| 👟 **Tốc độ Cấp 3** | Tăng lên **4.025 px/frame** (Nhanh hơn Boss) | 1 | **190 xu** |
| 👟 **Tốc độ Cấp 4** | Tăng lên **4.6 px/frame** (Tốc độ tối đa) | 1 | **250 xu** |
| 🕯️ **Nâng cấp Nến** | Bán kính tầm nhìn tăng từ 6 -> **7.2 Tiles** (+20%) | 1 | **110 xu** |
| 🔇 **Giảm ồn (Muffler)**| Âm thanh ăn hạt giảm từ 10 -> **8.0 Tiles** (-20%) | 1 | **120 xu** |
| 🥷 **Khử mùi (Stealth)**| Bán kính ngửi của Boss bị giảm còn **80%** | 1 | **150 xu** |
