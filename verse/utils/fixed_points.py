from typing import Tuple, List 
import numpy as np 
from scipy.integrate import ode 
from verse import BaseAgent, Scenario,  ScenarioConfig
from verse.analysis.utils import wrap_to_pi 
from verse.analysis.analysis_tree import TraceType, AnalysisTree 
from verse.parser import ControllerIR
from verse.analysis import AnalysisTreeNode, AnalysisTree, AnalysisTreeNodeType
from enum import Enum, auto
from verse.plotter.plotter2D import *
from verse.plotter.plotter3D_new import *
import plotly.graph_objects as go
import copy
from typing import Dict, Sequence
from z3 import *
from verse.analysis.simulator import convertStrToEnum
import types

### revised version of top function
### will now return a list of the vertices of composed/product hyperrectangles (2 vertices per rect) index by node number
def reach_at_fix(tree: AnalysisTree, t_lower: float = None, t_upper: float = None) -> Dict[int, List[List[float]]]:
    nodes: List[AnalysisTreeNode] = tree.nodes 
    agents = nodes[0].agent.keys() # list of agents
    reached: Dict[int, List[List[float]]] = {}
    node_counter = 0
    sim_enum: Dict[str, Dict[str, int]] = {} #indexed by agent and then by mode -- simulates the enum class 
    for agent in agents:
        sim_enum[agent] = {'_index': 0} # initial start with an index of 0 
    T = 0 # we know time horizon occurs in the leaf node, by definition, shouldn't matter which leaf node we check
    if t_lower is None or t_upper is None:
        last: list[AnalysisTreeNode] = tree.get_leaf_nodes(tree.root)
        T = last[0].trace[list(agents)[0]][-1][0] # using list casting since the agent doesn't matter
    for node in nodes:
        reached[node_counter] = None
        modes = node.mode 
        reach_node: Dict[str, List[List[float]]] = {} # will store ordered list of hyperrectangle vertices indexed by agents
        for agent in agents:
            reach_node[agent] = []
            # could turn this into a subroutine
            for mode in modes[agent]:
                if mode not in sim_enum[agent]:
                    sim_enum[agent][mode] = sim_enum[agent]['_index']
                    sim_enum[agent]['_index'] += 1

            ### make error message for t_lower and t_upper
            if t_lower is not None and t_upper is not None: ### may want to seperate this out into a seperate function
                for i in range(0, len(node.trace[agent]), 2): # just check the upper bound, time difference between lower and upper known to be time step of scenario
                    if node.trace[agent][i+1][0]<t_lower: # first, use the time of the upper bound to see if we can add current node
                        continue
                    if node.trace[agent][i+1][0]>t_upper:
                        break
                    lower = list(node.trace[agent][i][1:]) # now strip out time and add agent's mode(s)
                    upper = list(node.trace[agent][i+1][1:])
                    for mode in modes[agent]: # assume that size of modes[agent] doesn't change between nodes
                        ### for now, use this simulated enum instead of trying to figure out how to access enum class
                        lower.append(sim_enum[agent][mode])
                        upper.append(sim_enum[agent][mode]) 
                    reach_node[agent] += [lower, upper]
            else: ### for now, just assume if t_lower and t_upper not supplied, we just want last node 
                if node.trace[agent][-1][0]==T:
                    lower = list(node.trace[agent][-2][1:])
                    upper = list(node.trace[agent][-1][1:])
                    for mode in modes[agent]: # assume that size of modes[agent] doesn't change between nodes
                        ### for now, use this simulated enum instead of trying to figure out how to access enum class
                        lower.append(sim_enum[agent][mode])
                        upper.append(sim_enum[agent][mode]) 
                    reach_node[agent] += [lower, upper]
        ### loop through each agent and add its state value to an existing composed state
        for agent in agents:
            for i in range(len(reach_node[agent])):
                if reached[node_counter] is None:
                    reached[node_counter] = [[] for _ in range(len(reach_node[agent]))] 
                # print(len(reach_node[agent]))
                reached[node_counter][i] += reach_node[agent][i]
        if reached[node_counter] is not None: ### design choice, decided not to add node if there wasn't anything in it, could alternatively added and then created an additional check in contains_all
            node_counter += 1
    return reached

