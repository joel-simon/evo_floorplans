from __future__ import division
import math
import pyclipper
from floor_plans.math_util import dist
from floor_plans.utilities import pairwise

def circumfrence(poly):
    return sum(dist(i, j) for i, j in pairwise(poly))

def clip(a, b):
    """ return polygon of a-b
    """
    if len(a) == 3: # triangle base case.
        return a

    pc = pyclipper.Pyclipper()
    try:
        pc.AddPath(a, pyclipper.PT_SUBJECT, True)
    except pyclipper.ClipperException as e:
        print(a)
        raise e
    try:
        pc.AddPath(b, pyclipper.PT_CLIP, True)
    except pyclipper.ClipperException as e:
        print(b)
        raise e

    paths = pc.Execute(pyclipper.CT_INTERSECTION, pyclipper.PFT_EVENODD, pyclipper.PFT_EVENODD)

    if len(paths) > 0:
        return paths[0]
    else:
        return a

def union(polygon_list):
    pc = pyclipper.Pyclipper()
    pc.AddPaths(polygon_list, pyclipper.PT_SUBJECT, closed=True)
    result = pc.Execute(pyclipper.CT_UNION, pyclipper.PFT_NONZERO, pyclipper.PFT_NONZERO)
    return result

def shoelace(point_list):
    """ The shoelace algorithm for polgon area """
    area = 0.0
    n = len(point_list)
    for i in range(n):
        j = (i + 1) % n
        area += (point_list[j][0] - point_list[i][0]) * \
                (point_list[j][1] + point_list[i][1])
    return area

def create_circle(center, radius, n=16):
    points = []
    cx, cy = center
    r = math.pi * 2.0 / n
    for i in range(n):
        x = (math.cos(r * i)*radius) + cx
        y = (math.sin(r * i)*radius) + cy
        points.append((x, y))
    return points

def center(point_list):
    x = [p[0] for p in point_list]
    y = [p[1] for p in point_list]
    minx, maxx = min(x), max(x)
    miny, maxy = min(y), max(y)

    dx = maxx/2 + minx/2
    dy = maxy/2 + miny/2
    return (dx, dy)


def area(point_list):
    return abs(shoelace(point_list)) / 2

def sorted_cw(point_list):
    if shoelace(point_list) > 0:
        return point_list
    else:
        return list(reversed(point_list))

def sorted_ccw(point_list):
    if shoelace(point_list) > 0:
        return list(reversed(point_list))
    else:
        return point_list

def offset(point_list, n):
    pco = pyclipper.PyclipperOffset()
    pco.AddPath(point_list, pyclipper.JT_SQUARE, pyclipper.ET_CLOSEDPOLYGON)
    return pco.Execute(n)[0]

def resolution_subdivide(point_list, n):
    new_points = []

    for i, p1 in enumerate(point_list):
        p2 = point_list[(i+1)%len(point_list)]
        new_points.append(p1)

        d = dist(p1, p2)
        num_div = int(d // n)
        step_x = (p2[0]-p1[0]) / num_div
        step_y = (p2[1]-p1[1]) / num_div
        for j in range(num_div-1):
            new_p = ((p1[0] + step_x*(j+1)), (p1[1] + step_y * (j+1)))
            new_points.append(new_p)

    return new_points

# pts = resolution_subdivide( [(0, 0), (1, 0), (1, 1), (0, 1)] , .25)
# print pts
# for i, p1 in enumerate(pts):
#   p2 = pts[(i+1)%len(pts)]

#   d = dist(p1, p2)
#   print d
    # num_div = int(d // n) - 1
    # print(d, num_div)


def sorted_clockwise(points):
    mlat = sum(p[0] for p in points) / float(len(points))
    mlng = sum(p[1] for p in points) / float(len(points))
    def algo(x):
        return (math.atan2(x[0] - mlat, x[1] - mlng) + 2 * math.pi) % (2*math.pi)
    return sorted(points, key=algo)
