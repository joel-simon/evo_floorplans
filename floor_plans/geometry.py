from __future__ import division
import math

def angle_between(a, b):
    x1, y1 = a
    x2, y2 = b
    dx = x2 - x1
    dy = y2 - y1
    rads = math.atan2(dy,dx)
    rads %= 2*math.pi
    return rads

def dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])

def det(a, b):
    return a[0] * b[1] - a[1] * b[0]

def ccw(A,B,C):
    return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])

def segment_intersect(A,B,C,D):
    # Return true if line segments AB and CD intersect
    return ccw(A,C,D) != ccw(B,C,D) and ccw(A,B,C) != ccw(A,B,D)

def line_intersection(line1, line2):
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

    div = det(xdiff, ydiff)
    if div == 0:
       return None

    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    return x, y


def is_left(a, b, c):
    """
    Where a = line point 1; b = line point 2; c = point to check against.
    If the formula is equal to 0, the points are colinear.
    If the line is horizontal, then this returns true if the point is above the line.
    """
    return (b[0] - a[0])*(c[1] - a[1]) > (b[1] - a[1])*(c[0] - a[0])

# def colinear(a, b, c):
#     print 'colinear', (b[0] - a[0])*(c[1] - a[1]) - (b[1] - a[1])*(c[0] - a[0])
#     return near(0, (b[0] - a[0])*(c[1] - a[1]) - (b[1] - a[1])*(c[0] - a[0]), 200)

def near(a, b, rtol=1e-5):
    return abs(a - b) < rtol

def poly_intersection(poly1, poly2):
    for i, p1_first_point in enumerate(poly1[:-1]):
        p1_second_point = poly1[i + 1]
        for j, p2_first_point in enumerate(poly2[:-1]):
            p2_second_point = poly2[j + 1]
            if line_intersection((p1_first_point, p1_second_point), (p2_first_point, p2_second_point)):
                return True
    return False

def outer_tangents(p1, r1, p2, r2):
    x1, y1 = p1
    x2, y2 = p2

    ang = math.atan2(y2-y1, x2-x1)
    po2 = math.pi / 2

    start1 = (x1 + math.cos(ang + po2)*r1, y1+math.sin(ang + po2)*r1)
    end1 = (x2 + math.cos(ang + po2)*r2, y2 + math.sin(ang + po2)*r2)

    start2 = (x1 + math.cos(ang - po2)*r1, y1+math.sin(ang - po2)*r1)
    end2 = (x2 + math.cos(ang - po2)*r2, y2 + math.sin(ang - po2)*r2)


    return ((start1, end1), (start2, end2))

def rotate_point(origin, point, angle):
    """
    Rotate a point counterclockwise by a given angle around a given origin.
    The angle should be given in radians.
    """
    ox, oy = origin
    px, py = point

    qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
    qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
    return qx, qy
