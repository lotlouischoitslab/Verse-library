from typing import Dict, List
import copy
from enum import Enum

import numpy as np

from verse.map.lane_segment import AbstractLane
from verse.map.lane import Lane


class LaneMap:
    def __init__(self, lane_seg_list: List[Lane] = []):
        self.lane_dict: Dict[str, Lane] = {}
        self.left_lane_dict: Dict[str, List[str]] = {}
        self.right_lane_dict: Dict[str, List[str]] = {}
        self.h_dict = {}
        for lane_seg in lane_seg_list:
            self.lane_dict[lane_seg.id] = lane_seg
            self.left_lane_dict[lane_seg.id] = []
            self.right_lane_dict[lane_seg.id] = []

    def add_lanes(self, lane_seg_list: List[AbstractLane]):
        for lane_seg in lane_seg_list:
            self.lane_dict[lane_seg.id] = lane_seg
            self.left_lane_dict[lane_seg.id] = []
            self.right_lane_dict[lane_seg.id] = []

    def lane_geometry(self, lane_idx):
        if isinstance(lane_idx, Enum):
            lane_idx = lane_idx.name
        if len(lane_idx) == 3:
            src_lane = f"T{lane_idx[1]}"
        else:
            src_lane = lane_idx 
        return self.lane_dict[src_lane].get_geometry()

    def get_longitudinal_position(self, lane_idx: str, position: np.ndarray) -> float:
        if len(lane_idx) == 3:
            src_lane = f"T{lane_idx[1]}"
        else:
            src_lane = lane_idx 
        if not isinstance(position, np.ndarray):
            position = np.array(position)
        # print(self.lane_dict)
        lane = self.lane_dict[src_lane]
        return lane.get_longitudinal_position(position)

    def get_lateral_distance(self, lane_idx: str, position: np.ndarray) -> float:
        if len(lane_idx) == 3:
            src_lane = f"T{lane_idx[1]}"
        else:
            src_lane = lane_idx 
        if not isinstance(position, np.ndarray):
            position = np.array(position)
        lane = self.lane_dict[src_lane]
        return lane.get_lateral_distance(position)

    def get_altitude(self, lane_idx, position: np.ndarray) -> float:
        raise NotImplementedError

    def get_lane_heading(self, lane_idx: str, position: np.ndarray) -> float:
        if len(lane_idx) == 3:
            src_lane = f"T{lane_idx[1]}"
        else:
            src_lane = lane_idx 
        if not isinstance(position, np.ndarray):
            position = np.array(position)
        lane = self.lane_dict[src_lane]
        return lane.get_heading(position)

    def get_lane_segment(self, lane_idx: str, position: np.ndarray) -> AbstractLane:
        if len(lane_idx) == 3:
            src_lane = f"T{lane_idx[1]}"
        else:
            src_lane = lane_idx 
        if not isinstance(position, np.ndarray):
            position = np.array(position)
        lane = self.lane_dict[src_lane]
        seg_idx, segment = lane.get_lane_segment(position)
        return segment

    def get_speed_limit(self, lane_idx: str) -> float:
        if len(lane_idx) == 3:
            src_lane = f"T{lane_idx[1]}"
        else:
            src_lane = lane_idx 
        lane: Lane = self.lane_dict[src_lane]
        # print(lane.get_speed_limit())
        return lane.get_speed_limit()

    def get_all_speed_limit(self) -> Dict[str, float]:
        ret_dict = {}
        for lane_idx, lane in self.lane_dict.items():
            ret_dict[lane_idx] = lane.get_speed_limit()
        # print(ret_dict)
        return ret_dict

    def get_lane_width(self, lane_idx: str) -> float:
        if len(lane_idx) == 3:
            src_lane = f"T{lane_idx[1]}"
        else:
            src_lane = lane_idx 
        lane: Lane = self.lane_dict[src_lane]
        return lane.get_lane_width()

    def h(self, lane_idx, agent_mode_src, agent_mode_dest):
        return self.h_dict[(lane_idx, agent_mode_src, agent_mode_dest)]

    def h_exist(self, lane_idx, agent_mode_src, agent_mode_dest):
        if (lane_idx, agent_mode_src, agent_mode_dest) in self.h_dict:
            return True 
        else:
            return False

