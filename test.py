from __future__ import print_function, division
import time

from floor_plans.visualize import View
from floor_plans.floorplan import FloorPlan
from floor_plans import polygon
from floor_plans.math_util import dist
from floor_plans import floorplan_statistics as fps


names = [
    'SPEECH', 'ST', 'COMP LAB', 'PK',
    'SUPER', 'FINANCE', 'ASST', 'SPED', 'BOILER',
    'ART', 'PK', 'PRINCIPLE', 'AP ASSISTANT PRINCIPLE', 'CONFERENCE',
    'G', 'G', 'WORK', 'DIS', 'VOL', 'STORAGE',
    'TOILET', 'CONF', 'CURR', 'WORK', 'SEC',
    'RECEPT', 'TOILET', 'hallway', 'STORAGE', 'STAGE',
    'KITCHEN', 'AUTISM', 'STORAGE', 'LIFE SKILLS', 'TOILET',
    'FACULTY', 'hallway', 'PROJ', 'CONF', 'LIT',
    'MATH', 'K', 'K', 'hallway', '2',
    '2', '2', '2', '1', '2',
    '1', '1', '1', '1', 'hallway',
    'hallway', 'TEAM', 'K', 'TITLE 1', 'TEST',
    'hallway', 'K', 'K', 'hallway', 'JANITORIAL',
    'TOILET', 'RR', 'hallway', 'STORAGE', 'NONE',
    'hallway', 'hallway', 'hallway', 'RESOURCE',
    'hallway', 'WORK', 'hallway', 'hallway', 'TOILET',
    'NURSE', 'WAIT', 'hallway', 'PK', 'LIBRARY',
    'EXAM', 'hallway', 'hallway', 'WORK', 'RECORDS',
    'EVAL', 'EVAL', 'TOILET', 'hallway', 'LOUNGE',
    'GYM STORAGE', 'hallway',
    'hallway',# 'entrance',
    'KILN', 'ART STORAGE',
    'MUSIC STORAGE', 'OT/PT', 'NONE', 'ELECTRICAL', 'MUSIC',
    'hallway', 'TOILET', 'GYM', 'hallway', 'CAFETERIA',
    'hallway', 'TOILET', 'hallway', 'TOILET','CONFERENCE3',
    'RECEPT2', 'CUSTODIAL', 'RECYCLE', 'hallway', 'hallway',
    'hallway', 'hallway', 'BLDG/EQUIP STORAGE', 'hallway', 'hallway',
    'hallway'
]
names = [n.lower() for n in names]

doors = [
    (43, 44, .5),
    (44, 45, .5),
    (45, 46, .5),
    (46, 47, .5),
    (47, 48, .5),
    (48, 49, .1),
    (19, 20, .5),
    (20, 21, .5),
    (21, 22, .5),
    (22, 23, .5),
    (23, 24, .5),
    (29, 30, .5),
    (65, 78, .5),
    (66, 65, .5),
    (67, 66, .5),
    (51, 44, .1),
    (20, 13, .1),
    (33, 29, .5),
    (35, 33, .1),
    (60, 64, .5),
    (59, 60, .5),
    (57, 59, .5),
    (39, 57, .5),
    (24, 69, .5),
    (248, 250, .5),
    (250, 251, .5),
    (49, 251, .5),
    (68, 77, .5),
    (64, 63, .5),
    (246, 247, .5),
    (70, 65, .1),
    (71, 66, 1),
    (29, 31, .1),
    (63, 37, .5),
    (76, 245, .5),
    (76, 246, .5),
    (25, 235, .5),
    (27, 236, .5),
    (74, 2, .9),
    (2, 3, .5),
    (2, 0, .5),
    (26, 28, .5),
    (26, 18, .5),
    (8, 10, .5),
    (10, 1, .5),
    (4, 9, .5),
    (23, 16, .5),
    (4, 253, .5),
    (28, 142, .5),
    (238, 240, .5),
    (243, 242, .5),
    (242, 84, .5),
    (208, 148, .9),
    (155, 213, .9),
    (207, 155, .5),
    (138, 223, .5),
    (214, 216, .5),
    (201, 138, .5),
    (216, 218, .5),
    (220, 203, .5),
    (221, 203, .5),
    (221, 255, .5),
    (139, 137, .1),
    (139, 137, .9),
    (152, 93, .5),
    (89, 91, .1),
    (89, 87, .5),
    (234, 232, .1),
    (234, 232, .9),
    (142, 144, .5),
    (53, 46, .1),
    (54, 47, .5),
    (21, 14, .5),
    (154, 145, .5),
    (153, 149, .5),
    (146, 139, .5),
    (150, 98, .5),
    (161, 163, .5),
    (161, 162, .5),
    (136, 137, .5),
    (178, 182, .5),
    (107, 106, .5),
    (157, 133, .5), # Entrance.
]

