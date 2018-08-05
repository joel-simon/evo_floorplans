from __future__ import division, print_function
import os, sys
import time
import math
from collections import Counter, defaultdict

from floor_plans.pygame_draw import PygameDraw

from floor_plans.math_util import dist
from floor_plans.concave_hull import concave2
from floor_plans import polygon

colors = defaultdict(lambda: (168, 231, 176))
import pygame
import pygame.gfxdraw
import Box2D

BLACK = (0,0,0)
WHITE = (255,255,255)
PURPLE = (231, 206, 245)
RED = (244, 157, 165)
BLUE = (202, 225, 239)

colors['entrance'] = (253, 251, 168)
colors['entrance'] = (50, 200, 50)
colors['hallway'] = (253, 251, 168) # Yellow
colors['toilet'] = (200, 200, 0)
colors['administration'] = RED
colors['playground'] = (230, 230, 230)
for name in ['cafeteria', 'stage', 'gym', 'library', 'faculty']:
    colors[name] = PURPLE

for name in ['boiler', 'kitchen', 'recycle', 'custodial', 'electrical',\
            'bldg/equip stoage']:
    colors[name] = BLUE

class View(PygameDraw):
    def __init__(self, *args, **kwargs):
        super(View, self).__init__(*args, **kwargs)
        self.load_image('door_single', 'floor_plans/img/semicircle16.png')
        # self.load_image('door_single', 'floor_plans/img/door_single64.png', (16, 16))
        self.load_image('door_double', 'floor_plans/img/door_double.png')

    def draw_physics_layout(self, physics_layout):
        self.surface.fill(WHITE)
        text = []
        
        for body in physics_layout.world.bodies:
            if body.userData is not None:
                p = (body.position[0]*10, body.position[1]*10)
                r = body.userData['r'] * 10
                self.draw_circle(p, r, (200, 200, 200), 0)
                # self.draw_circle(p, r, BLACK)
                # text.append((p, str(body.userData['label'])))

        for joint in physics_layout.world.joints:
            p1 = (joint.bodyA.position[0]*10, joint.bodyA.position[1]*10)
            p2 = (joint.bodyB.position[0]*10, joint.bodyB.position[1]*10)
            width = int(1 + 3*joint.userData['weight'])
            if isinstance(joint, Box2D.b2RopeJoint):
                self.draw_line(p1, p2, RED, 3)
            else:
                self.draw_line(p1, p2, RED, width)
        
        # Draw text over joints.
        for p, txt in text:
            self.draw_text(p, txt, center=True)

        self.end_draw()

    def draw_hallways(self, floor):
        for poly in floor.hallway_geometry:
            self.draw_polygon(poly, colors['hallway'])
            self.draw_polygon(poly, BLACK, 1)

    def draw_backgrounds(self, floor):
        # Room backgrounds.
        for ID, verts in floor.rooms.items():
            name = floor.room_names[ID]
            polygon = [floor.vertices[vi] for vi in verts]
            self.draw_polygon(polygon, colors[name])
            # self.draw_polygon(polygon, (200, 200, 200))

    def draw_outside_walls(self, floor):
         for vi, vj, edge in floor.edges_iter(data=True):
            p1 = floor.vertices[vi]
            p2 = floor.vertices[vj]

            color = colors['hallway'] if edge['width'] > 0 else (100, 100, 100)
            if edge['outside']: # outside wall
                self.draw_line(p1, p2, color, 2)

    def draw_walls(self, floor):
        # Walls.
        for vi, vj, edge in floor.edges_iter(data=True):
            p1 = floor.vertices[vi]
            p2 = floor.vertices[vj]

            # color = RED if edge['directed'] != None else BLACK
            color = colors['hallway'] if edge['width'] > 0 else (100, 100, 100)

            # if 'derp' in edge:
            #     color = RED

            # if edge['width'] and edge['inner']:
            #     print(vi, vj, edge)
            # if
            if edge['outside']: # outside wall
                pass

            elif edge['inner']:
                # pass
                pass
                # if edge['width'] > 0:
                #     self.draw_line(p1, p2, color, 1)
            else:
                if edge['width'] > 0:
                    pass
                    # self.draw_line(p1, p2, color, edge['width'])
                else:
                    self.draw_line(p1, p2, color, 1)

    def draw_room_text(self, floor):
        # #  # Room names
        for ID, verts in floor.rooms.items():
            name = floor.room_names[ID]
            x, y = polygon.center([floor.vertices[vi] for vi in verts])
            name = name.upper() if name != 'toilet' else 'T'
            self.draw_text((x, y), name[:5], color=BLACK, center=True)
            # self.draw_text((x, y), str(ID)+name[:5], color=BLACK, center=True) # FOR DEBUGGING.

    def draw_statistics(self, floor):
        if hasattr(floor, 'scores'):
            for i, (k,v) in enumerate(floor.scores.items()):
                y = i*15 + 20
                self.draw_text((150, y), k+': '+str(v), color=BLACK, font=18)

        if hasattr(floor, 'stats'):
            for i, (k,v) in enumerate(floor.stats.items()):
                y = i*15 + 20
                if v < 1:
                    s = k+': '+str(round(v, 4))
                else:
                    s = k+': '+str(int(v))
                self.draw_text((5, y), s, color=BLACK, font=18)

        txt = "First Floor: %s SF"%(format(int(floor.area), ','))
        self.draw_text((5, 5), txt, color=BLACK, font=18)


    def draw_doors(self, floor):
        door_width = 3

        if floor.door_locations == None:
            floor.create_door_locations(floor.hallway_geometry)

        for p, r, double in floor.door_locations:
            x, y = int(self.scale*p[0]), int(self.scale*p[1])
            width = int(door_width * self.scale)
            degrees = int(math.degrees(r+math.pi))
            if False:#double:
                pygame.gfxdraw.pie(self.surface, x, y, width, degrees, degrees+90, BLACK)
                pygame.gfxdraw.pie(self.surface, x, y, width, degrees, degrees-90, BLACK)
            else:
                pygame.gfxdraw.pie(self.surface, x, y, width, degrees, degrees+90, BLACK)

    def draw_entrances(self, floor):
        for i, v in enumerate(floor.entrances):
            self.draw_circle(floor.vertices[v], 3, BLACK, 0 if i==0 else 1)

    def draw_ruler(self, location=(500, 50)):
        x, y = location
        for x_ in [0, 8, 16, 24]:
            x2 = x + x_
            self.draw_line((x2+2, y+6), (x2+2, y+10), BLACK, 1)
            self.draw_text((x2,y),   str(x_), color=BLACK)

        # self.draw_line((x+10, y+6), (x+10, y+10), BLACK, 1)
        # self.draw_line((x+18, y+6), (x+18, y+10), BLACK, 1)

        # self.draw_text((x+8,y), '8', color=BLACK)
        # self.draw_text((x+16,y),'16', color=BLACK)

    def draw_voronoi_debug(self, floor):
        data = floor.debug_data
        # for cell in data['cells']:
        #     self.draw_polygon(cell, (200, 200, 200), 0)
        #     self.draw_polygon(cell, BLACK, 4)
        # return
        for p, r in zip(data['xy'], data['r']):
            self.draw_circle(p, r, (200, 200, 200), 0)
            self.draw_circle(p, r, BLACK)
            
        self.draw_polygon(data['hull'], RED, 5)
        self.draw_polygon(data['expanded_hull'], PURPLE, 5)
        for p in data['expanded_hull']:
            self.draw_circle(p, 5, PURPLE, 0)

    def draw_floorplan(self, floor, genome=None):
        self.surface.fill(WHITE)

        self.draw_backgrounds(floor)
        self.draw_doors(floor)
        self.draw_walls(floor)
        self.draw_outside_walls(floor)
        self.draw_hallways(floor)
        # self.draw_entrances(floor)
        self.draw_statistics(floor)
        self.draw_room_text(floor)
        self.draw_ruler()
        # self.draw_voronoi_debug(floor)

        # FOR DEBUGGING
        # for i, v in enumerate(floor.vertices):
        #     if i in floor.room_centers.values():
        #         self.draw_text(v, str(i), color=BLACK, center=True)

        self.end_draw()

