# ============================================================
#  pc_gesture_start.py  —  PC(웹캠)에서 손동작을 인식해 허브에 출발/정지 신호를 보낸다
#
#  손바닥 펴기(Open_Palm)  → 허브 슬롯 0 프로그램 실행 (사탕 가져오기 출발)
#  주먹 쥐기(Closed_Fist)  → 실행 중인 프로그램 정지
#  엄지 척(Thumb_Up)       → 집게 열기/닫기 테스트 (REPL 방식, 옵션)
#
#  준비:
#    pip install opencv-python mediapipe pyserial
#    모델 파일 gesture_recognizer.task 를 이 파일과 같은 폴더에 둔다 (README 참고)
#    허브를 USB로 연결하고, SPIKE 앱 / AI이거다 브라우저 탭은 닫는다 (포트를 독점하기 때문)
#
#  실행:  python pc_gesture_start.py
#  종료:  창에서 q
# ============================================================
import json
import random
import string
import sys
import time

import cv2
import mediapipe as mp
import serial
import serial.tools.list_ports
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

MODEL_PATH = 'gesture_recognizer.task'
SLOT = 0                 # 허브에 미션 프로그램을 저장해 둔 슬롯 번호
GO_GESTURE = 'Open_Palm'
STOP_GESTURE = 'Closed_Fist'
MIN_SCORE = 0.6          # 이 확신도 이상일 때만 인정
HOLD_FRAMES = 10         # 같은 손동작이 연속 10프레임(약 0.3초) 유지돼야 신호로 인정 (오작동 방지)
COOLDOWN_SEC = 3.0       # 신호를 보낸 뒤 이 시간 동안은 다시 보내지 않음


# ---------------- 허브 통신 ----------------
class SpikeHub:
    """SPIKE Prime 허브와 USB 시리얼(JSON-RPC)로 대화한다."""

    def __init__(self, port=None, baud=115200):
        port = port or self.find_port()
        if port is None:
            raise RuntimeError('허브를 찾지 못했습니다. USB 케이블과 전원을 확인하세요.')
        self.ser = serial.Serial(port, baud, timeout=0.2)
        time.sleep(0.5)
        print(f'[hub] 연결: {port}')

    @staticmethod
    def find_port():
        for p in serial.tools.list_ports.comports():
            desc = (p.description or '') + ' ' + (p.manufacturer or '')
            if 'LEGO' in desc.upper() or p.vid == 0x0694:
                return p.device
        # 못 찾으면 후보 목록을 보여 준다
        print('[hub] 시리얼 포트 목록:')
        for p in serial.tools.list_ports.comports():
            print('   ', p.device, '-', p.description)
        return None

    def _rpc(self, method, params):
        msg = {'m': method, 'p': params,
               'i': ''.join(random.choices(string.ascii_letters + string.digits, k=4))}
        self.ser.write((json.dumps(msg) + '\r').encode())

    def run_slot(self, slot=SLOT):
        print(f'[hub] 슬롯 {slot} 실행 → 출발!')
        self._rpc('program_execute', {'slotid': slot})

    def stop(self):
        print('[hub] 프로그램 정지')
        self._rpc('program_terminate', {})

    # ---- 옵션: 슬롯 대신 코드를 직접 보내 실행 (REPL 방식) ----
    def run_code(self, code):
        """허브 REPL에 파이썬 코드를 밀어 넣어 바로 실행한다. 슬롯 저장이 안 되는 환경에서 사용."""
        self.ser.write(b'\x03\x03')          # 실행 중인 것 중단
        time.sleep(0.3)
        self.ser.write(b'\x01')              # raw REPL 진입
        time.sleep(0.2)
        self.ser.write(code.encode() + b'\x04')   # 코드 전송 + 실행
        time.sleep(0.3)
        print('[hub] 코드 전송 완료')

    def close(self):
        self.ser.close()


# ---------------- 손동작 인식 ----------------
def make_recognizer():
    base = mp_python.BaseOptions(model_asset_path=MODEL_PATH)
    opts = vision.GestureRecognizerOptions(base_options=base, num_hands=1)
    return vision.GestureRecognizer.create_from_options(opts)


def main():
    try:
        hub = SpikeHub()
    except Exception as e:
        print('허브 연결 실패:', e)
        print('허브 없이 인식만 테스트합니다 (신호는 화면에만 표시).')
        hub = None

    recognizer = make_recognizer()
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print('웹캠을 열 수 없습니다. 카메라 권한을 확인하세요.')
        sys.exit(1)

    state = 'READY'          # READY / RUNNING
    last_gesture, held = 'None', 0
    last_signal_time = 0.0
    message, message_until = '', 0.0

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame = cv2.flip(frame, 1)                       # 거울처럼 보이게
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = recognizer.recognize(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))

        gesture, score = 'None', 0.0
        if result.gestures:
            top = result.gestures[0][0]
            gesture, score = top.category_name, top.score
        if score < MIN_SCORE:
            gesture = 'None'

        # 같은 손동작이 연속으로 유지되는지 센다
        held = held + 1 if gesture == last_gesture else 1
        last_gesture = gesture

        now = time.time()
        can_signal = (now - last_signal_time) > COOLDOWN_SEC
        if held == HOLD_FRAMES and can_signal:
            if gesture == GO_GESTURE and state == 'READY':
                if hub: hub.run_slot(SLOT)
                state, message = 'RUNNING', 'GO! 사탕 가지러 출발'
                last_signal_time, message_until = now, now + 2.5
            elif gesture == STOP_GESTURE and state == 'RUNNING':
                if hub: hub.stop()
                state, message = 'READY', 'STOP'
                last_signal_time, message_until = now, now + 2.5

        # 화면 표시
        h, w = frame.shape[:2]
        color_state = (40, 170, 90) if state == 'READY' else (30, 90, 230)
        cv2.rectangle(frame, (0, 0), (w, 70), (20, 20, 20), -1)
        cv2.putText(frame, f'{gesture}  {score:.2f}', (16, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(frame, f'STATE: {state}', (16, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_state, 2)
        # 유지 시간 게이지
        bar = int(min(held, HOLD_FRAMES) / HOLD_FRAMES * 200)
        cv2.rectangle(frame, (w - 220, 25), (w - 20, 45), (80, 80, 80), 1)
        cv2.rectangle(frame, (w - 220, 25), (w - 220 + bar, 45), (0, 200, 255), -1)
        if now < message_until:
            cv2.putText(frame, message, (16, h - 24), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 220, 255), 3)
        cv2.putText(frame, 'Open palm = GO   Fist = STOP   q = quit', (16, h - 60) if now < message_until else (16, h - 24),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        cv2.imshow('Candy Robot - Gesture Start', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    if hub:
        hub.close()


if __name__ == '__main__':
    main()
