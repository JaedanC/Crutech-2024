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

game_objects = []


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


        screen.fill((0, 0, 0, 0))
        shape_registry.draw_shapes(screen)

        # Flip the screen and try to keep at the target FPS
        pygame.display.flip()
        clock.tick(TARGET_FPS)

    pygame.quit()
    print('Done!')


if __name__ == "__main__":
    main()
