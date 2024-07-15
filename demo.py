import random
from enum import Flag

# See https://raw.githubusercontent.com/pybox2d/pybox2d/master/library/Box2D/examples/simple/simple_01.py
import pygame
import Box2D
from pygame.locals import (QUIT, KEYDOWN, K_ESCAPE, K_a, K_d, K_w, K_s, KEYUP, K_q)

from model import *
from settings import *


# Create the world
world = Box2D.b2World(gravity=(0, -10), doSleep=True)

kinematic_rect = KinematicRectangle(world, (100, 350), (120, 50),                                (100, 100, 250, 255))
dynamic_rect =   DynamicRectangle(  world, (200, 250), (25, 45), CollisionInfo(restitution=0.7), (100, 150, 150, 255))

kinematic_circle = KinematicCircle(world, (370, 275), 25,                                 (50, 200, 250, 255))
mouse_ball =       KinematicCircle(world, (500, 150), 10                                                     )
dynamic_circle =   DynamicCircle(  world, (150, 250), 30, CollisionInfo(restitution=0.7), (100, 255, 150, 255)).set_velocity((350, -450))

kinematic_line = KinematicLine(world, (30, 20), (130, 100), (255, 90, 255, 255))

octogon = [
    (300, 80),
    (320, 80),
    (340, 100),
    (340, 120),
    (320, 140),
    (300, 140),
    (280, 120),
    (280, 100),
]
kinematic_polygon = KinematicPolygon(world, octogon, (145, 100, 160, 255))

game_objects = [
    StaticLine(world, (10,                10                ), (SCREEN_WIDTH - 10, 10                ), colour=(255, 150, 100, 255)),
    StaticLine(world, (SCREEN_WIDTH - 10, 10                ), (SCREEN_WIDTH - 10, SCREEN_HEIGHT - 10), colour=(255, 150, 100, 255)),
    StaticLine(world, (SCREEN_WIDTH - 10, SCREEN_HEIGHT - 10), (10,                SCREEN_HEIGHT - 10), colour=(255, 150, 100, 255)),
    StaticLine(world, (10,                SCREEN_HEIGHT - 10), (10,                10                ), colour=(255, 150, 100, 255)),
    DynamicLine(world, (10, 10), (100, 10), CollisionInfo(restitution=1), (255, 255, 90, 255)),
    StaticCircle(   world, (320, 275), 25, (50, 255, 150, 255)).set_velocity(( 35, -45)),
    StaticRectangle(world, (230, 250), (25, 45), (100, 100, 150, 255)),
    StaticPolygon(world, octogon,                   (45, 190, 100, 255)),
    DynamicPolygon(world, octogon, CollisionInfo(), (45, 190, 100, 255)),
    dynamic_rect,
    kinematic_rect,
    kinematic_circle,
    dynamic_circle,
    kinematic_line,
    mouse_ball,
    kinematic_polygon,
]


# region Collision Groups

class CollisionGroup(Flag):
    NoCollision = 0
    Default = auto()
    SecondGroup = auto()
    ThirdGroup = auto()

    @classmethod
    def ALL(cls):
        # From https://stackoverflow.com/a/78229655
        return ~CollisionGroup(0)

for game_obj in game_objects:
    game_obj.set_collision_group(CollisionGroup.Default, CollisionGroup.ALL())

dynamic_circle.set_collision_group(CollisionGroup.SecondGroup, CollisionGroup.Default)
mouse_ball.set_collision_group(CollisionGroup.ThirdGroup,      CollisionGroup.Default)

# endregion


def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)
    pygame.display.set_caption("Simple pygame example")
    clock = pygame.time.Clock()
    
    io = KeyQuery()
    shape_registry = ShapeRegistry(world)
    shape_registry.add(game_objects)
    
    running = True
    while running:
        io.clear_pressed()
        io.mark_mouse_relative(pygame.mouse.get_rel())
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                running = False
                break

            if event.type == KEYDOWN:
                io.mark_pressed(event.key)
            elif event.type == KEYUP:
                io.mark_released(event.key)


        left_right = int(io.is_key_down(K_d)) - int(io.is_key_down(K_a))
        up_down    = int(io.is_key_down(K_s)) - int(io.is_key_down(K_w))

        kinematic_rect.set_velocity((left_right * 400, up_down * 400))
        kinematic_line.set_velocity((left_right * 400, up_down * 400))
        kinematic_circle.set_velocity((left_right * 400, up_down * 400))
        kinematic_polygon.set_velocity((left_right * 400, up_down * 400))
        
        mouse_relo = (
            io.get_mouse_relative()[0] * TARGET_FPS,
            io.get_mouse_relative()[1] * TARGET_FPS,
        )
        mouse_ball.set_velocity(mouse_relo)
        mouse_ball.set_position(pygame.mouse.get_pos())

        if io.is_key_pressed(K_q):
            shape_registry.delete(kinematic_rect)
            


        dynamic_circle.set_angular_velocity(random.random() * 50 - 25)
        dynamic_circle.set_friction(random.random() * 0.2)


        screen.fill((0, 0, 0, 0))
        shape_registry.draw_shapes(screen)

        # Make Box2D simulate the physics of our world for one step.
        # Instruct the world to perform a single step of simulation. It is
        # generally best to keep the time step and iterations fixed.
        # See the manual (Section "Simulating the World") for further discussion
        # on these parameters and their implications.
        world.Step(TIME_STEP, 10, 10)

        for contact in world.contacts:
            contact: Box2D.b2Contact
            if not contact.touching:
                continue

            shape_a: Shape = contact.fixtureA.userData
            shape_b: Shape = contact.fixtureB.userData

            if  (shape_b is kinematic_line and shape_a is dynamic_rect) or \
                (shape_a is kinematic_line and shape_b is dynamic_rect):

                print("Collision between kinematic_line and dynamic_rect!")

        # Flip the screen and try to keep at the target FPS
        pygame.display.flip()
        clock.tick(TARGET_FPS)

    pygame.quit()
    print('Done!')


if __name__ == "__main__":
    main()
