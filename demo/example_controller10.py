from enum import Enum, auto
import copy
from dryvr_plus_plus.map.lane_map import LaneMap


class VehicleMode(Enum):
    Normal = auto()
    SwitchLeft = auto()
    SwitchRight = auto()
    Brake = auto()
    Accelerate = auto()


class LaneMode(Enum):
    Lane0 = auto()
    Lane1 = auto()
    Lane2 = auto()


class LaneObjectMode(Enum):
    Vehicle = auto()
    Ped = auto()        # Pedestrians
    Sign = auto()       # Signs, stop signs, merge, yield etc.
    Signal = auto()     # Traffic lights
    Obstacle = auto()   # Static (to road/lane) obstacles


class State:
    x = 0.0
    y = 0.0
    theta = 0.0
    v = 0.0
    vehicle_mode: VehicleMode = VehicleMode.Normal
    lane_mode: LaneMode = LaneMode.Lane0
    type: LaneObjectMode

    def __init__(self, x, y, theta, v, vehicle_mode: VehicleMode, lane_mode: LaneMode, type: LaneObjectMode):
        self.data = []


def controller(ego: State, other: State, sign: State, lane_map: LaneMap):
    output = copy.deepcopy(ego)
    if ego.vehicle_mode == VehicleMode.Normal:
        if lane_map.get_longitudinal_position(other.lane_mode, [other.x, other.y]) - lane_map.get_longitudinal_position(ego.lane_mode, [ego.x, ego.y]) > 3 \
            and lane_map.get_longitudinal_position(other.lane_mode, [other.x, other.y]) - lane_map.get_longitudinal_position(ego.lane_mode, [ego.x, ego.y]) < 5 \
                and ego.lane_mode == other.lane_mode:
            if lane_map.has_left(ego.lane_mode):
                output.vehicle_mode = VehicleMode.SwitchLeft
        if lane_map.get_longitudinal_position(other.lane_mode, [other.x, other.y]) - lane_map.get_longitudinal_position(ego.lane_mode, [ego.x, ego.y]) > 3 \
            and lane_map.get_longitudinal_position(other.lane_mode, [other.x, other.y]) - lane_map.get_longitudinal_position(ego.lane_mode, [ego.x, ego.y]) < 5 \
                and ego.lane_mode == other.lane_mode:
            if lane_map.has_right(ego.lane_mode):
                output.vehicle_mode = VehicleMode.SwitchRight
        # if ego.lane_mode != other.lane_mode:
        #     output.vehicle_mode = VehicleMode.Accelerate
        # if lane_map.get_longitudinal_position(other.lane_mode, [other.x, other.y]) - lane_map.get_longitudinal_position(ego.lane_mode, [ego.x, ego.y]) > 5:
        #     output.vehicle_mode = VehicleMode.Accelerate
        if lane_map.get_speed_limit(ego.lane_mode) > 1:
            output.vehicle_mode = VehicleMode.Accelerate

    if ego.vehicle_mode == VehicleMode.SwitchLeft:
        if lane_map.get_lateral_distance(ego.lane_mode, [ego.x, ego.y]) >= 2.5:
            output.vehicle_mode = VehicleMode.Normal
            output.lane_mode = lane_map.left_lane(ego.lane_mode)
    if ego.vehicle_mode == VehicleMode.SwitchRight:
        if lane_map.get_lateral_distance(ego.lane_mode, [ego.x, ego.y]) <= -2.5:
            output.vehicle_mode = VehicleMode.Normal
            output.lane_mode = lane_map.right_lane(ego.lane_mode)
    if ego.vehicle_mode == VehicleMode.Accelerate:
        if lane_map.get_longitudinal_position(other.lane_mode, [other.x, other.y]) - lane_map.get_longitudinal_position(ego.lane_mode, [ego.x, ego.y]) > 3 \
            and lane_map.get_longitudinal_position(other.lane_mode, [other.x, other.y]) - lane_map.get_longitudinal_position(ego.lane_mode, [ego.x, ego.y]) < 5 \
                and ego.lane_mode == other.lane_mode:
            output.vehicle_mode = VehicleMode.Normal
        # if lane_map.get_speed_limit(ego.lane_mode, [ego.x, ego.y]) <= ego.v:
        #     output.vehicle_mode = VehicleMode.Normal

    return output
