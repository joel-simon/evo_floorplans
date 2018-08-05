from __future__ import print_function, division
import random
import pickle
import math
# from math import atan2, cos, sin, pi
from collections import defaultdict, namedtuple
import networkx as nx

from floor_plans.math_util import mean, dist
from floor_plans.physicsLayout import PhysicsLayout
from floor_plans.voronoi import voronoi_cells
from floor_plans.obj import OBJ
from floor_plans import polygon, geometry
from floor_plans.hallways import create_hallways
from floor_plans.pos_utils import center, fix_overlapping, scale_offset, get_center
from floor_plans import floorplan_statistics as fps
from floor_plans.hallway_smoothing import smooth
from floor_plans.hallway_geometry import create_geometry
from floor_plans.utilities import pairwise

class UnconnectedGenomeException(Exception):
    """ Raised a genetic mutation causes the genome graph to not be connected.
    """
    def __str__(self):
        return('UnconnectedGenomeException')

class InvalidContraintException(Exception):
    """ Raised when two rooms that need to be adjacent are not.
    """
    def __str__(self):
        return('InvalidContraintException')

def derp(pos, genome):
    for conn in genome.conn_genes.values():
        if conn.fixed:
            x1, y1 = pos[conn.in_node_id]
            x2, y2 = pos[conn.out_node_id]
            # print(x1, y1, x2, y2)
            cx, cy = (x1+x2)/2., (y1+y2)/2.
            pos[conn.in_node_id] = (cx, cy)
            pos[conn.out_node_id] = (cx, cy)

