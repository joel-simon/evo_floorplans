from collections import Counter, defaultdict

from pyhull.delaunay import DelaunayTri
from pyhull.convex_hull import ConvexHull

from floor_plans.math_util import dist

class InvalidHullException(Exception):
    def __str__(self):
        return('InvalidHullException')


def concave2(points, alpha):
    try:
        return _concave(points, alpha)
    except InvalidHullException as e:
        return _concave(points, alpha + 10)

def _concave(points, alpha):
    if len(points) <= 3:
        return points

    # Create delaunay triangulation.
    tri = DelaunayTri(points)

    # For each edge, count the number of faces that reference it.
    edge_counts = Counter()

    for (i, j, k) in tri.vertices:
        d1 = dist(tri.points[i], tri.points[j]) < alpha
        d2 = dist(tri.points[i], tri.points[k]) < alpha
        d3 = dist(tri.points[j], tri.points[k]) < alpha
        if (d1) and (d2) and (d3):
            edge_counts[tuple(sorted((i,j)))] += 1
            edge_counts[tuple(sorted((i,k)))] += 1
            edge_counts[tuple(sorted((j,k)))] += 1

    perim_edges = defaultdict(list) # Store vertices on perimeter.
    for (i, j), count in edge_counts.items():
        # If edge has one reference, it is on the perimeter.
        if count == 1:
            perim_edges[i].append(j)
            perim_edges[j].append(i)

    for i, vl in perim_edges.items():
        if len(vl) != 2:
            raise InvalidHullException()


    start_v = list(perim_edges.keys())[0]
    ordered_verts = [start_v]
    next_v = perim_edges[start_v][0]
    prev_v = start_v

    while next_v != start_v:
        ordered_verts.append(next_v)
        if perim_edges[next_v][0] != prev_v:
            prev_v = next_v
            next_v = perim_edges[next_v][0]
        else:
            prev_v = next_v
            next_v = perim_edges[next_v][1]
        perim_edges[prev_v].remove(next_v)
    return ordered_verts, (tri, edge_counts)


# def concave(points, radii):
#     if len(points) <= 3:
#         return points
#     min_r = min(radii)
#     # Create delaunay triangulation.
#     tri = DelaunayTri(points)

#     # Get exterior edges.
#     # For each edge, count the number of faces that reference it.
#     counts = Counter()
#     for (i, j, k) in tri.vertices:
#         d1 = dist(tri.points[i], tri.points[j]) < 1.5 * (radii[i] + radii[j])
#         d2 = dist(tri.points[i], tri.points[k]) < 1.5 * (radii[i] + radii[k])
#         d3 = dist(tri.points[j], tri.points[k]) < 1.5 * (radii[j] + radii[k])
#         if (d1) and (d2) and (d3):
#             counts[tuple(sorted((i,j)))] += 1
#             counts[tuple(sorted((i,k)))] += 1
#             counts[tuple(sorted((j,k)))] += 1

#     # Store vertices on perimeter.
#     vert_map = defaultdict(list)
#     for (i, j), count in counts.items():
#         if count == 1:
#             vert_map[i].append(j)
#             vert_map[j].append(i)

#     # for v in vert_map.values():
#     #     if len(v) != 2:
#     #         print(vert_map)
#     #         assert len(v) == 2

#     start_v = vert_map.keys()[0]
#     ordered_verts = [start_v]
#     next_v = vert_map[start_v][0]
#     prev_v = start_v
#     # next_v = vert_map[start_v][0]

#     while next_v != start_v:
#         # assert next_v not in ordered_verts
#         ordered_verts.append(next_v)
#         if vert_map[next_v][0] != prev_v:
#             prev_v = next_v
#             next_v = vert_map[next_v][0]
#         else:
#             prev_v = next_v
#             next_v = vert_map[next_v][1]

#     # ordered_points = [points[i] for i in ordered_verts]
#     # return ordered_points
#     assert(len(ordered_verts) == len(set(ordered_verts)))
#     return ordered_verts, (tri, counts)


def convex(points, radii):
    vertices = ConvexHull(points).vertices
    vert_map = defaultdict(list)

    for (i, j) in vertices:
        vert_map[i].append(j)
        vert_map[j].append(i)

    start_v = list(vert_map.keys())[0]
    ordered_verts = [start_v]
    next_v = vert_map[start_v][0]
    prev_v = start_v
    # next_v = vert_map[start_v][0]

    while next_v != start_v:
        # assert next_v not in ordered_verts
        ordered_verts.append(next_v)
        if vert_map[next_v][0] != prev_v:
            prev_v = next_v
            next_v = vert_map[next_v][0]
        else:
            prev_v = next_v
            next_v = vert_map[next_v][1]

    # ordered_points = [points[i] for i in ordered_verts]
    # return ordered_points
    return ordered_verts
