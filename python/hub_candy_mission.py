# ============================================================
#  hub_candy_mission.py  —  허브(SPIKE Prime)에서 실행되는 미션 프로그램
#  AI이거다 / SPIKE 앱에서 이 코드를 열어 허브의 "슬롯 0"에 저장(다운로드)해 둔다.
#  PC의 pc_gesture_start.py가 손동작을 인식하면 이 슬롯을 실행시킨다.
#
#  로봇: 미니 멀티로버 — 주행 모터 E+F, 리프트 C, 컬러 센서 A(아래 앞), 거리 센서 B(위 앞)
#  사탕은 리프트를 올린 채 다가가 사탕 뒤로 내려 걸고, 그대로 끌고 온다.
#        바퀴 지름 5.6cm (1회전 17.5cm), 바퀴 간격 약 11cm
#  매트: 사탕 매트 (가운데 로터리, 양쪽 곡선 길, 빨간 표시 2개)
# ============================================================
from spike import PrimeHub, MotorPair, Motor, ColorSensor, DistanceSensor
from spike.control import wait_for_seconds

hub = PrimeHub()
pair = MotorPair('E', 'F')
lift = Motor('C')
color = ColorSensor('A')
dist = DistanceSensor('B')

pair.set_motor_rotation(17.5, 'cm')   # 바퀴 1회전 = 17.5cm
pair.set_default_speed(25)

LEFT, RIGHT = 1, -1   # 센서가 올라탈 라인 가장자리
KP = 1.5              # 반사값 오차 → 조향값 비율 (라인을 자꾸 놓치면 키우고, 심하게 흔들리면 줄인다)
SAFE_CM = 10          # 거리 센서로 이 거리 안에 무언가 보이면 정지 (보행자 안전)

# ---------- 실측해서 고치는 값 ----------
ARC_TO_CANDY = 32     # 로터리 입구(빨간 표시) → 사탕 구역 앞까지 라인을 따라가는 거리(cm)
REACH = 6             # 사탕 구역을 향해 돌아선 뒤, 리프트 바가 사탕을 지나도록 전진하는 거리(cm)
LIFT_DEG = 300        # 리프트 바가 바닥 ↔ 위로 움직이는 모터 각도 (기어비에 맞춰 실측)
PATH_HOME = 115       # 로터리 입구 → 출발 박스 앞까지 곡선 길 거리(cm)


# ---------- 기본 동작 ----------
def turn(deg):
    """자이로로 제자리 회전. 양수 = 오른쪽"""
    hub.motion_sensor.reset_yaw_angle()
    pair.start(steering=100 if deg > 0 else -100, speed=20)
    while abs(hub.motion_sensor.get_yaw_angle()) < abs(deg):
        pass
    pair.stop()


def wait_if_blocked():
    """앞에 손이나 사람이 있으면 멈추고 'NO'를 띄운 채 기다린다."""
    d = dist.get_distance_cm()
    if d is not None and d < SAFE_CM:
        pair.stop()
        hub.light_matrix.show_image('NO')
        hub.speaker.beep(60, 0.1)
        while True:
            d = dist.get_distance_cm()
            if d is None or d >= SAFE_CM:
                break
        hub.light_matrix.show_image('ARROW_N')


def follow_step(edge):
    """컬러 센서 하나로 라인 가장자리를 따라가는 한 스텝 (P 제어)"""
    wait_if_blocked()
    r = color.get_reflected_light()          # 0(검정) ~ 100(흰색), 가장자리 = 50
    steer = int((r - 50) * KP) * edge
    steer = max(-100, min(100, steer))
    pair.start(steering=steer)


def follow_until_red(count=1, edge=LEFT):
    """빨간 표시를 count번째 만날 때까지 라인 따라가기"""
    seen = 0
    on_red = (color.get_color() == 'red')
    while seen < count:
        follow_step(edge)
        red = (color.get_color() == 'red')
        if red and not on_red:
            seen += 1
            hub.speaker.beep(72, 0.1)
        on_red = red
    pair.stop()


def follow_for_cm(cm, edge=LEFT):
    """정해진 거리(cm)만큼 라인 따라가기 — 모터 각도로 거리를 센다"""
    m = Motor('E')
    m.set_degrees_counted(0)
    while abs(m.get_degrees_counted()) / 360 * 17.5 < cm:
        follow_step(edge)
    pair.stop()


def lift_up():
    """바를 올린다 — 사탕 위를 지나갈 수 있고, 걸려 있던 사탕은 놓인다"""
    lift.run_for_degrees(-LIFT_DEG, 40)


def lift_down():
    """바를 내린다 — 바와 로봇 사이에 사탕이 있으면 걸려서 끌려온다"""
    lift.run_for_degrees(LIFT_DEG, 40)


# ---------- 미션: A에서 출발 → 사탕 A 걸어 끌고 → A로 복귀 ----------
def mission_candy_A():
    hub.light_matrix.show_image('ARROW_N')
    hub.speaker.beep(84, 0.3)                      # 출발 신호음

    lift_up()                                      # 0. 바를 올린 채 출발 (사탕 위를 지나갈 수 있게)
    follow_until_red(count=1, edge=LEFT)           # 1. 곡선 길을 따라 로터리 입구까지
    follow_for_cm(ARC_TO_CANDY, edge=LEFT)         # 2. 왼쪽 가장자리 → 시계 방향으로 사탕 A 앞까지
    turn(-90)                                      # 3. 사탕 구역 쪽(바깥)으로 돌아선다
    pair.move(REACH, 'cm', speed=20)               # 4. 바가 사탕을 지나 사탕이 바와 로봇 사이에 오게 전진
    lift_down()                                    # 5. 바를 내려 사탕을 건다
    hub.light_matrix.show_image('HAPPY')
    pair.move(-REACH, 'cm', speed=20)              # 6. 사탕을 끌고 후진해서 라인으로 복귀
    turn(-90)                                      # 7. 돌아갈 방향(반시계)으로
    follow_until_red(count=1, edge=RIGHT)          # 8. 오른쪽 가장자리 → 입구로 빠져나온다
    follow_for_cm(PATH_HOME, edge=RIGHT)           # 9. 곡선 길을 따라 출발 박스까지 끌고 간다
    lift_up()                                      # 10. 바를 올려 사탕을 놓는다
    hub.light_matrix.show_image('YES')
    hub.speaker.beep(96, 0.5)


mission_candy_A()
