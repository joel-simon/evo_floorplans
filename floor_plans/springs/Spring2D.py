from .vector import Vect2D as Vect
from copy import copy

class World(object):
    """docstring for World"""
    def __init__(self, gravity=-10, resolve_steps=100):
        self.joints = []
        self.bodies = []
        self.gravity = Vect(0, gravity)
        self.resolve_steps = resolve_steps
        self.delta = 1.0 / self.resolve_steps

    def CreateStaticBody(self, **kwargs):
        self.bodies.append(StaticBody(**kwargs))
        return self.bodies[-1]

    def CreateDynamicBody(self, **kwargs):
        self.bodies.append(Body(**kwargs))
        return self.bodies[-1]

    def CreateDistanceJoint(self, bodyA, bodyB, **kwargs):
        joint = Joint(bodyA, bodyB)
        self.joints.append(joint)
        bodyA.joints.append(joint)
        bodyB.joints.append(joint)
        return self.joints[-1]

    def DestroyBody(self, body):
        assert(body in self.bodies)
        for joint in copy(body.joints):
            self.DestroyJoint(joint)
        self.bodies.remove(body)
        return

    def DestroyJoint(self, joint):
        if joint._destroyed:
            raise ValueError('Attempt to destroy a destroyed joint', joint)
        joint.bodyA.joints.remove(joint)
        joint.bodyB.joints.remove(joint)
        self.joints.remove(joint)
        joint._destroyed = True
        return

    def step(self):
        for j in range(self.resolve_steps):
            for joint in self.joints:
                joint.resolve()

            for body in self.bodies:
                body.accelerate(self.gravity)
                body.simulate(self.delta)

    def check_valid(self):
        """ Only used for debugging.
        """
        for joint in self.joints:
            assert(joint in joint.bodyA.joints)
            assert(joint in joint.bodyB.joints)

        for body in self.bodies:
            for joint in body.joints:
                assert(joint in self.joints)

class Body(object):
    """docstring for Body"""
    def __init__(self, x, y, mass=1.0, userData={}):
        self.position = Vect(x, y)
        self.previous = Vect(x, y)
        self.acceleration = Vect(0., 0.)
        self.userData = userData
        self.mass = mass
        self.joints = []

    def accelerate(self, vect):
        self.acceleration.iadd(vect)

    def correct(self, vect):
        self.position.iadd(vect)

    def simulate(self, delta):
        self.acceleration.imul(delta*delta)
        position = self.position.mul(2.).sub(self.previous).add(self.acceleration)
        self.previous = self.position
        self.position = position
        self.acceleration.zero()

class StaticBody(Body):
    def accelerate(self, vect):
        pass
    def correct(self, vect):
        pass
    def simulate(self, delta):
        pass

class Joint(object):
    """docstring for Joint"""
    def __init__(self, bodyA, bodyB, userData={}):
        assert(isinstance(bodyA, Body))
        assert(isinstance(bodyB, Body))
        assert(bodyA != bodyB)
        self.bodyA = bodyA
        self.bodyB = bodyB
        self.target = bodyA.position.distance(bodyB.position)
        self._destroyed = False
        self.userData = userData

    def resolve(self):
        assert(not self._destroyed)
        pos1 = self.bodyA.position
        pos2 = self.bodyB.position
        direction = pos2.sub(pos1)
        length = direction.length()
        factor = (length-self.target)/(length*2.1)
        correction = direction.mul(factor)

        self.bodyA.correct(correction)
        correction.imul(-1)
        self.bodyB.correct(correction)

    def GetReactionForce(self):
        assert(not self._destroyed)
        pos1 = self.bodyA.position
        pos2 = self.bodyB.position
        deviation = self.target - pos1.distance(pos2)
        return deviation * deviation
