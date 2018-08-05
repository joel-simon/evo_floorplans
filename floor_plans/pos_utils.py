"""
Utilities for dictionaries of xy tuple values.
"""
from __future__ import print_function, division
import random
from collections import defaultdict

def center(pos, dimensions):
    x = [p[0] for p in pos.values()]
    y = [p[1] for p in pos.values()]

    minx, maxx = min(x), max(x)
    miny, maxy = min(y), max(y)

    dx = dimensions[0]/2. - ((maxx + minx)/2)
    dy = dimensions[1]/2. - ((maxy + miny)/2)

    for ID, p in pos.items():
        pos[ID] = (p[0]+dx, p[1]+dy)

def scale_offset(pos, scale=1, dx=0, dy=0):
    for ID, (x, y) in pos.items():
        x1 = x*scale + dx
        y1 = y*scale + dy
        pos[ID] = [x1, y1]

def fix_overlapping(pos, r=10):
    random.seed(0xDABBAD00)
    positions = defaultdict(set)
    ran = random.random
    for k, p in pos.items():
        tp = (int(p[0]), int(p[1]))
        positions[tp].add(k)

    for p, ks in positions.items():
        if len(ks) > 1:
            for k in ks:
                pos[k] = (pos[k][0]+ran()*r, pos[k][1]+ran()*r)

def get_center(pos):
    cx = 0#self.bounds[0]/2.
    cy = 0#self.bounds[1]/2.

    for body in self.world.bodies:
        cx += body.position[0]
        cy += body.position[1]
    cx /= len(self.world.bodies)
    cy /= len(self.world.bodies)
    return cx, cy


def rotate(pos, angle):
    # pos_matrix = np.array(pos.values())
    # rot_matrix = np.matrix(((math.cos(angle),-math.sin(angle)), (math.sin(angle), math.cos(angle))))
    center = get_center(pos)
    # for ID, (x, y) in pos.items():
    #     x1 = x-cx
    #     x2 = y-cy
    return {ID: rotate_point(center, p) for ID, p in pos.items()}
    # foo = {ID, x-cx, x}
