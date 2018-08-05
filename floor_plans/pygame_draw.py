"""
    provide a consistent api around pygame draw functions
    using gfx draw when available (not pypy)
"""
import sys
import pygame
import math
BLACK = (0,0,0)

def rot_center(image, angle):
    """rotate an image while keeping its center and size"""
    orig_rect = image.get_rect()
    rot_image = pygame.transform.rotate(image, angle)
    rot_rect = orig_rect.copy()
    rot_rect.center = rot_image.get_rect().center
    rot_image = rot_image.subsurface(rot_rect).copy()
    return rot_image

class Draw(object):
    """docstring for Draw"""
    def __init__(self, w, h, scale=1, save_path=None):
        pygame.init()
        pygame.font.init()
        pygame.mixer.init()

        self.fonts = dict()
        # defaultdict(lambda n: pygame.font.SysFont("monospace", n))
        # self.fonts[12]
        # self.fonts[18]
        # self.font_small = pygame.font.SysFont("monospace", 12)
        # self.font_large = pygame.font.SysFont("monospace", 18)

        self.w = w
        self.h = h
        self.scale = scale
        self.surface = pygame.display.set_mode((w, h))
        self.images = dict()

        self.save_path = save_path
        if self.save_path:
            self.frame = 0


    def load_image(self, name, path, dimensions=None):
        myimage = pygame.image.load(path)
        if dimensions:
            w, h = dimensions
            myimage = pygame.transform.scale(myimage, (int(w*self.scale), int(h*self.scale)))
        myimage.convert()
        self.images[name] = myimage

    def draw_image(self, name, position, rotation=None):
        assert(name in self.images)
        # img = pygame.transform.scale(, (20, 20))
        # myimage, imagerect = self.images[name]
        # pygame.trasnformscale(Surface, (width, height), DestSurface = None)
        img = self.images[name]
        if rotation:
            img = rot_center(img, math.degrees(rotation))
            # img = pygame.transform.rotate(img, math.degrees(rotation))
        x, y = position
        self.surface.blit(img, (int(self.scale*x), int(self.scale*y)))

    def save(self, path):
        pygame.image.save(self.surface, path)
        # if self.save_path:
        #     path =  os.path.join(self.save_path, '{:04d}.jpg'.format(self.frame))
        #     pygame.image.save(self.surface, path)
        #     self.frame += 1

    def end_draw(self):
        pygame.display.flip()


    def hold(self):
        while True:
            for event in pygame.event.get():
              if event.type == pygame.QUIT:
                sys.exit()

try:
    # TODO: implement gfxdraw.
    raise ImportError
    import pygame.gfxdraw
    print('Using gfxdraw')
    class PygameDraw(Draw):
        """docstring for PygameDraw"""
        def draw_polygon(self, points, color, t=0):
            print(color)
            points = [(int(x*self.scale), int(y*self.scale)) for x,y in points]
            if t == 0:
                pygame.gfxdraw.aapolygon(self.surface, points, color)
            elif t == 1:
                pygame.gfxdraw.filled_polygon(self.surface, points, color)
            else:
                pygame.draw.polygon(self.surface, color, points, t)

        def draw_circle(self, position, radius, color, width=1):
            pos = (int(position[0]*self.scale), int(position[1]*self.scale))
            r  = int(radius*self.scale)
            if width == 0:
                pygame.gfxdraw.filled_circle(self.surface, pos[0], po[1], r, color)
            elif width == 1:
                pygame.gfxdraw.aacircle(self.surface, pos[0], po[1], r, color)
            else:
                pygame.draw.circle(self.surface, color, pos, r, width)

        def draw_line(self, positionA, positionB, color, width=1):
            positionA = (int(positionA[0]*self.scale), int(positionA[1]*self.scale))
            positionB = (int(positionB[0]*self.scale), int(positionB[1]*self.scale))
            if width == 1:
                x1, y1 = positionA
                x2, y2 = positionB
                pygame.gfxdraw.line(self.surface, x1, y1, x2, y2, color)
            else:
                pygame.draw.line(self.surface, color, positionA, positionB, int(width))


        def draw_lines(self, points, color, width=1):
            raise NotImplementedError()
            # points = [(int(x), int(y)) for x,y in points]
            # pygame.gfxdraw.lines(self.surface, color, False, points, width)

        def draw_rect(self, rect, color, width=1):
            rect = tuple(v*self.scale for v in rect)
            pygame.gfxdraw.rect(self.surface, color, rect, width)

        def draw_text(self, position, string, font=12, color=BLACK, center=False):
            if font not in self.fonts:
                self.fonts[font] = pygame.font.SysFont("monospace", font)
            text = self.fonts[font].render(string, 1, color)
            x = int(position[0]*self.scale)
            y = int(position[1]*self.scale)
            if center:
                w = text.get_rect().width
                h = text.get_rect().height
                self.surface.blit(text, (int(x-w/2.), int(y-h/2.)))
            else:
                self.surface.blit(text, (x, y))

except ImportError:
    class PygameDraw(Draw):
        """docstring for PygameDraw"""
        def draw_polygon(self, points, color, t=0):
            points = [(int(x*self.scale), int(y*self.scale)) for x,y in points]
            pygame.draw.polygon(self.surface, color, points, t)

        def draw_circle(self, position, radius, color, width=1):
            pos = (int(position[0]*self.scale), int(position[1]*self.scale))
            r  = int(radius*self.scale)
            width = int(width*self.scale)
            pygame.draw.circle(self.surface, color, pos, r, width)

        def draw_line(self, positionA, positionB, color, width=1):
            positionA = (int(positionA[0]*self.scale), int(positionA[1]*self.scale))
            positionB = (int(positionB[0]*self.scale), int(positionB[1]*self.scale))
            width = int(width*self.scale)
            pygame.draw.line(self.surface, color, positionA, positionB, width)

        def draw_lines(self, points, color, width=1):
            points = [(int(x), int(y)) for x,y in points]
            pygame.draw.lines(self.surface, color, False, points, width)

        def draw_rect(self, rect, color, width=1):
            rect = tuple(v*self.scale for v in rect)
            pygame.draw.rect(self.surface, color, rect, width)

        def draw_text(self, position, string, font=8, color=BLACK, center=False):
            font = int(self.scale * font)
            if font not in self.fonts:
                self.fonts[font] = pygame.font.SysFont("monospace", font)
            text = self.fonts[font].render(string, 1, color)
            x = int(position[0]*self.scale)
            y = int(position[1]*self.scale)
            if center:
                w = text.get_rect().width
                h = text.get_rect().height
                self.surface.blit(text, (int(x-w/2.), int(y-h/2.)))
            else:
                self.surface.blit(text, (x, y))