#unit test this
def contain_all_fix(reach1: Dict[int, List[List[float]]], reach2: Dict[int, List[List[float]]]) -> Bool:
    nodes = list(reach1.keys()) # this is abritrary, could be from either reach set, just need this 
    state_len = len(reach1[nodes[0]][0]) # taking the first vertex, could be any
    P = RealVector('p', state_len)
    in_r1 = Or() #just set this boolean statement to just Or for now, can sub with Or(False) if having issues
    in_r2 = Or() #as above, sub with Or(False) if having issues
    s = Solver()
    # print(reach1, reach2[5][3], reach2[5][5], reach2[6][3], reach2[6][5])
    for node in reach1: # for each node
        if reach1[node] is None:
            continue
        for i in range(0, len(reach1[node]), 2): # for each vertex in the node
            includes = And()
            hr = [reach1[node][i], reach1[node][i+1]] # clarifies expressions and matches logic with contain_all
            for j in range(state_len):
                includes = And(includes, P[j] >= hr[0][j], P[j] <= hr[1][j])
            in_r1 = Or(in_r1, includes)
    
    for node in reach2: #same as above loop except for r2 -- should probably make into subroutine
        if reach2[node] is None: ### temp solution, reachset contained a node with nothing in it
            continue
        for i in range(0, len(reach2[node]), 2): # for each vertex in the node
            includes = And()
            hr = [reach2[node][i], reach2[node][i+1]] # clarifies expressions and matches logic with contain_all
            for j in range(state_len):
                includes = And(includes, P[j] >= hr[0][j], P[j] <= hr[1][j])
            in_r2 = Or(in_r2, includes)
    
    s.add(in_r1, Not(in_r2))
    return s.check() == unsat

def fixed_points_fix(tree: AnalysisTree, T: float = 40, t_step: float = 0.01) -> bool:
    reach_end = reach_at_fix(tree)
    reach_else = reach_at_fix(tree, 0, T-t_step+t_step*.01) # need to add some offset because of some potential decimical diffs  
    return contain_all_fix(reach_end, reach_else)

### functions below this point should not be used in lieu of the functions above

### returns whether hyperrectangle 1 is contained within hyperrectangle 2
### expects to be given two states (lower and upper bounds for each state) from a trace/set of traces
def contained_single(h1: List[np.array], h2: List[np.array]) -> bool: 
    lower: List[bool] = h2[0][1:] <= h1[0][1:] # consider after first index, time -- move to top
    upper: List[bool] = h1[1][1:] <= h2[1][1:]
    return all(lower) and all(upper)

### extracts nodes reached between a certain lower time bound and upper time bound
### by default, will only extract the states from the very last
def reach_at(trace: AnalysisTree, t_lower: float = None, t_upper: float = None) -> Dict[str, Dict[str, List[List[np.array]]]]: 
    nodes = trace.nodes 
    agents = nodes[0].agent.keys() # list of agents\
    reached: Dict[str, Dict[str, List[List[np.array]]]] = {}
    for agent in agents:
        reached[agent] = {}
    T = 0 # we know time horizon occurs in the leaf node, by definition, shouldn't matter which leaf node we check
    if t_lower is None or t_upper is None:
        last: list[AnalysisTreeNode] = trace.get_leaf_nodes(trace.root)
        T = last[0].trace[list(agents)[0]][-1][0] # using list casting since the agent doesn't matter
    for node in nodes:
        modes = node.mode 
        for agent in agents:
            ### make error message for t_lower and t_upper
            if t_lower is not None and t_upper is not None: ### may want to seperate this out into a seperate function
                for i in range(0, len(node.trace[agent]), 2): # just check the upper bound, time difference between lower and upper known to be time step of scenario
                    lower = node.trace[agent][i]
                    upper = node.trace[agent][i+1]
                    if upper[0]>=t_lower and upper[0]<=t_upper: ### think about why cut off here explicitly -- includes T-delta T but not T if upper bound is T-delta T
                        state = [lower, upper]
                        if modes[agent] not in reached[agent]: #initializing mode of agent in dict if not already there
                            reached[agent][modes[agent]] = []
                        reached[agent][modes[agent]].append(state) #finally, add state to reached
            else: ### for now, just assume if t_lower and t_upper not supplied, we just want last node 
                if node.trace[agent][-1][0]==T:
                    if modes[agent] not in reached[agent]: #initializing mode of agent in dict if not already there
                        reached[agent][modes[agent]] = []
                    reached[agent][modes[agent]].append([node.trace[agent][-2], node.trace[agent][-1]]) 
    return reached

