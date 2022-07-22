from enum import Enum, auto


class BallTypeMode(Enum):
    TYPE1 = auto()
    TYPE2 = auto()

class BallMode(Enum):
    Normal = auto()
    
class State:
    x:float
    y = 0.0
    vx = 0.0
    vy = 0.0
    mode: BallMode
    type: BallTypeMode
    def __init__(self, x, y, vx, vy, ball_mode:BallMode, type: BallTypeMode):
        pass

def controller(ego:State, other: State):
    output = copy.deepcopy(ego)
    if ego.x<0:
        output.vx = -ego.vx
        output.x=0
    if ego.y<0:
        output.vy = -ego.vy
        output.y=0
    if ego.x>20:
        output.vx = -ego.vx
        output.x=20
    if ego.y>20:
        output.vy = -ego.vy
        output.y=20
    def abs_diff(a, b):
        if a < b:
            r = b - a
        else:
            r = a - b
        return r
    def dist(a, b):
        return abs_diff(a.x, b.x) + abs_diff(a.y, b.y)
    assert not (dist(ego, other) < 5 and ego.x < other.x), "collision"
    return output

from dryvr_plus_plus.example import BallAgent
from dryvr_plus_plus import Scenario
from dryvr_plus_plus.plotter.plotter2D import *
import plotly.graph_objects as go

if __name__ == "__main__":
    ball_controller = './demo/ball_bounces_dev.py'
    bouncingBall = Scenario()
    myball1 = BallAgent('red-ball', file_name=ball_controller)
    myball2 = BallAgent('green-ball', file_name=ball_controller)
    bouncingBall.add_agent(myball1)
    bouncingBall.add_agent(myball2)
    bouncingBall.set_init(
        [
            [[5, 10, 2, 2], [5, 10, 2, 2]],
            [[15, 1, 1, -2], [15, 1, 1, -2]]
        ],
        [
            (BallMode.Normal,),
            (BallMode.Normal,)
        ],
        [
            (BallTypeMode.TYPE1,),
            (BallTypeMode.TYPE2,)
        ]
    )
    traces = bouncingBall.simulate(10, 0.01)
    fig = go.Figure()
    fig = simulation_tree(traces, fig=fig)
    fig.show()

