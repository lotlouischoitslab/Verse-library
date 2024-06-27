
from typing import Tuple, List 

import numpy as np 
from scipy.integrate import ode 

from verse import BaseAgent, Scenario, ScenarioConfig
from verse.analysis.utils import wrap_to_pi 
from verse.analysis.analysis_tree import TraceType, AnalysisTree 
from verse.parser import ControllerIR
from verse.analysis import AnalysisTreeNode, AnalysisTree, AnalysisTreeNodeType
import copy 

from enum import Enum, auto

from verse.plotter.plotter2D import *
from verse.plotter.plotter3D_new import *
import plotly.graph_objects as go

from verse.utils.fixed_points import *

class BrussAgent(BaseAgent):
    def __init__(
        self, 
        id, 
        code = None,
        file_name = None
    ):
        super().__init__(id, code, file_name)

    @staticmethod
    def dynamic(t, state):
        x, y = state
        x_dot = 1+x**2*y-2.5*x
        y_dot = 1.5*x-x**2*y
        return [x_dot, y_dot]

    def TC_simulate(
        self, mode: List[str], init, time_bound, time_step, lane_map = None
    ) -> TraceType:
        time_bound = float(time_bound)
        num_points = int(np.ceil(time_bound / time_step))
        trace = np.zeros((num_points + 1, 1 + len(init)))
        trace[1:, 0] = [round(i * time_step, 10) for i in range(num_points)]
        trace[0, 1:] = init
        for i in range(num_points):
            r = ode(self.dynamic)
            r.set_initial_value(init)
            res: np.ndarray = r.integrate(r.t + time_step)
            init = res.flatten()
            trace[i + 1, 0] = time_step * (i + 1)
            trace[i + 1, 1:] = init
        return trace

class BrussMode(Enum):
    Normal=auto()

class State:
    x: float
    y: float
    agent_mode: BrussMode 

    def __init__(self, x, y, agent_mode: BrussMode):
        pass 

def decisionLogic(ego: State, other: State):
    output = copy.deepcopy(ego)
    return output 



if __name__ == "__main__":
    import os 
    script_dir = os.path.realpath(os.path.dirname(__file__))
    input_code_name = os.path.join(script_dir, "brusselator.py")
    Bruss = BrussAgent('bruss', file_name=input_code_name)

    scenario = Scenario(ScenarioConfig(init_seg_length=1, parallel=False))

    scenario.add_agent(Bruss) ### need to add breakpoint around here to check decision_logic of agents

    init_bruss = [[2, 1],[3, 1.5]]
    # # -----------------------------------------

    scenario.set_init_single(
        'bruss', init_bruss, (BrussMode.Normal,)
    )

    trace = scenario.verify(10, 0.01)

    # pp_fix(reach_at_fix(trace, 0, 10))

    ### fixed points eventually reached at t=120, not quite at t=60 though
    print(f'Fixed points exists? {fixed_points_fix(trace, 10, 0.01)}')

    fig = go.Figure()
    fig = reachtube_tree(trace, None, fig, 0, 1, [0, 1], "fill", "trace", plot_color=colors[1:]) # easy way to get another color aside from red
    fig = reachtube_tree(trace, None, fig, 0, 2, [0, 2], "fill", "trace")
    # fig = simulation_tree(trace, None, fig, 1, 2, [1, 2], "fill", "trace")
    fig.show()