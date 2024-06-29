import pygame
from pygame.locals import (QUIT, KEYDOWN, K_ESCAPE, K_a, K_d, KEYUP)
from typing import Tuple
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

# player_bar = StaticBox(
#     world,
#     position=(100, 350),
#     size=(200, 50),
#     colour=(100, 150, 255, 255)
# )

game_balls = [DynamicCircle(
    world,
    position=(150, 250),
    radius=30,
    velocity=(350, 450),
    colour=(100, 255, 150, 255),
    density=1,
    friction=0,
    restitution=0.9,
)]

dynamic_rect = Rectangle(
    world,
    (200, 250),
    (25, 45),
    CollisionType.Dynamic,
    CollisionInfo(restitution=0.9),
    (100, 100, 150, 255)
)

static_rect = Rectangle(
    world,
    (230, 250),
    (25, 45),
    CollisionType.Static,
    None,
    (100, 100, 150, 255)
)

kinematic_rect = Rectangle(
    world,
    (100, 350),
    (200, 50),
    CollisionType.Kinematic,
    None,
    (100, 100, 250, 255)
)

def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)
    pygame.display.set_caption("Simple pygame example")
    clock = pygame.time.Clock()
    
    key_query = KeyQuery()

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

        direction = int(key_query.is_key_down(K_d)) - int(key_query.is_key_down(K_a))
        # position = player_bar.get_position()
        # player_bar.set_position((position[0] + direction * 3, position[1]))

        kinematic_rect.set_velocity((direction * 400, 0))

        # player_bar.set_position((pygame.mouse.get_pos()[0], player_bar.get_position()[1]))
            

        screen.fill((0, 0, 0, 0))

        # player_bar.draw(screen)

        for ball in game_balls:
            ball.draw(screen)
            # Add random angular velocity and friction to encourage the ball to
            # bounce around
            ball.body.angularVelocity = random.random() * 50 - 25
            ball.fixture.friction = random.random() * 0.2


        for border in world_borders:
            border.draw(screen)
        
        dynamic_rect.draw(screen)
        static_rect.draw(screen)
        kinematic_rect.draw(screen)

        # Make Box2D simulate the physics of our world for one step.
        # Instruct the world to perform a single step of simulation. It is
        # generally best to keep the time step and iterations fixed.
        # See the manual (Section "Simulating the World") for further discussion
        # on these parameters and their implications.
        world.Step(TIME_STEP, 10, 10)

        # Flip the screen and try to keep at the target FPS
        pygame.display.flip()
        clock.tick(TARGET_FPS)

    pygame.quit()
    print('Done!')


if __name__ == "__main__":
    main()