entrances = [352, 311, 299, 283, 376, 333, 365]

obj_path = 'school/floor1.obj'
bounds = (750, 750)
view = View(*bounds, scale=2)

source_upf = (39.645008 - 32.433640) / 24. # units per foot
# source_ppm = ppf / 0.3048 # pixels per meter

target_upf = 1.
scale =  target_upf / source_upf

floor = FloorPlan.from_obj(obj_path, names, doors, scale, entrances)

def merge_rooms(name, room_ids, verts):
    room_ids = set(room_ids)
    new_room_id = max(floor.rooms.keys())+1

    # Delete interior room nodes.
    for rid in room_ids:
        if floor.room_centers[rid] in floor:\
        # , floor.room_names[rid]
            floor.remove_node(floor.room_centers[rid])
        for vid in floor.rooms[rid]:
            if vid not in verts and vid in floor:
                floor.remove_node(vid)

    for ID in room_ids:
        del floor.rooms[ID]
        del floor.room_names[ID]
        del floor.room_centers[ID]
        for vid, rooms in floor.vert_to_room.items():
            if len(rooms.intersection(room_ids)):
                rooms -= room_ids
                rooms.add(new_room_id)

    poly = [floor.vertices[vi] for vi in verts]
    center = polygon.center(poly)
    center_i = len(floor.vertices)
    floor.vertices.append(center)
    
    floor.rooms[new_room_id] = verts
    floor.room_names[new_room_id] = name
    floor.room_centers[new_room_id] = center_i
    floor.room_sizes[new_room_id] = polygon.area(poly)

    return new_room_id

""" Merge administration room clusters together.
"""
# admin1_id = len(floor.rooms) # create new room ID.
# # IDs of rooms to merge
admin1_rooms = [113, 87, 88, 89, 90, 93, 92, 117, 114, 112, 4, 5, 6, 7, 22, 21, 23]
admin1_verts = [156, 170, 172, 174, 176, 178, 179, 183, 182, 180, 157, 168,
                167, 187, 229, 159, 185, 200, 198, 196, 194, 192, 190, 158,
                204, 254, 166, 169]

admin2_rooms = [25, 16, 17, 18, 19, 20, 80, 79, 84, 15, 14, 13, 12, 11, 24, 86]
admin2_verts = [133, 128, 129, 130, 165, 225, 131, 121, 107, 227, 226, 104,
                108, 122, 114, 113, 112, 111, 110, 109, 134, 230, 135, 132]
admin1_id = merge_rooms('administration', admin1_rooms, admin1_verts)
admin2_id = merge_rooms('administration', admin2_rooms, admin2_verts)

floor.add_edge(floor.room_centers[admin1_id], floor.room_centers[119], outside=False, inner=True, width=10)
floor.add_edge(floor.room_centers[admin2_id], floor.room_centers[81], outside=False, inner=True, width=10)

# try:
# print(fps.calculate_all(floor))
for k, v in fps.calculate_all(floor).items():
    print(k, v)
# except Exception as e:
#     print(e)

view.draw_floorplan(floor)
view.hold()
