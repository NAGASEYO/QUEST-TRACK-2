# art/sheet.png (2줄 2칸) 을 잘라서 frames/1.png ~ 4.png 로 저장한다.
# 실행: .venv\Scripts\python.exe cut_frames.py
from pathlib import Path

from PIL import Image

HERE = Path(__file__).parent
SHEET = HERE / "art" / "sheet.png"
OUT = HERE / "frames"

SIZE = 160         # 완성 그림 한 변 (픽셀)
FAINT = 64         # 이보다 옅은 점은 잡티로 보고 지운다 (0~255)

# 칸 순서 → 저장할 번호 (① 만세, ② 한 손, ③ 반대 손, ④ 눈 감음)
CELLS = {1: (0, 0), 2: (0, 1), 3: (1, 0), 4: (1, 1)}


def main():
    sheet = Image.open(SHEET).convert("RGBA")
    cell = sheet.width // 2

    # 옅은 잡티 지우기
    alpha = sheet.getchannel("A").point(lambda a: 0 if a < FAINT else a)
    sheet.putalpha(alpha)

    cells = {n: sheet.crop((c * cell, r * cell, (c + 1) * cell, (r + 1) * cell))
             for n, (r, c) in CELLS.items()}

    # 4장을 모두 같은 네모로 잘라야 바꿔 보여 줄 때 패드가 흔들리지 않는다
    boxes = [img.getbbox() for img in cells.values()]
    box = (min(b[0] for b in boxes), min(b[1] for b in boxes),
           max(b[2] for b in boxes), max(b[3] for b in boxes))

    OUT.mkdir(exist_ok=True)
    for n, img in cells.items():
        cat = img.crop(box)
        scale = SIZE / max(cat.size)
        cat = cat.resize((round(cat.width * scale), round(cat.height * scale)), Image.LANCZOS)

        # 가로 가운데, 아래쪽에 붙인다 (작업표시줄 위에 앉아 있게)
        frame = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        frame.paste(cat, ((SIZE - cat.width) // 2, SIZE - cat.height))
        frame.save(OUT / f"{n}.png")
        print(f"frames/{n}.png 저장")


if __name__ == "__main__":
    main()
