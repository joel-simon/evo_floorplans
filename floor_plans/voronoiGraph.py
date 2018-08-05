import sys, time, math
from collections import defaultdict
from itertools import combinations
import pyvoro

def norm(x, y):
    return math.sqrt(x*x + y*y)

def normalize(x, y):
    pass

class PhysicsBody(object):
    def __init__(self, ID, x, y, r):
        assert type(ID) is int
        self.ID = ID
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.
        self.vy = 0.
        self.ax = 0.
        self.ay = 0.
        self.r = r
        self.userData = {}
        self.stress = 1
        self.m = 1.

    def apply_force(self, fx, fy):
        self.ax += fx / self.m
        self.ay += fy / self.m

class SpringLayout(object):
    """docstring for SpringLayout"""
    def __init__(self, damping=0.3, verbose=False,
                minEnergyThreshold=.00005, timestep=0.01, max_steps=200):

        self.stiffness = 400
        self.damping   = damping
        self.minEnergyThreshold = minEnergyThreshold
        self.timestep  = timestep
        self.max_steps = max_steps
        self.verbose = verbose

        self.bodies = dict()
        self.edges = []
        self.last_energy = 0

    def _applyHookesLaw(self):
        for node1, node2, weight in self.edges:
            dx = node2.x - node1.x
            dy = node2.y - node1.y

            r = node1.r + node2.r
            d_norm = norm(dx, dy)

            if d_norm == 0:
                d_norm = 1

            displacement = r - d_norm
            f = (weight * self.stiffness) * displacement #(1 if displacement > 0 else -1)
            forcex = (dx / d_norm) * f * -.5
            forcey = (dy / d_norm) * f * -.5

            node1.apply_force(forcex, forcey)
            node2.apply_force(-1*forcex, -1*forcey)

    def _totalEnergy(self):
        energy = 0.0
        for node in self.bodies.values():
            speed = node.vx + node.vy
            energy += 0.5 * node.m * speed * speed

        return energy

    def _updateVelocityAndPositions(self):
        for node in self.bodies.values():
            node.vx += node.ax * self.timestep
            node.vy += node.ay * self.timestep

            node.ax = 0
            node.ay = 0

            node.vx *= 1 - self.damping
            node.vy *= 1 - self.damping

            node.x += node.vx * self.timestep
            node.y += node.vy * self.timestep

            # node.x = max(0.0, node.x)
            # node.y = max(0.0, node.y)
            # node.x = min(750.0, node.x)
            # node.y = min(750.0, node.y)

    def _distance(self, node_a, node_b):
        return math.sqrt(((node_a.x - node_b.x)**2) + ((node_a.y - node_b.y)**2))

    def _intersecting(self, node_a, node_b):
        return self._distance(node_a, node_b) < (node_a.r + node_b.r)

    def add_edge(self, id_a, id_b, weight):
        assert id_a != id_b
        self.edges.append((self.bodies[id_a], self.bodies[id_b], weight))

    def add_body(self, ID, x, y, r):
        body = PhysicsBody(ID, x, y, r)
        self.bodies[ID] = body
        return body

    def collide(self):
        for body1, body2 in combinations(self.bodies.values(), 2):
            x = body2.x - body1.x
            y = body2.y - body1.y
            r = body1.r + body2.r

            if x < r and y < r:
                l = norm(x, y)
                if l == 0:
                    x = 1
                    y = 1
                    l = 1
                if (l < r):
                    l = (r-l) / l * .5
                    x *= l
                    y *= l
                    body1.x -= x
                    body1.y -= y
                    body2.x += x
                    body2.y += y

    def step(self, view):
        self._applyHookesLaw()
        self._applyGravity()
        self._updateVelocityAndPositions()
        self.collide()
        if view is not None:
            view(self)

    def _applyGravity(self):
        for body in self.bodies.values():
            x = body.x - 750/2.
            y = body.y - 750/2.
            l = norm(x, y)
            if l != 0:
                body.apply_force(-(x/l)*body.m*10000, -(y/l)*body.m*10000)

    def finished(self, steps):
        if len(self.bodies) == 0:
            return True

        avg_energy = self._totalEnergy() / float(len(self.bodies))

        if self.verbose:
            print("Step:%i, avg_energy:%f" % (steps, avg_energy))

        if steps > self.max_steps:
            return True

        # if avg_energy < self.last_energy:
        #     if ((self.last_energy - avg_energy) < (self.last_energy*self.minEnergyThreshold) and steps > 2):
        #         return True

        self.last_energy = avg_energy

        return False

    def run(self, view=None):
        if self.verbose:
            print('Physics Starting')
        steps = 0

        while not self.finished(steps):
            self.step(view)
            steps += 1

        if self.verbose:
            print('Physics done')


