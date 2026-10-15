# 사탕 로봇 시뮬레이터 (SPIKE Prime · Python)

레고 스파이크 프라임 드라이빙베이스로 사탕 매트 위를 자율주행해 사탕을 가져오는 수업용 시뮬레이터입니다.
코딩하기 전에 명령을 블록처럼 쌓아 실행해 보며, 각 블록에 대응하는 파이썬 코드를 함께 봅니다.

- **웹 시뮬레이터**: `index.html` (GitHub Pages로 게시 → 아래 주소)
- **실제 로봇 코드**: `python/` 폴더
  - `hub_candy_mission.py` — 허브에서 실행되는 미션(라인 추적 → 사탕 집기 → 복귀)
  - `pc_gesture_start.py` — PC 웹캠 손동작 인식으로 출발/정지 신호 전송
  - `README.md` — 설치·실행 순서

## 게시 주소
GitHub Pages를 켜면 `https://<계정>.github.io/<저장소>/` 에서 열립니다.
(Settings → Pages → Branch: `main`, Folder: `/ (root)`)

## 로봇 사양
주행 모터 E+F · 집게 C · 컬러 센서 A · 거리 센서 B · 바퀴 지름 5.6cm(1회전 17.5cm) · 바퀴 간격 약 11cm

---
대담 AI Lab · 고색고등학교 「레고 스파이크 프라임 기반 파이썬 프로그래밍」
