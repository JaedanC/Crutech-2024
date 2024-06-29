import pygame
from pygame.locals import (QUIT, KEYDOWN, K_ESCAPE, K_a, K_d, K_w, K_s, KEYUP, K_q)
pygame.color.Color
import random

# See https://raw.githubusercontent.com/pybox2d/pybox2d/master/library/Box2D/examples/simple/simple_01.py
import Box2D
from model import *

TARGET_FPS = 60
TIME_STEP = 1.0 / TARGET_FPS

# --- pybox2d world setup ---
# Create the world
world = Box2D.b2World(gravity=(0, 0), doSleep=True)


world_borders = [
    StaticLine(world, (5,                5                ), (SCREEN_WIDTH - 5, 5                ), colour=(255, 150, 100, 255)),
    StaticLine(world, (SCREEN_WIDTH - 5, 5                ), (SCREEN_WIDTH - 5, SCREEN_HEIGHT - 5), colour=(255, 150, 100, 255)),
    StaticLine(world, (SCREEN_WIDTH - 5, SCREEN_HEIGHT - 5), (5,                SCREEN_HEIGHT - 5), colour=(255, 150, 100, 255)),
    StaticLine(world, (5,                SCREEN_HEIGHT - 5), (5,                5                ), colour=(255, 150, 100, 255)),
]

game_balls = [
    DynamicCircle(
        world,
        (150, 250),
        30,
        CollisionInfo(restitution=1.1),
        colour=(100, 255, 150, 255),
    ).set_velocity((350, -450)),
    StaticCircle(
        world,
        (320, 275),
        25,
        colour=(50, 255, 150, 255),
    ).set_velocity((35, -45)),
    KinematicCircle(
        world,
        (370, 275),
        25,
        colour=(50, 200, 250, 255),
    ).set_velocity((-35, 45))
]

dynamic_rect = DynamicRectangle(
    world,
    (200, 250),
    (25, 45),
    CollisionInfo(restitution=0.9),
    (100, 100, 150, 255)
)

static_rect = StaticRectangle(
    world,
    (230, 250),
    (25, 45),
    (100, 100, 150, 255)
)

kinematic_rect = KinematicRectangle(
    world,
    (100, 350),
    (200, 50),
    (100, 100, 250, 255)
)

kinematic_line = KinematicLine(
    world,
    (30, 20),
    (130, 100),
    (255, 90, 255, 255),
)

game_objects = game_balls + world_borders + [
    dynamic_rect,
    static_rect,
    kinematic_rect,
    DynamicLine(
        world,
        (10, 10),
        (100, 100),
        CollisionInfo(restitution=0.9),
        (255, 255, 90, 255),
    ),
    kinematic_line
]


def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)
    pygame.display.set_caption("Simple pygame example")
    clock = pygame.time.Clock()
    
    key_query = KeyQuery()
    shape_register = ShapeRegister(world)
    shape_register.add(game_objects)
    
    running = True
    while running:
        key_query.clear()
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                running = False
                break

            if event.type == KEYDOWN:
                key_query.mark_pressed(event.key)
            elif event.type == KEYUP:
                key_query.mark_released(event.key)

        left_right = int(key_query.is_key_down(K_d)) - int(key_query.is_key_down(K_a))
        up_down    = int(key_query.is_key_down(K_s)) - int(key_query.is_key_down(K_w))

        kinematic_rect.set_velocity((left_right * 400, up_down * 400))
        kinematic_line.set_velocity((left_right * 400, up_down * 400))
        game_balls[2].set_velocity((left_right * 400,  up_down * 400))

        if key_query.is_key_pressed(K_q):
            shape_register.delete(kinematic_rect)
            


        screen.fill((0, 0, 0, 0))

        for ball in game_balls[:1]:
            # Add random angular velocity and friction to encourage the ball to
            # bounce around
            ball: DynamicCircle
            ball.set_angular_velocity(random.random() * 50 - 25)
            ball.set_friction(random.random() * 0.2)

        shape_register.draw_shapes(screen)

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
