from audioop import tomono
from quadrotor_agent import QuadrotorAgent
from verse import Scenario
# from verse.plotter.plotter2D import *
from verse.plotter.plotter3D_new import *
from verse.map.example_map.simple_map_3d import SimpleMap1, SimpleMap2, SimpleMap3, SimpleMap5
from verse.sensor.example_sensor.quadrotor_sensor import QuadrotorSensor
import os
import json
import plotly.graph_objects as go
from enum import Enum, auto
from gen_json import write_json, read_json


class CraftMode(Enum):
    Normal = auto()
    Switch_Down = auto()
    Switch_Up = auto()
    Switch_Left = auto()
    Switch_Right = auto()


class TrackMode(Enum):
    Lane0 = auto()
    Lane1 = auto()
    Lane2 = auto()


if __name__ == "__main__":
    input_code_name = './demo/quadrotor/quadrotor_controller.py'
    scenario = Scenario()

    path = os.path.abspath(__file__)
    path = path.replace('demo5.py', 'test.json')
    # print(path)
    with open(path, 'r') as f:
        prarms = json.load(f)
    time_step = 0.1
    quadrotor1 = QuadrotorAgent('test1', file_name=input_code_name)
    scenario.add_agent(quadrotor1)
    init_l_1 = [-15, -4, 1, 0, 0, 0]
    init_u_1 = [-14, -3, 1, 0, 0, 0]
    # init_u_1 = [3.5, -8.5, -1, 0, 0, 0]
    scenario.set_init_single(quadrotor1.id, [init_l_1, init_u_1], tuple(
        [CraftMode.Normal, TrackMode.Lane0]))
    quadrotor2 = QuadrotorAgent('test2', file_name=input_code_name)
    scenario.add_agent(quadrotor2)
    init_l_2 = [-17, -13, 8, 0, 0, 0]
    init_u_2 = [-16, -12, 9, 0, 0, 0]
    # init_u_2 = [3, -5, -4, 0, 0, 0]
    scenario.set_init_single(quadrotor2.id, [init_l_2, init_u_2], tuple(
        [CraftMode.Normal, TrackMode.Lane0]))

    t_v = {quadrotor1.id: (1, 1),
           quadrotor2.id: (1, 0.3)}
    bs = {quadrotor1.id: [0.4]*3,
          quadrotor2.id: [0.4]*3}
    tmp_map = SimpleMap5(t_v_pair=t_v, box_side=bs)
    scenario.set_map(tmp_map)
    fig = go.Figure()
    scenario.set_sensor(QuadrotorSensor())

    traces = scenario.simulate(100, time_step)
    # path = os.path.abspath(__file__)
    # path = path.replace('quadrotor_demo2.py', 'output_2.json')
    # write_json(traces, path)
    fig = go.Figure()
    fig = simulation_tree_3d(traces, tmp_map, fig, 1, 2, 3, [0, 1, 2, 3],
                             'lines', 'trace')
    fig.show()

    # traces = scenario.verify(100, time_step)
    # fig = go.Figure()
    # fig = reachtube_tree_3d(traces, tmp_map, fig, 1, 2, 3, [0, 1, 2, 3],
    #                         'lines', 'trace')
    # fig.show()