class FloorPlan(nx.Graph):
    """ A FloorPlan is a graph where nodes are rooms and edges
        exist between adjacent rooms to represent doors.

        node: [name, area, position, vertices, accessible]
        edge: [weight=distance, doors:[(veri0, vertj)]]
    """
    def __init__(self, vertices, rooms, room_names, vert_to_room, room_centers,
                 entrances, smooth_hallways=True):
        super(FloorPlan, self).__init__()
        self.area = 0
        self.population = 360 + 40# TODO: dont hardcode (=20*n_classrooms + 40 faculty)
        self.vertices = vertices
        self.rooms = rooms
        self.room_names = room_names
        self.vert_to_room = vert_to_room
        self.room_centers = room_centers
        self.entrances = entrances
        self.room_sizes = None
        self.door_locations = None
        self.outside_verts = []
        self.hallway_geometry = []
        self.update_areas()
        self.phenotype = None
        self.from_obj = False
        self.smooth_hallways = smooth_hallways
        # self.firescapes = firescapes

    def update_areas(self):
        self.room_sizes = dict()
        self.area = 0
        for ID, vl in self.rooms.items():
            area = polygon.area([self.vertices[vi] for vi in vl])
            # if self.room_names[ID] != 'playground':
            self.room_sizes[ID] = area
            self.area += area
            # else:
            #     self.room_sizes[ID] = 0

    # def inner_edges(self, room_id):
    #     """ yield (i, j, data) edge tuples
    #     """
    #     cv = self.room_centers[room_id]
    #     for v in self.rooms[room_id]:
    #         if self.has_edge(cv, v):
    #             yield cv, v, self.edge[cv][v]

    def calc_outisde_edges(self, not_outside=set()):
        # nextv = dict()
        # print(not_outside)
        outside_v = set()
        for a, b, data in self.edges_iter(data=True):
            if not data['inner']:# and (a in not_outside and b in not_outside):
                rooms = list(self.vert_to_room[a].intersection(self.vert_to_room[b]))
                one_is_playground = False
                if len(rooms) == 2:
                    if self.room_names[rooms[0]] == 'playground' or self.room_names[rooms[1]] == 'playground':
                        one_is_playground = True
                if (len(rooms) == 1 and not self.room_names[rooms[0]] == 'playground') or (len(rooms) == 2 and one_is_playground):
                    self.edge[a][b]['outside'] = True
                    outside_v.add(a)
                    outside_v.add(b)

        self.outside_verts = outside_v.difference(not_outside)

        # for rid, verts in self.rooms.items():
        #     if self.room_names[rid] == 'empty':
        #         self.outside_verts.difference_update(verts)

        # for ID, name in self.room_names.items():
        #     if name == 'empty':
        #         edges = list(pairwise(self.rooms[ID]))
        #         for i, j in edges:
        #             rooms = self.get_edge_rooms(i, j)
        #                 if gs


        # outside_polygon = [self.vertices[i] for i in list(outside_v)]
        # self.outside_polygon = polygon.sorted_clockwise(outside_polygon)
        # outside_verts = []
        # used = set()
        # for i, j in

    def get_edge_rooms(self, i, j):
        """ Return the rooms that share this edge.
            Will be 1 or 2 rooms.
        """
        rooms = self.vert_to_room[i].intersection(self.vert_to_room[j])
        assert(len(rooms)) # if no rooms, then i,j is not a valid edge
        return rooms

    def get_rooms_edge(self, room1_id, room2_id):
        """ Return the edge that two rooms share,
            will be None if no such edge exists (rooms not adjacent)
        """
        room1_edges = set(pairwise(self.rooms[room1_id]))
        room2_edges = set(pairwise(reversed(self.rooms[room2_id])))

        vl = set(self.rooms[room1_id]).intersection(set(self.rooms[room2_id]))
        if len(vl) != 2:
            return None
        else:
            i, j = vl
            return i, j, self.edge[i][j]

    def add_edge(self, i, j, **kwargs):
        length = dist(self.vertices[i], self.vertices[j])
        if 'length' not in kwargs:
            kwargs['length'] = length
        if 'between_fixed' not in kwargs:
            kwargs['between_fixed'] = False
        if 'outside' not in kwargs:
            kwargs['outside'] = False
        # if 'directed' not in kwargs:
        #     kwargs['directed'] = None
        if 'width' not in kwargs:
            kwargs['width'] = 0
        super(FloorPlan, self).add_edge(i, j, weight=length,  **kwargs)


    def add_adjacent_room_edges(self, others):
        """ For rooms of the same type that also share a wall, connect with door
        """
        for i, j, data in self.edges(data=True):
            # Find the two rooms that this door connects
            rl = self.get_edge_rooms(i, j)
            if len(rl) == 2 and data['width'] == 0:
                r1, r2 = rl
                c1, c2 = self.room_centers[r1], self.room_centers[r2]
                v1, v2 = self.vertices[c1], self.vertices[c2]
                if self.room_names[r1] == self.room_names[r2] and dist(v1, v2) > 4:
                    self.add_edge(c1, c2, width=4, inner=True, outside=False)

        for ID1, ID2 in others:
            self.add_edge(self.room_centers[ID1], self.room_centers[ID2], width=4, inner=True, outside=False)


    def create_door_locations(self, hallway_polygon):
        self.door_locations = []
        room_centers = set(self.room_centers.values())
        center_to_room = { c:ID for ID, c in self.room_centers.items() }

        for n1, n2, data in self.edges(data=True):
            if data['inner'] and data['width'] > 0:
                n1_center = n1 in room_centers
                n2_center = n2 in room_centers

                if n1_center and n2_center: # If a room-to-room door.
                    n3, n4, d = self.get_rooms_edge(center_to_room[n1], center_to_room[n2])
                    v1, v2 = self.vertices[n3], self.vertices[n4]
                    if dist(v1, v2) > 4: # Need 4 feet for door
                        angle = (geometry.angle_between(v1, v2) + math.pi/2)# % 2*pi
                        pos = ((v1[0]+v2[0])/2, (v1[1]+v2[1])/2)
                        self.door_locations.append((pos, angle, False))

                elif n1_center and n2 in self.outside_verts or n2_center and n1 in self.outside_verts:
                    # Door to outside.
                    n_out, n_cent = (n2, n1) if n1_center else (n1, n2)
                    if len(self.vert_to_room[n_cent]) == 1:
                        v1, v2 = self.vertices[n_out], self.vertices[n_cent]
                        angle = geometry.angle_between(v1, v2) - math.pi /2
                        self.door_locations.append((v1, angle, True))
                else: # A room to hallway door
                    v1, v2 = self.vertices[n1], self.vertices[n2]
                    for poly in hallway_polygon:
                        for i, v3 in enumerate(poly):
                            v4 = poly[i-1]
                            if geometry.segment_intersect(v1, v2, v3, v4):
                                pos = ((v3[0]+v4[0])/2, (v3[1]+v4[1])/2)
                                dl = (pos, geometry.angle_between(v4, v3), True)
                                self.door_locations.append(dl)
            # elif data['width']:
            #     n1_out = n1 in self.outside_verts
            #     n2_out = n2 in self.outside_verts
            #     v1, v2 = self.vertices[n1], self.vertices[n2]
            #     if n1_out:
            #         dl = (v1, geometry.angle_between(v1, v2), True)
            #     else:
            #         dl = (v2, geometry.angle_between(v2, v1), True)

            #     self.door_locations.append(dl)


    @classmethod
    def from_genome(cls, genome, firescapes=False, view=None, cache=True):
        if genome.phenotype is not None and cache:
            return genome.phenotype
        G = genome_to_graph(genome) # First create a graph representation.
        pos = nx.spectral_layout(G) # Create with spectral layout of graph.
        scale_offset(pos, dx=75, dy=75, scale=600)
        fix_overlapping(pos) # Prevent overlapping points.
        center(pos, dimensions=(750, 750))
        pos = physics_layout(G, pos, view) # Apply physics simulation.
        center(pos, dimensions=(750, 750))
        if 'concave_alpha' in genome.attribute_genes:
            a = genome.attribute_genes['concave_alpha'].value
        else:
            a = 40
        cells, debug_data = voronoi_cells(pos, genome.node_genes, a) # Room walls by voronoi tesselation.
        vert_to_id = defaultdict(lambda: len(vert_to_id)) # Map vertices to global indexes.
        rooms = defaultdict(list)
        vert_to_room = defaultdict(set)
        room_names = dict()
        room_centers = dict()
        edges = []

        no_outside = set()

        for ID, verts in cells.items():
            gene = genome.node_genes[ID]
            # print(gene.name)
            if gene.name == 'empty' or gene.name == 'playground':
                no_outside.update(set([vert_to_id[vert] for vert in verts]))
                if gene.name == 'empty':
                    continue

            center_v = polygon.center(verts)
            center_i = vert_to_id[center_v]
            room_centers[ID] = center_i
            vert_to_room[center_i].add(ID)
            room_names[ID] = gene.name

            # if gene.name == 'playground':
            #     continue

            for i, vert in enumerate(verts):
                vid = vert_to_id[vert]# voronoi points are integers and thus hashable.
                rooms[ID].append(vid)

                vert_to_room[vid].add(ID)
                if gene.name != 'playground':
                    edges.append((vid, vert_to_id[verts[i-1]], {'inner':False}))
                edges.append((vid, center_i, {'inner':True, 'directed': None}))


        vertices = sorted(vert_to_id.keys(), key=lambda v:vert_to_id[v])
        floor = cls(vertices, dict(rooms), room_names, vert_to_room, room_centers, entrances=[])
        floor.debug_data = debug_data # temporary

        for i, j, data in edges: # add edges.
            floor.add_edge(i, j, **data)

        floor.calc_outisde_edges(no_outside)

        # Remove edges that connect centers to outside
        # for ri, vc in floor.room_centers.items():
        #     if room_names[ri] in ['cafeteria', 'library', 'gym']:
        #         continue
        #     verts = rooms[ri]
        #     out = [v for v in verts if v in floor.outside_verts]
        #     if len(out) == len(verts):
        #         continue
        #     for v in out:
        #         if floor.has_edge(vc, v):
        #             floor.remove_edge(vc, v)

        # for v in floor.outside_verts:
        #     for ri in vert_to_room[v]:
        #         if room_names[ri] not in ['cafeteria', 'library', 'gym'] and \
        #             len(room_centers[ri]):
        #             vc = room_centers[ri]
        #             floor.remove_edge(v, vc)

        # new_polygons = []
        # for ID, face in floor.rooms:
        #     polygon = [floor.vertices[vi] for vi in face]
        #     clipped = poylgon.clip(polygon, floor.hallway_geometry)
        #     new_polygons.append(clipped)

        # self.topologize(new_polygons)

        """ Prevent adjacency requirements from having a hallway between them.
        """
        for conn in genome.conn_genes.values():
            if conn.fixed:
                room1_id = conn.in_node_id
                room2_id = conn.out_node_id
                edge = floor.get_rooms_edge(room1_id, room2_id)
                if edge:
                    i, j, data = edge
                    data['between_fixed'] = True
                else:
                    raise InvalidContraintException()

        alpha = genome.attribute_genes['hallway_alpha'].value
        decay = genome.attribute_genes['hallway_decay'].value
        if 'fe_weight' in genome.attribute_genes:
            fe_weight = genome.attribute_genes['fe_weight'].value
        else:
            fe_weight = .2
        create_hallways(floor, alpha=alpha, pheromone_decay=decay, iters=10, fe_weight=fe_weight,\
                        verbose=False, firescapes=firescapes)

        for i, j, d in floor.edges(data=True):
            if d['between_fixed'] and d['width']:
                raise InvalidContraintException()

        cx = mean([x for x, y in floor.vertices])
        cy = mean([y for x, y in floor.vertices])
        x1, y1 = floor.vertices[floor.entrances[0]]
        angle = -math.atan2(y1-cy, x1-cx) + math.pi/2
        floor.vertices = [geometry.rotate_point((cx, cy), p, angle) for p in floor.vertices]

        floor.add_adjacent_room_edges([(c.in_node_id, c.out_node_id) for c in genome.conn_genes.values() if c.fixed])
        smooth(floor)
        floor.hallway_geometry = create_geometry(floor)
        floor.stats = fps.calculate_all(floor)
        return floor

    @classmethod
    def from_obj(cls, obj_path, names, doors, scale, entrances):
        # floor = cls()
        obj = OBJ(obj_path, swapyz=True)

        vertices = [(v[0]*scale, v[1]*scale) for v in obj.vertices] #apply scale and remove 3rd dimension.

        vert_to_room = defaultdict(set)
        edge_to_room = defaultdict(set)

        rooms = defaultdict(list)
        vert_to_room = defaultdict(set)
        room_names = dict()
        room_centers = dict()
        edges = []

        for room_id, (face, name) in enumerate(zip(obj.faces, names)):
            face = [i-1 for i in face[0]] # change to 0 start counting.
            rooms[room_id] = face
            room_names[room_id] = name

            poly = [vertices[i] for i in face]
            room_centers[room_id] = len(vertices)
            vertices.append(polygon.center(poly))

            for i, vi in enumerate(face):
                vert_to_room[vi].add(room_id)
                edge_attr = {'outside':False, 'inner':False, 'width':0}
                edges.append((vi, face[i-1], edge_attr))

        floor = cls(vertices, rooms, room_names, vert_to_room, room_centers, entrances)
        floor.from_obj = True
        for i, j, data in edges:
            floor.add_edge(i, j, **data)

        floor.calc_outisde_edges()

        floor.door_locations= []
        for vi1, vi2, p in doors:
            # Find the two rooms that this door connects
            rid1, rid2 = vert_to_room[vi1].intersection(vert_to_room[vi2]) # must be two.

            v1, v2 = vertices[vi1], vertices[vi2]
            vi_door = len(vertices) # create new node for door.
            v_door = ((v1[0]+v2[0])/2., (v1[1]+v2[1])/2.)

            vertices.append(v_door)
            edge_attr = {'outside':False, 'inner':True, 'width':10}
            floor.add_edge(room_centers[rid1], vi_door, **edge_attr)

            edge_attr = {'outside':False, 'inner':True, 'width':10}
            floor.add_edge(vi_door, room_centers[rid2], **edge_attr)

        # Connect adjacent .
        for vi1, vi2 in floor.edges():
            rooms = vert_to_room[vi1].intersection(vert_to_room[vi2])
            if len(rooms) == 2:
                ri, rj = rooms
                if room_names[ri] == room_names[rj] and room_names[ri].lower() == 'hallway':
                    vi, vj = room_centers[ri], room_centers[rj]
                    floor.add_edge(vi, vj, outside=False, inner=True, width=10)

        return floor

