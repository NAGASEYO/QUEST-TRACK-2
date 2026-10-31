@echo off
chcp 65001 >nul
rem 냥 패드 펫을 dist\pet.exe 하나로 묶는다
rem 실행: build.bat 을 더블클릭하거나, week-03 폴더에서 build.bat 입력
cd /d "%~dp0"

rem 1. 그림 자르기 (art\sheet.png -> frames\1~4.png)
.venv\Scripts\python.exe cut_frames.py || goto :fail

rem 2. 묶기 (--windowed: 까만 명령 창 없이, --add-data: 그림을 exe 안에 넣기)
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --windowed ^
    --name pet --add-data "frames;frames" pet.py || goto :fail

echo.
echo 완성: dist\pet.exe
exit /b 0

:fail
echo.
echo 묶기 실패. 위의 오류 메시지를 확인하세요.
exit /b 1
