from __future__ import print_function, division

from math import atan2, cos, sin, pi, sqrt, hypot
from floor_plans import polygon, geometry
from floor_plans.math_util import mean, dist

def create_geometry(floor):
    """ given a graph where some edges are hallways,
        return a polygon object of the hallways
    """ 
    node_polys = []
    edge_polys = []

    offset = 0

    """ Every node in the hallway graph is given geoemtry of a cirlce.
    """
    for n in floor.nodes():
        # Node circles are average width of their neighbor edges.
        size = 0
        k = 0
        for n2 in floor.neighbors_iter(n):
            if floor.edge[n][n2]['width'] > 0 and not floor.edge[n][n2]['inner']:
                k += 1
                size = max(size, floor.edge[n][n2]['width'])

        if size > 0:
            circle = polygon.create_circle(floor.vertices[n], offset + size//2, n=16)
            if k > 1:
                node_polys.append(circle)
            # Dont add circles to graph leaves unless entrance.
            elif k == 1 and n in floor.outside_verts:
                node_polys.append(circle)
                # node_polys.append(polygon.clip(circle, floor.outside_polygon))

        floor.node[n]['size'] = size

    for i, j, data in floor.edges_iter(data=True):
        if data['width'] > 0 and not data['inner']:
            p1 = floor.vertices[i]
            r1 = offset + floor.node[i]['size'] // 2
            p2 = floor.vertices[j]
            r2 = offset + floor.node[j]['size'] // 2
            (p1, p2), (p3, p4) = geometry.outer_tangents(p1, r1, p2, r2)
            edge_polys.append([p1, p2, p4, p3])
    
    # For some reason the union on works properly when we union the edge 4gons first
    # and then union all the nodes (circles) on afterwards 
    # poly = max(polygon.union(polygon.union(edge_polys) + node_polys), key=len)

    # attempting to smooth polygon with double offsetting
    # if offset != 0:
    # print(len(poly))
    # poly = polygon.offset(poly, 2)
    # print(len(poly))
    # floor.door_locations = door_locations
    if len(edge_polys) ==0:
        return []
    return polygon.union(polygon.union(edge_polys) + node_polys)