def genome_to_graph(genome):
    G = nx.Graph()

    for node_id, ng in genome.node_genes.items():
        G.add_node(node_id, name=ng.name, size=ng.size)

    for conn in genome.conn_genes.values():
        G.add_edge(conn.in_node_id, conn.out_node_id, weight=conn.weight, fixed=conn.fixed)

    subgraphs = list(nx.connected_components(G))
    # print(subgraphs)
    # print(len(subgraphs))
    if len(subgraphs) != 1:
        # print(map(list, subgraphs))
        for g1, g2 in pairwise(map(list, subgraphs)):
            # print(g1[-1], g2[0])
            G.add_edge(g1[-1], g2[0], weight=.25, fixed=False)
    # if not nx.is_connected(G):
    #     raise UnconnectedGenomeException()

    return G

def physics_layout(G, starting_position, view=None):
    scale = 1/10.
    physics = PhysicsLayout(max_steps=25, bounds=(750*scale, 750*scale))

    for ID, data in G.nodes(data=True):
        x = starting_position[ID][0] * scale
        y = starting_position[ID][1] * scale
        r = data['size'] * scale
        physics.add_body(ID, (x, y), r, label=data['name'])

    for i, j, d in G.edges(data=True):
        # if d['fixed']:
        #     physics.add_hard_edge(i, j)
        # else:
        physics.add_edge(i, j, d['weight'], fixed=d['fixed'])

    # # The order of which things are added to Box2D is very important!
    # # If sorting not defined, results will not be consistent and vary across pickling
    # for ID, p in sorted(starting_position.items()):
    #     name = genome.node_genes[ID].name
    #     r = genome.node_genes[ID].size
    #     physics.add_body(ID, (p[0]*scale, p[1]*scale), r*scale, label=name)

    # for conn in sorted(genome.conn_genes.values(), key=lambda c: c.key):
    #     if conn.fixed:
    #         physics.add_hard_edge(conn.in_node_id, conn.out_node_id)
    #     else:
    #         physics.add_edge(conn.in_node_id, conn.out_node_id, conn.weight, fixed=conn.fixed)

    physics.run(view=view)

    foo = { ID: b.position/scale for ID, b in physics.bodies.items() }
    return (foo)
