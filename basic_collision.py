#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
An attempt at some simple, self-contained pygame-based examples.

Example 01

In short:
One static body: a big polygon to represent the ground
One dynamic body: a rotated big polygon
And some drawing code to get you going.

kne
"""
import pygame
from pygame.locals import (QUIT, KEYDOWN, K_ESCAPE, K_a, K_d, KEYUP)
from typing import Tuple

# See https://raw.githubusercontent.com/pybox2d/pybox2d/master/library/Box2D/examples/simple/simple_01.py
import Box2D
from model import *

TARGET_FPS = 60
TIME_STEP = 1.0 / TARGET_FPS


# --- pybox2d world setup ---
# Create the world
world = Box2D.b2World(gravity=(0, -10), doSleep=True)

static_box = StaticBox(
    world,
    position=(100, 350),
    size=(200, 50),
    colour=(100, 150, 255, 255)
)

dynamic_body = DynamicCircle(
    world,
    position=(150, 250),
    radius=10,
    velocity=(32, 0),
    colour=(100, 255, 150, 255),
    density=1,
    friction=0,
    restitution=1,
)

static_line = __StaticLine(
    world,
    point_a=(10, 10),
    point_b=(SCREEN_WIDTH - 10, SCREEN_HEIGHT - 10),
    colour=(255, 150, 100, 255)
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
        position = static_box.get_position()
        static_box.set_position((position[0] + direction * 3, position[1]))
            

        screen.fill((0, 0, 0, 0))

        static_box.draw(screen)
        dynamic_body.draw(screen)
        static_line.draw(screen)

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
