from __future__ import print_function, division

from math import atan2, cos, sin, pi, sqrt, hypot
from random import random

import pyvoro
from pyvoro import voroplusplus

from floor_plans.concave_hull import concave2, convex
from floor_plans import polygon, geometry
from floor_plans.math_util import mean, dist

def get_normals(hull):
    # Compute teh normals of each segment of the concave hull.
    normals = []
    for i, a in enumerate(hull):
        c = hull[(i+1)%len(hull)]
        x1, y1 = a
        x2, y2 = c
        dx = x2-x1
        dy = y2-y1
        derp = hypot(dx, dy)
        norm = [dy/derp, -dx/derp]
        normals.append(norm)
    return normals

def expand_hull(hull, hull_indexes, room_sizes, r=1):
    normals = get_normals(hull)
    expanded_hull = []
    derp = []
    for i in range(len(normals)):
        p1 = hull[i]
        p2 = hull[(i+1)%len(hull)]
        norm1 = normals[i]
        norm2 = normals[i-1]
        norm3 = [(norm1[0] + norm2[0])/2, (norm1[1] + norm2[1])/2]
        hyp = hypot(norm3[0], norm3[1])
        norm3[0] /= hyp
        norm3[1] /= hyp

        # Normal coming out of vertex
        r1 = r * room_sizes[hull_indexes[i]]
        hp1 = (p1[0] + norm3[0] * r1, p1[1] + norm3[1] * r1)

        # normal coming out of segment
        r2 = r * (room_sizes[hull_indexes[i]] + room_sizes[hull_indexes[(i+1)%len(hull)]])/2
        center = ((p1[0]+p2[0])/2., (p1[1]+p2[1])/2.)
        hp2 = (center[0] + norm1[0]*r2, center[1] + norm1[1] * r2)

        if hp1[0] > 0 and hp1[0] < 750 and hp1[1] > 0 and hp1[1] < 750:
            expanded_hull.append(hp1)
            derp.append(r1/2)

        if hp2[0] > 0 and hp2[0] < 750 and hp2[1] > 0 and hp2[1] < 750:
            expanded_hull.append(hp2)
            derp.append(r2/2)

    return expanded_hull, derp

def voronoi_cells(pos, node_genes, alpha=40, bounds=(750, 750)):
    """ Create a dict of room_id -> cell object with vertic information
    """
    room_ids = []
    room_xy = []
    room_sizes = []

    derp = []

    expanded_offset = 30

    for ID, (x,y) in pos.items():
        room_ids.append(ID)
        xi = min(bounds[0]-1, max(0, int(x)))
        yi = min(bounds[1]-1, max(0, int(y)))
        room_xy.append((xi, yi))
        r = node_genes[ID].size
        room_sizes.append(r)

        segment_length = 20.0
        circumference = 2 * pi * r
        steps = max(5, int(circumference/segment_length))
        derp.append((x, y))
        for i in range(steps):
            a = (i/float(steps)) * pi * 2.0
            derp.append((x+cos(a)*r, y+sin(a)*r))
            if r > segment_length:
                derp.append((x+cos(a)*r/2, y+sin(a)*r/2))

    hull = concave2(derp, alpha)[0]
    hull = [derp[i] for i in hull]

    expanded_hull1 = polygon.offset(hull, expanded_offset)

    if polygon.shoelace(hull) > 0:
       hull.reverse()

    radii = [node_genes[ID].size for ID in room_ids]

    for (x,y), r in zip(expanded_hull1, derp):
        if x > 0 and y > 0 and x < bounds[0] and y < bounds[1]:
            room_xy.append((int(x), int(y)))
            radii.append(expanded_offset)

    try:
        cells = pyvoro.compute_2d_voronoi(
          [(x, y) for x,y in room_xy],
          [[0.0, bounds[0]], [0.0, bounds[1]]],
          2.0, # Block size.
          radii
        )
    except voroplusplus.VoronoiPlusPlusError as e:
        raise e

    formatted_cells = dict()
    # expanded_hull_i = [(int(x), int(y)) for x, y in expanded_hull1]

    for i, room_id in enumerate(room_ids):
        cell = cells[i]
        verts_i = [(int(round(x)), int(round(y))) for x, y in cell['vertices']]
        formatted_cells[room_id] = verts_i

    return formatted_cells, {'expanded_hull': expanded_hull1, 'hull': hull,\
                             'cells': formatted_cells.values(), 'xy': room_xy, 'r': room_sizes}