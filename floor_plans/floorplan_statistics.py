from collections import defaultdict
from itertools import combinations

from floor_plans.geometry import dist
from floor_plans.math_util import mean, dist
from floor_plans.dijkstra import dijkstra
from floor_plans import polygon
from floor_plans import travel_paths as pathing
from floor_plans.utilities import pairwise

def path_length(floor, path):
    return sum(floor[path[i]][path[i+1]]['length'] for i in range(len(path)-1))

def area(floor):
    return floor.area

def outside_wall_length(floor):
    return sum(d['length'] for i,j,d in floor.edges(data=True) if d['outside'])

def total_wall_length(floor):
    l = 0
    for i, j, data in floor.edges(data=True):
        if data['inner']:
            continue
        if data['outside']:
            l += data['length'] * 2
        elif data['width']:
            l -= data['length']
        else:
            l += data['length']
        # elif not data['inner'] or data['width']:
        #     l += data['length']
    l += sum(map(polygon.circumfrence, floor.hallway_geometry))
    return l

def average_daily_walking_distance(floor, path_dists, paths, classes_per_day=6):
    avg_room_distance = 0
    avg_entrance_distance = 0

    for load, path in pathing.betweenness_centrality(floor, path_dists, paths):
        avg_room_distance += path_length(floor, path)

    # for load, path in pathing.public_foo(floor, path_dists, paths):
    #     avg_room_distance += path_length(floor, path)

    for load, path in pathing.entrance_paths(floor, path_dists, paths):
        avg_entrance_distance += path_length(floor, path)

    # print(avg_room_distance)

    # assume everyone enters and leaves once.
    return (classes_per_day*avg_room_distance + 2*avg_entrance_distance) / floor.population

def total_hallway_area(floor):
    # return sum(map(polygon.area, floor.hallway_geometry))
    return sum(d['length']*d['width'] for i,j,d in floor.edges_iter(data=True) if not d['inner'])

def average_cluster_distance(floor, path_dists, paths):
    name_to_rooms = defaultdict(set)
    total_avg = 0

    # Find rooms types of which there re multiple rooms.
    for ID, room in floor.rooms.items():
        name = floor.room_names[ID].lower()
        if name in ['1', '2', 'pk', 'k', 'administration']:
            name_to_rooms[name].add(ID)

    centers = floor.room_centers.values()

    n = 0.
    for name, rooms in name_to_rooms.items():
        if len(rooms) > 1:
            n += 1
            avg = 0
            rid_pairs = list(combinations(rooms, 2))
            for a, b in rid_pairs:
                v1 = floor.room_centers[a]
                v2 = floor.room_centers[b]
                avg += path_length(floor, paths[v1][v2])

            total_avg += avg / float(len(rid_pairs))

    return total_avg/n


def toilet_dist(floor, path_dists, paths):
    ppt = defaultdict(int)
    toilet_centers = set([floor.room_centers[ID] for ID, name in floor.room_names.items() if name == 'toilet'])
    ctr = {c:ID for ID, c in floor.room_centers.items()}
    has_bathroom = set(['1', '2', 'PK', 'K'])
    needs_bathroom = [ID for ID,name in floor.room_names.items() if name not in has_bathroom]

    total_path_length = 0
    n = 0
    for ID in needs_bathroom:
        c = floor.room_centers[ID]
        path = pathing.min_path(path_dists[c], paths[c], toilet_centers)
        load = floor.population * (floor.room_sizes[ID] / floor.area)
        # load = floor.population * floor.room_sizes[ID] / len(floor.rooms)
        n += load
        total_path_length += path_length(floor, path)
        ppt[path[-1]] += load

    # for load, path in pathing.closest_paths(floor, path_dists, paths, vert_options=toilet_centers):
    #     total_path_length += load * path_length(floor, path)
    #     n += load
    foo = mean(v/floor.room_sizes[ctr[c]] for c, v in ppt.items())
    return (total_path_length / n), foo


    # n = 0    
    # total = 0
    # for load, path in pathing.between_class_paths(floor, path_dists, paths):
    #     if path[-1] in toilet_centers or path[0] in toilet_centers:
    #         n += load
    #         total += load*path_length(floor, path)
    #         if path[-1] in toilet_centers:
    #             ppt[path[-1]] += load
    #             # print(floor.room_names[ctr[path[0]]], path_length(floor, path))
    #         else:
    #             ppt[path[-1]] += load
    #             # print(floor.room_names[ctr[path[-1]]], path_length(floor, path))
    
    # # print 'm', mean(v/floor.room_sizes[ctr[c]] for c, v in ppt.items())
    # # for c, v in ppt.items():
    # #     print(c, v, floor.room_sizes[ctr[c]])
    # # print(ppt, mean(ppt.values()))
    # return((total / n), mean(v/floor.room_sizes[ctr[c]] for c, v in ppt.items()))

def window_area(floor):
    class_rooms = set(['computer lab', 'tutoring', 'title 1', 'work', \
                        'team', 'library', 'tutoring', 'conference', 'resource', \
                        '2', '1', 'pk', 'k', 'art', 'music', 'life skills', 
                        'faculty', 'library', 'administration', 'cafeteria'])
    foo = []
    for rid, verts in floor.rooms.items():
        if floor.room_names[rid].lower() not in class_rooms:
            continue

        total = 0
        outside = 0 
        for i, j in pairwise(verts):
            d = floor.edge[i][j]
            total += d['length']
            outside += d['length'] * d['outside']
        foo.append(outside/total)

    return mean(foo)

def avg_fire_escape_dist(floor, path_dists, paths):
    s = 0
    foo = 0
    for load, path in pathing.closest_paths(floor, path_dists, paths, vert_options=floor.entrances):
        s += load * path_length(floor, path)
        foo += load
    # print(foo)
    return s / foo
    # for ID, center in floor.room_centers.items():
    #     s += path_dists

def calculate_all(floor):
    path_dists, paths = pathing.all_paths(floor, weight='length')
    td, pptsf = toilet_dist(floor, path_dists, paths)
    stats = {
        'ha': total_hallway_area(floor),
        'wl': total_wall_length(floor),
        'ol': outside_wall_length(floor),
        'wd': average_daily_walking_distance(floor, path_dists, paths),
        'cd': average_cluster_distance(floor, path_dists, paths),
        'td': td,
        'fe': avg_fire_escape_dist(floor, path_dists, paths),
        'ta': pptsf,
        'wa': window_area(floor),
    }
    return stats


if __name__ == '__main__':
    import sys, pickle
    from floor_plans.floorplan import FloorPlan
    genome = pickle.load(open('/Users/joelsimon/Dropbox/floor_plans/test_genome.p', 'rb'))

    floor = FloorPlan.from_genome(genome)
    print(average_walking_distance(floor))
    print(total_wall_length(floor))
    print(outside_wall_length(floor))
