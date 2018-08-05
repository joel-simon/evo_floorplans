from __future__ import print_function, division

import networkx as nx
from floor_plans.geometry import dist

def project(A, B, C):
    """ Given three points, return the point D
        where D is on the segment AB and CD is orthogonal to AB
    """
    x1, y1 = A
    x2, y2 = B
    x3, y3 = C

    px = x2-x1
    py = y2-y1
    dAB = px*px + py*py
    u = ((x3 - x1) * px + (y3 - y1) * py) / dAB
    
    x = x1 + u * px
    y = y1 + u * py

    return x, y

def smooth(floor):
    """ Smooth the hallways to reduce overly curvy hallways.
    """
    V = floor.vertices
    H = nx.Graph()
    
    for i, j, data in floor.edges_iter(data=True):
        if data['width'] > 0 and not data['inner']:
            H.add_edge(i, j)

    mapping = dict()

    for vi1 in H.nodes():
        vn = H.neighbors(vi1)
        if len(vn) == 2:  # Only take nodes with two 
            vi2, vi3 = vn
            
            v1 = floor.vertices[vi1]
            v2, v3 = floor.vertices[vi2], floor.vertices[vi3]

            p = project(v3, v2, v1)# projection point
            new_n = ((v1[0] + p[0])/2., (v1[1] + p[1])/2.)
            mapping[vi1] = new_n

    # floor.projection_points = [(floor.vertices[vi],p) for vi, p in mapping.items()]

    for k, v in mapping.items():
        V[k] = v

    # Update edge lengths.
    for i, j, data in floor.edges_iter(data=True):
        data['length'] = dist(floor.vertices[i], floor.vertices[j])
        data['weight'] = 1e6 if data['inner'] or data['outside'] else data['length']

    floor.update_areas()