### assuming getting inputs from reach_at calls
### this algorithm shouldn't work, it doesn't consider the composition of all agents
def contain_all(reach1: Dict[str, Dict[str, List[List[np.array]]]], reach2: Dict[str, Dict[str, List[List[np.array]]]], state_len: int = None) -> bool:
    if state_len is None: ### taking from input now, could also derive from either reach1 or reach2
        agents = list(reach1.keys()) # if this works 100%, then get rid of if and option to pass state_len as input
        state_len = len(reach1[agents[0]][list(reach1[agents[0]].keys())[0]][0][0])-1 # strip one dimension to account for ignoring time
    P = RealVector('p', state_len) 
    in_r1 = Or() #just set this boolean statement to just Or for now, can sub with Or(False) if having issues
    in_r2 = Or() #as above, sub with Or(False) if having issues
    s = Solver()
    ### eventually want to check sat of (in_r1 and not in_r2)
    for agent in reach1.keys():
        for mode in reach1[agent].keys():
            for hr in reach1[agent][mode]: # hr is a hyperrectangle defined by lower and upper bounds stored in a list
                includes = And()
                for i in range(state_len):
                    includes = And(includes, P[i] >= hr[0][i+1], P[i] <= hr[1][i+1]) ### include the previous conditions and new bounds for the new dimension
                in_r1 = Or(in_r1, includes) ### in_r1 should check to if there exists a point that can be any hyperrectangle from set r1
    ### could probably seperate out above and below loops into subroutine
    for agent in reach2.keys():
        for mode in reach2[agent].keys():
            for hr in reach2[agent][mode]:
                includes = And()
                for i in range(state_len):
                    includes = And(includes, P[i] >= hr[0][i+1], P[i] <= hr[1][i+1]) ### include the previous conditions and new bounds for the new dimension
                in_r2 = Or(in_r2, includes) ### in_r2 should check to if there exists a point that can be any hyperrectangle from set r2
    
    s.add(in_r1, Not(in_r2))
    return s.check() == unsat

### assuming user has T and t_step from previous scenario definition 
def fixed_points_sat(tree: AnalysisTree, T: float = 40, t_step: float = 0.01) -> bool: 
    reach_end = reach_at(tree)
    reach_else = reach_at(tree, 0, T-t_step+t_step*.01) # need to add some offset because of some potential decimical diffs  
    return contain_all(reach_end, reach_else)

def pp_fix(reach_set: Dict[int, List[List[float]]]) -> None:
    for node in reach_set:
        for i in range(0, len(reach_set[node]), 2):
            print(f'Non-empty node {node} -- {i//2}th state: {[reach_set[node][i], reach_set[node][i+1]]}')

def pp_old(reach_set: Dict[str, Dict[str, List[List[np.array]]]]) -> None:
    for agent in reach_set:
        for mode in reach_set[agent]:
            for state in reach_set[agent][mode]:
                print(f'Agent {agent} in mode {mode}: {state}')