"""
archived if needed later and dont want to go through git history
"""

# def pick_entrace(vl, vertices):
#     """ Select one vertex to be the entrance.
#         Take the one thats most center-bottom
#     """
#     minx, miny = vertices[vl[0]]
#     maxx, maxy = vertices[vl[0]]

#     for vi in vl:
#         x, y = vertices[vi]
#         minx = min(minx, x)
#         miny = min(miny, y)
#         maxx = max(maxx, x)
#         maxy = max(maxy, y)

#     halfw = (maxx - minx)/2
#     centerx = halfw + minx

#     def bottom_center(vi):
#         xy = vertices[vi]
#         center = abs(xy[0] - centerx) / halfw
#         bottom = 1 - ((xy[1]-miny) / (maxy - miny))
#         return (center + bottom)/2

#     return min(vl, key=bottom_center)


    # entrance_options = set()
    # for i, j, data in floor.edges_iter(data=True):
    #     if data['outside']:
    #         if len(vert_to_room[i]) > 1:
    #             entrance_options.add(i)
    #         if len(vert_to_room[j]) > 1:
    #             entrance_options.add(j)


       # def topologize(self, polygons):
        # def point_to_int(xy):
        # return (int(xy[0]), int(xy[1]))
    #     """
    #     Take a list of polygons that share points and return a well formed graph.
    #     Helper method for from_genome.

    #     return graph, vertices, and faces
    #     """
    #     vert_to_id = defaultdict(lambda: len(vert_to_id)) # Map vertices to global indexes.
    #     faces = defaultdict(list)
    #     vert_to_face = defaultdict(set)

    #     # room_centers = dict()
    #     # edges = []

    #     for ID, poly in polygons.items():
    #         # center_v = polygon.center(poly)
    #         # center_i = vert_to_id[center_v]
    #         # room_centers[ID] = center_i
    #         # vert_to_room[center_i].add(ID)

    #         for i, vert in enumerate(poly):
    #             vet = point_to_int(vert)
    #             vid = vert_to_id[vert]
    #             faces[ID].append(vid)
    #             vert_to_room[vid].add(ID)

    #             edges.append((vid, vert_to_id[verts[i-1]], {'outside':False, 'inner':False}))
    #             edges.append((vid, center_i, {'outside':False, 'inner':True}))


    # min_path = None
    # min_dist = None
    # dists = path_dists[floor.room_centers[room1_id]]
    # paths = paths[floor.room_centers[room1_id]]
    # c2 = floor.room_centers[room2_id]

    # for v in floor.rooms[room2_id]:
    #     if v in dists and floor.has_edge(v, c2):
    #         d = dists[v] + floor[v][c2]['weight']
    #         if (min_dist is None or d < min_dist) and len(paths[v]) > 2:
    #             min_dist = d
    #             min_path = paths[v]

    # if min_path is None: # edge case
    #     for v in floor.rooms[room2_id]:
    #         if v in dists and floor.has_edge(v, c2):
    #             d = dists[v] + floor[v][c2]['weight']
    #             if min_dist is None or d < min_dist:
    #                 min_dist = d
    #                 min_path = paths[v]

    # if min_path is None:
    #     print(floor.room_centers[room1_id], floor.room_centers[room2_id])
    #     print(floor.room_names[room1_id], floor.room_names[room2_id])
    #     raise ValueError()

    # return min_path + [c2]
    # min_path = None
    # min_dist = None
    # dists = path_dists[floor.room_centers[room1_id]]
    # paths = paths[floor.room_centers[room1_id]]
    # c2 = floor.room_centers[room2_id]

    # for v in floor.rooms[room2_id]:
    #     if v in dists and (min_dist is None or dists[v] < min_dist) and floor.has_edge(v, c2):
    #         min_dist = dists[v]
    #         min_path = paths[v]

    # if min_path is None:
    #     raise KeyError

    # return min_path + [c2]

def shortest_edge_with_vertex(floor, G, room_id, v):
    foo = []
    for i, j in floor.node[room_id]['outer_edges']:
        if i == v:
            foo.append(j)
        elif j == v:
            foo.append(i)

    if len(foo) == 1:
        return foo[0]
    elif G[v][foo[0]]['weight'] < G[v][foo[1]]['weight']:
        return foo[0]
    else:
        return foo[1]
    # if G[edge_a[0]][edge_a[1]]['weight'] < G[edge_b[0]][edge_b[1]]['weight']:
    #     return edge_a
    # else:
    #     return edge_b
