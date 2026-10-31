# 냥 패드 펫
# 실행: .venv\Scripts\python.exe pet.py
import signal
import sys
import time
from collections import deque
from pathlib import Path

from pynput import keyboard
from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QMenu, QWidget

# exe 로 묶어서 실행하면 그림이 임시 폴더(sys._MEIPASS)에 풀리므로 거기서 찾는다
HERE = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
FRAMES = HERE / "frames"

SIZE = 160         # 펫 크기 (cut_frames.py 의 SIZE 와 같아야 함)
MARGIN = 16        # 화면 오른쪽 끝과 펫 사이 거리 (픽셀)
COUNT_H = 24       # 펫 아래 횟수 글자 칸 높이 (픽셀)

# 움직임 규칙 (바꾸고 싶으면 여기 숫자만 고치면 된다)
USE_CHEER = False  # True 로 바꾸면 빨리 칠 때 ① 만세가 나온다
FAST_PRESSES = 6   # 1초 동안 이만큼 이상 누르면 ① 만세 (USE_CHEER 가 True 일 때만)
REST_SECONDS = 3   # 이만큼 안 누르면 ④ 쉬기

# 그림 번호
CHEER, PAW_A, PAW_B, REST = 1, 2, 3, 4


class KeyCounter(QObject):
    """다른 창에서 키가 눌린 것을 알아차리고 pressed 신호만 보낸다.

    어떤 키인지는 받자마자 버린다. 저장도 전송도 화면 출력도 하지 않는다.
    """
    pressed = Signal()

    def __init__(self):
        super().__init__()
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.daemon = True

    def on_press(self, *_):
        # pynput 이 넘겨주는 키 값(_)은 쓰지 않는다. "눌렸다"는 신호만 보낸다.
        self.pressed.emit()

    def start(self):
        self.listener.start()

    def stop(self):
        self.listener.stop()


class Pet(QWidget):
    def __init__(self):
        super().__init__()
        # 테두리 없음 · 항상 위 · 작업표시줄에 버튼 안 생김
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        # 고양이 말고 나머지는 투명하게
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.frames = {n: QPixmap(str(FRAMES / f"{n}.png")) for n in range(1, 5)}

        self.picture = QLabel(self)
        self.picture.setFixedSize(SIZE, SIZE)

        # 고양이 아래 횟수 글자
        self.count = 0
        self.count_label = QLabel(self)
        self.count_label.setGeometry(0, SIZE, SIZE, COUNT_H)
        self.count_label.setAlignment(Qt.AlignCenter)
        self.count_label.setStyleSheet(
            "color: white; background: rgba(0, 0, 0, 150); border-radius: 8px;"
            "font-size: 13px; font-weight: bold;")

        self.setFixedSize(SIZE, SIZE + COUNT_H)

        self.drag_offset = None   # 끄는 중일 때, 마우스와 펫 왼쪽 위 모서리 사이 거리

        self.recent = deque()     # 최근 1초 안에 눌린 "시각"들 (어떤 키인지는 없음)
        self.next_paw = PAW_A     # 다음에 보여 줄 손 (② ↔ ③ 번갈아)

        # REST_SECONDS 동안 키가 없으면 ④ 로 바꾸는 타이머. 키가 눌릴 때마다 처음부터 다시 잰다
        self.rest_timer = QTimer(self)
        self.rest_timer.setSingleShot(True)
        self.rest_timer.setInterval(REST_SECONDS * 1000)
        self.rest_timer.timeout.connect(lambda: self.show_frame(REST))

        self.show_frame(REST)
        self.show_count()
        self.move_to_corner()

    def show_frame(self, n):
        self.frame = n
        self.picture.setPixmap(self.frames[n])

    def show_count(self):
        self.count_label.setText(f"오늘 {self.count:,}")

    def on_key(self):
        self.count += 1
        self.show_count()

        # 1초보다 오래된 시각은 버리고, 남은 개수로 빠르기를 잰다
        now = time.monotonic()
        self.recent.append(now)
        while now - self.recent[0] > 1:
            self.recent.popleft()

        if USE_CHEER and len(self.recent) >= FAST_PRESSES:
            self.show_frame(CHEER)
        else:
            self.show_frame(self.next_paw)
            self.next_paw = PAW_B if self.next_paw == PAW_A else PAW_A

        self.rest_timer.start()

    def move_to_corner(self):
        # availableGeometry 는 작업표시줄을 뺀 화면 크기라서, 아래에 붙여도 작업표시줄을 가리지 않는다
        area = QApplication.primaryScreen().availableGeometry()
        self.move(area.right() - self.width() - MARGIN + 1, area.bottom() - self.height() + 1)

    # 왼쪽 버튼으로 끌어서 옮기기
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_offset = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        if self.drag_offset is not None:
            self.move(event.globalPosition().toPoint() - self.drag_offset)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_offset = None

    # 오른쪽 클릭 메뉴
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.addAction("끄기", QApplication.quit)
        menu.exec(event.globalPos())


def main():
    # 실행한 창에서 Ctrl+C 로도 끌 수 있게 한다
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    pet = Pet()

    # 키 듣기는 따로 돌아가므로, 신호로 받아서 펫 숫자를 올린다
    counter = KeyCounter()
    counter.pressed.connect(pet.on_key)
    counter.start()
    app.aboutToQuit.connect(counter.stop)

    pet.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
