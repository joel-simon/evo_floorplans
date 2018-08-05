from __future__ import print_function, division
# import numpy
import networkx as nx
import time
from collections import defaultdict
from itertools import combinations

from floor_plans.geometry import dist
from floor_plans.math_util import mean
from floor_plans import polygon
from floor_plans import travel_paths as pathing

def add_load(floor, path, key, load):
    for i, v1 in enumerate(path[:-1]):
        v2 = path[i+1]
        floor[v1][v2][key] += load / len(path)

def max_load(floor, path, key, load):
    for i, v1 in enumerate(path[:-1]):
        v2 = path[i+1]
        floor[v1][v2][key] = max(load, floor[v1][v2]['load'])

def intitialize(floor, start_pheromone):
    going_outside_penalty = 999999

    for v1, v2, data in floor.edges_iter(data=True):
        if data['between_fixed'] or data['outside']:
            data['weight'] = 1e5
        else:
            data['weight'] = data['length']


        data['pheromone'] = start_pheromone
        data['load'] = 0
        data['between_load'] = 0
        data['entrance_load'] = 0
        data['surge_load'] = 0
        data['width'] = None
        data['load_normalized'] = None

        # if v1 in floor.outside_verts or v2 in floor.outside_verts:
        #     data['weight'] += going_outside_penalty
    for ri, vc in floor.room_centers.items():
        if floor.room_names[ri] in ['cafeteria', 'library', 'gym']:
            continue
        for v in floor.rooms[ri]:
            if v in floor.outside_verts and floor.has_edge(vc, v):
                floor.edge[vc][v]['weight'] += going_outside_penalty

def create_entrances(floor):
    # """ Pick Entrance. """
    exit_vert_loads = []
    centers = set(floor.room_centers.values())
    forbidden_main_entrance = []

    ntid = {name:ID for ID, name in floor.room_names.items()}
    # if 'playground' in ntid:
    #     forbidden_main_entrance = set(floor.rooms[ntid['playground']])


    for i, j, edge in floor.edges_iter(data=True):
        if not edge['load']:
            continue
        j_out = j in floor.outside_verts
        i_out = i in floor.outside_verts
        if i in centers or j in centers:
            continue
        if i_out != j_out: # If one node on outside.
            if i in forbidden_main_entrance or j in forbidden_main_entrance:
                exit_vert_loads.append((0, i if i_out else j))
            else:
                exit_vert_loads.append((edge['load'], i if i_out else j))

    return [v for l, v in sorted(exit_vert_loads, reverse=True)]

def derp(floor):
    centers = set(floor.room_centers.values())
    for n1 in floor.nodes():
        if n1 in centers:
            continue
        good = False
        for n2 in floor.neighbors(n1):
            if floor[n1][n2]['load'] and not floor[n1][n2]['inner'] or (n2 in floor.outside_verts):
                good = True
                # break
        if not good:
            for n2 in floor.neighbors(n1):
                floor[n1][n2]['load'] = 0
                floor[n1][n2]['weight'] = floor[n1][n2]['length']

def calculate_loads(floor, fe_weight, firescapes):
    path_dists, paths = pathing.all_paths(floor, weight='weight')

    for _, _, data in floor.edges_iter(data=True): # Intitialize
        data['load'] = 0
        data['between_load'] = 0
        data['surge_load'] = 0
        data['entrance_load'] = 0

    a = 0
    for load, path in pathing.betweenness_centrality(floor, path_dists, paths):
        add_load(floor, path, key='between_load', load=load)
        a += load
    b = 0
    for load, path in pathing.public_foo(floor, path_dists, paths):
        add_load(floor, path, key='surge_load', load=load)
        b += load

    if firescapes:
        for load, path in pathing.closest_paths(floor, path_dists, paths, floor.outside_verts):
            add_load(floor, path, key='entrance_load', load=fe_weight*load)

    for i, j, d in floor.edges_iter(data=True):
        d['load'] = max(d['between_load'], d['entrance_load'], d['surge_load'])

def normalize_loads(floor):
    mload = sum(d['load'] for i, j, d in floor.edges(data=True))
    for i, j, d in floor.edges(data=True):
        d['load_normalized'] = d['load'] / mload

def create_hallways(floor, iters=10, alpha=12, k=10, pheromone_decay=.1, fe_weight=.5,
                                        start_pheromone=0, verbose=False, firescapes=False):
    max_width = 12
    min_width = 5
    intitialize(floor, start_pheromone)
    # print(fe_weight)
    # fe_weight = 1
    # Main loop.
    for step in range(iters):
        calculate_loads(floor, fe_weight, True)
        normalize_loads(floor)

        pheromone_values = [] # for logging

        for i, j, data in floor.edges(data=True):
            if not (data['between_fixed'] or data['outside']): #if not (data['between_fixed'] or data['outside']):
                data['pheromone'] = (1-pheromone_decay)*data['pheromone'] + k*data['load_normalized']
                pheromone_values.append(data['pheromone'])
                if data['pheromone'] > 0:# and not data['inner']:
                    data['weight'] = data['length'] / ((1+data['pheromone'])**alpha)

        if verbose:
            print("step %i, mean phero=%f, min=%f, max=%f" % \
                (step, mean(pheromone_values), min(pheromone_values), max(pheromone_values)))
            print("step %i, mean phero=%f, min=%f, max=%f" % \
                (step, mean(pheromone_values), min(pheromone_values), max(pheromone_values)))

    entrances = create_entrances(floor)# Create entrances based on those paths to exit
    floor.entrances = entrances

    calculate_loads(floor, fe_weight, firescapes)

    # Now that entrances are created. Find path to main one.
    path_dists, paths = pathing.all_paths(floor, weight='weight')

    if not firescapes:
        for i, j, d in floor.edges_iter(data=True):
            d['entrance_laod'] = 0

    # for load, path in pathing.closest_paths(floor, path_dists, paths, entrances):
    #     if len(path) > 1:
    #         add_load(floor, path, key='entrance_load', load=load)

    for load, path in pathing.closest_paths(floor, path_dists, paths, entrances[:1]):
        add_load(floor, path, key='entrance_load', load=load)
    for i, j, d in floor.edges_iter(data=True):
        d['load'] = max(d['load'], d['entrance_load'])

    # print(c)
    derp(floor)
    ########
    # # TODO explain.
    # for ID, face in floor.rooms.items():
    #     vc = floor.room_centers[ID]
    #     # print(list(floor.inner_edges(ID)))
    #     edge_with_door = max(floor.inner_edges(ID), key=lambda et: et[2]['load'])
    #     vd = edge_with_door[0] if edge_with_door[1] == vc else edge_with_door[1] # vert for door
    #     for v1, v2, data in floor.inner_edges(ID):
    #         if v2 != vc and data['load'] < load_for_doorway:
    #             data['load'] = 0
    #             data['weigh'] = data['length']

    #     s = sum(floor.edge[vc][j_]['load'] for j_ in face if floor.has_edge(vc, j_))
    #     jmax = max((floor.edge[vc][j_]['load'], j_) for j_ in face if floor.has_edge(vc, j_))[1]

    #     for j in face:
    #         if j != jmax and floor.has_edge(vc, j):
    #             floor.edge[vc][j]['load'] =0 maps
    # ########

    # max_laod = max(d['load'] for i, j,d in floor.edges_iter(data=True))
    load_to_width = 1#, max_width / max_laod

    # Convert loads into hallway dimensions.
    for i, j, d in floor.edges(data=True):
        if d['load'] > 0:
            d['width'] = min(max_width, max(min_width, d['load'] * load_to_width))
        else:
            d['width'] = 0

