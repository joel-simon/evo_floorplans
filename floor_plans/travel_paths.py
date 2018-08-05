from __future__ import print_function, division
from itertools import combinations
from collections import defaultdict
from floor_plans.dijkstra import dijkstra
import networkx as nx

# def shortest_room_path(floor, path_dists, paths, room1_id, room2_id):
#     return paths[floor.room_centers[room1_id]][floor.room_centers[room2_id]]

def all_paths(floor, weight='weight'):
    """
    """
    shortest_paths = {}
    shortest_path_dists = {}
    for vi in floor.room_centers.values():
        if floor.from_obj:
            # foo = set([c for ID, c in floor.room_centers.items() if floor.room_names[ID].lower() != 'hallway'])
            dists, paths = dijkstra(floor, [vi], weight, set())
        else:
            dists, paths = dijkstra(floor, [vi], weight, floor.room_centers.values())

        shortest_paths[vi] = paths
        shortest_path_dists[vi] = dists

    return shortest_path_dists, shortest_paths

def min_path(dists, paths, options):
    return paths[min(options, key=lambda v: dists[v] if v in dists else 999999)]

# def travel_loads(floor):
#     loads = dict()
        
#     for id1, id2 in combinations(list(floor.room_centers.values()), 2):


def betweenness_centrality(floor, path_dists, paths):
    n_rooms = len(floor.rooms)
    for id1, id2 in combinations(list(floor.rooms.keys()), 2):
        c1, c2 = floor.room_centers[id1], floor.room_centers[id2] 
        # if id1 not in public_ids and id2 not in public_ids:
        load = 2 * floor.population/(n_rooms**2)
        yield load, paths[c1][c2]

def public_foo(floor, path_dists, paths):
    public_names = set(['gym', 'cafeteria', 'playground'])
    n_rooms = len(floor.rooms)
    
    public_ids = set()
    for ID, name in floor.room_names.items():
        if name in public_names:
            public_ids.add(ID)
    
    for id1 in public_ids:
        p = 120
        c1 = floor.room_centers[id1]
        for id2 in floor.rooms:
            if id1 == id2:
                continue
            c2 = floor.room_centers[id2]
            load = p / n_rooms
            yield load, paths[c1][c2]

def between_class_paths2(floor, path_dists, paths):
    num_periods = 8
    
    homeroom_names = set(['1', '2', 'PK', 'K'])#, 'administration'])
    public_names = set(['gym', 'cafeteria', 'playground'])
    other_names = set(['title 1', 'tutoring', 'resource', 'autism', 'proj', 'music', 'art', 'life skills',
                            'computer lab', 'team'])
    """ Assumptions: 8 classes per day, 3 in homeroom, 1gym, 1cafeteria, 1 playground, 2 others
    
    """
    n_rooms = len(floor)

    homeroom_ids = set()
    public_ids = set()
    other_ids = set()
    toilet_ids = set()
    # administration_ids = set()
    max_students = dict()
    
    for ID, name in floor.room_names.items():
        if name in homeroom_names:
            homeroom_ids.add(ID)
        elif name in public_names:
            public_ids.add(ID)
        elif name in other_names:
            other_ids.add(ID)
        elif name  == 'toilet':
            toilet_ids.add(ID)

    # id_list = list(homeroom_ids)+list(public_ids) + list(other_ids) 
    students_homeroom = 3/8 * floor.population /  len(homeroom_ids)
    students_public = 3/8 * floor.population /  len(public_ids)
    students_other = 2/8 * floor.population /  len(other_ids)

    # print(students_homeroom, students_public, students_other)
    # toilet_centers = [floor.room_centers[ID] for ID in toilet_ids]    
    # print()
    for id1, id2 in combinations(list(floor.rooms.keys()), 2):
        c1, c2 = floor.room_centers[id1], floor.room_centers[id2] 
        
        # home <--> public
        if (id1 in homeroom_ids and id2 in public_ids) or (id2 in homeroom_ids and id1 in public_ids):
            load = 3/7*students_public + 3/7*students_homeroom

        # home <--> other
        elif (id1 in homeroom_ids and id2 in other_ids) or (id2 in homeroom_ids and id1 in other_ids):
            load = 2/7*students_homeroom + 3/7*students_other
        
        # other <--> public
        elif (id1 in homeroom_ids and id2 in public_ids) or (id2 in homeroom_ids and id1 in public_ids):
            load = 3/7*students_other + 2/7*students_public

        else:
            load = 2* floor.population/(n_rooms*n_rooms)

        yield load, paths[c1][c2]

def between_class_paths1(floor, path_dists, paths):
    occupied = set(['1', '2', 'PK', 'K', 'administration'])
    private_rooms = defaultdict(set)
    toilet_rooms = []
    common_rooms = []

    # Partition rooms ID's into three types.
    for ID, room in floor.rooms.items():
        name = floor.room_names[ID]
        if name in occupied:
            private_rooms[name].add(ID)
        elif name in 'toilet':
            toilet_rooms.append(ID)
        elif name != 'hallway':
            common_rooms.append(ID)

    toilet_centers = [floor.room_centers[ID] for ID in toilet_rooms]
    total_common_area = sum(a for ID, a in floor.room_sizes.items() if ID in common_rooms)

    a, b, c = 0,0, 0
    for name, others in private_rooms.items():
        for ID1 in others:
            center1 = floor.room_centers[ID1]
            if floor.room_names[ID1] == 'PK':
                continue # PK is an exception.

            # 60% going to other rooms of the same type
            load = .20 * (20.0 / (len(others) - 1))
            for ID2 in others:
                c1 = floor.room_centers[ID1]
                c2 = floor.room_centers[ID2]
                path = paths[c1][c2]
                yield (load, path)
                a += load
            # 40% going to common rooms (library, cafeteria, etc).
            for ID2 in common_rooms:
                load = .70 * 20.0 * (floor.room_sizes[ID2] / total_common_area)
                path = paths[floor.room_centers[ID1]][floor.room_centers[ID2]]
                yield (load, path)
                a += load
            # 10% of people go to the toilet. (.2 for their and back)
            # toilet_path = min_path(path_dists[center1], paths[center1], toilet_centers)
            # yield (.2 * 20, toilet_path)

    for ID1 in common_rooms:
        center1 = floor.room_centers[ID1]
        inthisroom = floor.population * (floor.room_sizes[ID] / total_common_area)

        # 50% going to common rooms (library, cafeteria, etc).
        for ID2 in common_rooms:
            load = .25 * inthisroom * (floor.room_sizes[ID2] / total_common_area)
            path = paths[floor.room_centers[ID1]][floor.room_centers[ID2]]
            yield (load, path)
            b += load
        # 10% of people go to the toilet. (.2 for their and back)
        toilet_path = min_path(path_dists[center1], paths[center1], toilet_centers)
        load = .25 * inthisroom
        yield (load, toilet_path)
        c += load
    # print(a, b, c)

def closest_paths(floor, path_dists, paths, vert_options):
    assert(len(vert_options))
    # s = 0
    for ID1, center1 in floor.room_centers.items():
        load = floor.population * (floor.room_sizes[ID1] / floor.area)
        # s += floor.room_sizes[ID1]
        path = min_path(path_dists[center1], paths[center1], vert_options)
        yield load, path

def entrance_paths(floor, path_dists, paths):
    """ Assuming even distribution of people """
    assert len(floor.entrances)
    for ID, center in floor.room_centers.items():
        """ Path to exit. """
        load = floor.population * (floor.room_sizes[ID] / floor.area)
        yield load, paths[center][floor.entrances[0]]
