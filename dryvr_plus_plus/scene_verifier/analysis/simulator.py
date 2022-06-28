from typing import List, Dict
import copy
import itertools

import numpy as np

from dryvr_plus_plus.scene_verifier.agents.base_agent import BaseAgent
from dryvr_plus_plus.scene_verifier.analysis.analysis_tree_node import AnalysisTreeNode


class Simulator:
    def __init__(self):
        self.simulation_tree_root = None

    def simulate(self, init_list, init_mode_list, agent_list:List[BaseAgent], transition_graph, time_horizon, time_step, lane_map):
        # Setup the root of the simulation tree
        root = AnalysisTreeNode(
            trace={},
            init={},
            mode={},
            agent={},
            child=[],
            start_time=0,
        )
        for i, agent in enumerate(agent_list):
            root.init[agent.id] = init_list[i]
            init_mode = [elem.name for elem in init_mode_list[i]]
            root.mode[agent.id] = init_mode
            root.agent[agent.id] = agent
            root.type = 'simtrace'
        self.simulation_tree_root = root
        simulation_queue = []
        simulation_queue.append(root)
        # Perform BFS through the simulation tree to loop through all possible transitions
        while simulation_queue != []:
            node:AnalysisTreeNode = simulation_queue.pop(0)
            print(node.start_time, node.mode)
            remain_time = round(time_horizon - node.start_time,10)
            if remain_time <= 0:
                continue
            # For trace not already simulated
            for agent_id in node.agent:
                if agent_id not in node.trace:
                    # Simulate the trace starting from initial condition
                    # [time, x, y, theta, v]
                    mode = node.mode[agent_id]
                    init = node.init[agent_id]
                    trace = node.agent[agent_id].TC_simulate(mode, init, remain_time, time_step, lane_map)
                    trace[:,0] += node.start_time
                    node.trace[agent_id] = trace.tolist()

            transitions, transition_idx = transition_graph.get_transition_simulate_new(node)

            # If there's no transitions (returned transitions is empty), continue
            if not transitions:
                continue


            # truncate the computed trajectories from idx and store the content after truncate
            truncated_trace = {}
            print("idx", idx)
            for agent_idx in node.agent:
                truncated_trace[agent_idx] = node.trace[agent_idx][transition_idx:]
                node.trace[agent_idx] = node.trace[agent_idx][:transition_idx+1]

            # Generate the transition combinations if multiple agents can transit at the same time step
            transition_list = list(transitions.values())
            all_transition_combinations = itertools.product(*transition_list)

            # For each possible transition, construct the new node.
            # Obtain the new initial condition for agent having transition
            # copy the traces that are not under transition

            for transition_combination in all_transition_combinations:
                next_node_mode = copy.deepcopy(node.mode) 
                next_node_agent = node.agent 
                next_node_start_time = list(truncated_trace.values())[0][0][0]
                next_node_init = {}
                next_node_trace = {}
                for transition in transition_combination:
                    transit_agent_idx, src_mode, dest_mode, next_init, idx = transition
                    if dest_mode is None:
                        continue
                    # next_node = AnalysisTreeNode(trace = {},init={},mode={},agent={}, child = [], start_time = 0)
                    next_node_mode[transit_agent_idx] = dest_mode 
                    next_node_init[transit_agent_idx] = next_init 
                for agent_idx in next_node_agent:
                    if agent_idx not in next_node_init:
                        next_node_trace[agent_idx] = truncated_trace[agent_idx]

                tmp = AnalysisTreeNode(
                    trace=next_node_trace,
                    init=next_node_init,
                    mode=next_node_mode,
                    agent=next_node_agent,
                    child=[],
                    start_time=next_node_start_time,
                    type='simtrace'
                )
                node.child.append(tmp)
                simulation_queue.append(tmp)
                # Put the node in the child of current node. Put the new node in the queue
            #     node.child.append(AnalysisTreeNode(
            #         trace = next_node_trace,
            #         init = next_node_init,
            #         mode = next_node_mode,
            #         agent = next_node_agent,
            #         child = [],
            #         start_time = next_node_start_time
            #     ))
            # simulation_queue += node.child
        return self.simulation_tree_root
