# 손동작으로 출발하는 사탕 로봇 — 설치와 실행

손동작 인식(AI)은 PC 웹캠에서 돌리고, 인식 결과를 USB로 허브에 보내 저장된 미션을 실행하는 구조입니다.

```
웹캠 → MediaPipe 손동작 인식 (PC)  ──USB 시리얼──▶  SPIKE Prime 허브 슬롯 0 실행
       손바닥 펴기 = 출발 / 주먹 = 정지                 라인 따라가기 → 리프트로 사탕 걸기 → 끌고 복귀
```

## 1. PC 준비 (한 번만)

```bash
pip install opencv-python mediapipe pyserial
```

손동작 모델 파일을 받아 `pc_gesture_start.py`와 같은 폴더에 둡니다.
https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task

(기본 제공 손동작: Open_Palm, Closed_Fist, Thumb_Up, Thumb_Down, Victory, Pointing_Up, ILoveYou — 별도 학습 없이 바로 씁니다.)

## 2. 허브 준비

1. AI이거다(또는 SPIKE 앱)에서 `hub_candy_mission.py`를 열고 **슬롯 0에 저장(허브로 다운로드)** 합니다.
2. 허브를 **USB 케이블**로 PC에 연결합니다.
3. SPIKE 앱과 AI이거다 브라우저 탭을 **닫습니다**. (포트를 독점하고 있으면 파이썬이 허브에 접속하지 못합니다)

## 3. 실행

```bash
python pc_gesture_start.py
```

- 카메라 창이 뜨면 손바닥을 펴서 약 0.3초 유지 → 허브가 삐 소리와 함께 출발합니다.
- 주먹을 쥐면 멈춥니다. 창에서 `q`를 누르면 종료합니다.
- 허브가 안 잡히면 포트 목록이 출력됩니다. macOS는 `/dev/cu.usbmodem…`, Windows는 `COM3` 같은 이름입니다.
  `SpikeHub(port='/dev/cu.usbmodem12345')`처럼 직접 지정할 수 있습니다.

## 4. 실측해서 고칠 값 (hub_candy_mission.py 위쪽)

| 이름 | 뜻 | 시뮬레이터 기본값 |
|---|---|---|
| `ARC_TO_CANDY` | 로터리 입구 → 사탕 구역 앞 (cm) | 32 |
| `REACH` | 리프트 바가 사탕을 지나도록 전진 (cm) | 6 |
| `LIFT_DEG` | 리프트 올림/내림 모터 각도 | 300 |
| `PATH_HOME` | 로터리 입구 → 출발 박스 (cm) | 115 |
| `KP` | 라인 추적 민감도 | 1.5 |
| `SAFE_CM` | 보행자 정지 거리 (cm) | 10 |

시뮬레이터(사탕 로봇 시뮬레이터 HTML)의 이동 거리 값으로 먼저 잡고, 실제 매트에서 1~2cm 단위로 조정합니다.

## 슬롯 저장이 안 되는 환경이라면

`SpikeHub.run_code(code)`를 쓰면 코드를 허브 REPL로 직접 보내 바로 실행할 수 있습니다.
`pc_gesture_start.py`에서 `hub.run_slot(SLOT)` 대신:

```python
code = open('hub_candy_mission.py', encoding='utf-8').read()
hub.run_code(code)
```

## 수업 확장 아이디어

- `Victory` 손동작이면 사탕 B를 가져오는 두 번째 미션(슬롯 1) 실행
- Teachable Machine으로 학생들이 직접 만든 손동작(예: "출발", "정지" 포즈)을 학습시켜 교체
- 허브 매트릭스에 인식된 손동작 아이콘 표시 (REPL로 `hub.light_matrix.show_image(...)` 전송)
- `LIFT_DEG`는 리프트 모터를 손으로 돌려 바닥에서 위까지 몇 도인지 `lift.get_degrees_counted()`로 재어 정한다
