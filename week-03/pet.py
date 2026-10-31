# 냥 패드 펫
# 실행: .venv\Scripts\python.exe pet.py
import signal
import sys
from pathlib import Path

from pynput import keyboard
from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QMenu, QWidget

HERE = Path(__file__).parent
FRAMES = HERE / "frames"

SIZE = 160         # 펫 크기 (cut_frames.py 의 SIZE 와 같아야 함)
MARGIN = 16        # 화면 오른쪽 끝과 펫 사이 거리 (픽셀)
COUNT_H = 24       # 펫 아래 횟수 글자 칸 높이 (픽셀)


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

        self.show_frame(4)
        self.show_count()
        self.move_to_corner()

    def show_frame(self, n):
        self.picture.setPixmap(self.frames[n])

    def show_count(self):
        self.count_label.setText(f"오늘 {self.count:,}")

    def add_one(self):
        self.count += 1
        self.show_count()

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
    counter.pressed.connect(pet.add_one)
    counter.start()
    app.aboutToQuit.connect(counter.stop)

    pet.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
