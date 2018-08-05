import math
class Vect2D(object):
    """docstring for Vect2D"""
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return "Vect2D(%f, %f)" % (self.x, self.y)

    def __repr__(self):
        return "Vect2D(%f, %f)" % (self.x, self.y)

    def __getitem__(self, index):
        if index ==0:
            return self.x
        elif index == 1:
            return self.y

    def isub(self, other):
        self.x -= other.x
        self.y -= other.y
        return self

    def sub(self, other):
        return Vect2D( self.x - other.x, self.y - other.y )

    def iadd(self, other):
        self.x += other.x
        self.y += other.y
        return self

    def add(self, other):
        return Vect2D( self.x + other.x, self.y + other.y )

    def imul(self, scalar):
        self.x *= scalar
        self.y *= scalar
        return self

    def mul(self, scalar):
        return  Vect2D( self.x * scalar, self.y * scalar )

    def idiv(self, scalar):
        self.x /= scalar
        self.y /= scalar
        return self

    def div(self, scalar):
        return  Vect2D( self.x / scalar, self.y / scalar )

    def normalized(self):
        x=self.x
        y=self.y
        length = math.sqrt(x*x + y*y)
        if length > 0:
            return  Vect2D(x/length, y/length)
        else:
            return Vect2D(0., 0.)

    def Normalize(self):
        return self.normalize()

    def normalize(self):
        x=self.x
        y=self.y
        length = math.sqrt(x*x + y*y)
        if length > 0:
            self.x = x/length
            self.y = y/length
        return self

    def length(self):
        return math.sqrt(self.x*self.x + self.y*self.y)

    def distance(self, other):
        x = self.x - other.x
        y = self.y - other.y
        return math.sqrt(x*x + y*y)

    def copy(self):
        return Vect2D(self.x, self.y)

    def zero(self):
        self.x = 0.
        self.y = 0.
        return self
