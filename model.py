import Box2D
import pygame
from typing import Tuple
from enum import Enum, auto

# Box2D deals with meters, but we want to display pixels,
# so define a conversion factor:
PPM = 20.0  # pixels per meter
SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480


def pixels_to_box2d(p: float) -> float:
    return p / PPM

def pixels_to_box2d_v(v: Tuple[float, float]) -> Tuple[float, float]:
    return (
        v[0] / PPM,
        v[1] / PPM,
    )

def flip_y_position(v: Tuple[float, float]):
    return (v[0], SCREEN_HEIGHT - v[1])

def flip_y_velocity(v: Tuple[float, float]):
    return (v[0], -v[1])

def box2d_to_pixels_v(v: Tuple[float, float]):
    return (
        v[0] * PPM,
        v[1] * PPM,
    )

def box2d_to_pixels(p: float):
    return p * PPM


class DynamicCircle:
    def __init__(
            self,
            world: Box2D.b2World,
            position: Tuple[float, float],
            radius: float,
            velocity: Tuple[float, float]=(0, 0),
            colour: Tuple[int, int, int, int]=(255, 255, 255, 255),
            density=1,
            friction=0,
            restitution=1,
        ):
        self.world = world
        self.body: Box2D.b2BodyDef = world.CreateDynamicBody(
            position=pixels_to_box2d_v(flip_y_position(position)),
            linearVelocity=pixels_to_box2d_v(flip_y_velocity(velocity)),
            linearDamping=0,
        )
        # And add a box fixture onto it (with a nonzero density, so it will move)
        self.fixture: Box2D.b2Fixture = self.body.CreateCircleFixture(
            radius=pixels_to_box2d(radius),
            density=density,
            friction=friction,
            restitution=restitution,
        )
        self.colour = colour
    
    def draw(self, screen: pygame.Surface):
        shape = self.fixture.shape
        # We take the body's transform and multiply it with each
        # vertex, and then convert from meters to pixels with the scale
        # factor.

        # But wait! It's upside-down! Pygame and Box2D orient their
        # axes in different ways. Box2D is just like how you learned
        # in high school, with positive x and y directions going
        # right and up. Pygame, on the other hand, increases in the
        # right and downward directions. This means we must flip
        # the y components.
        pygame.draw.circle(
            screen,
            self.colour,
            flip_y_position(box2d_to_pixels_v(self.body.transform * shape.pos)),
            box2d_to_pixels(shape.radius)
        )


class StaticBox:
    def __init__(self,
            world: Box2D.b2World,
            position: Tuple[float, float],
            size: Tuple[float, float],
            colour: Tuple[int, int, int, int]=(255, 255, 255, 255),
        ):
        # Box2D expects the position to be the centre point of the box, but I
        # find this calculation harder to understand. Thus, I move the position
        # to be the top left point (towards the pygame origin).
        position = (position[0] + size[0] / 2, position[1] + size[1] / 2)

        # It also expects the size to be the "radius" of the box. So we need to
        # halve it to get the size we expect.
        size = (size[0] / 2, size[1] / 2)

        # The fixture holds information like density and friction,
        # and also the shape.
        self.shape = Box2D.b2PolygonShape(
            box=pixels_to_box2d_v(size),
        )
        self.body: Box2D.b2Body = world.CreateStaticBody(
            position=pixels_to_box2d_v(flip_y_position(position)),
            shapes=self.shape,
        )
        self.colour = colour

    def draw(self, screen: pygame.Surface):
        # We take the body's transform and multiply it with each
        # vertex, and then convert from meters to pixels with the scale
        # factor.
        vertices = [box2d_to_pixels_v(self.body.transform * v) for v in self.shape.vertices]

        # But wait! It's upside-down! Pygame and Box2D orient their
        # axes in different ways. Box2D is just like how you learned
        # in high school, with positive x and y directions going
        # right and up. Pygame, on the other hand, increases in the
        # right and downward directions. This means we must flip
        # the y components.
        vertices = [flip_y_position(v) for v in vertices]

        pygame.draw.polygon(screen, self.colour, vertices)

    def set_position(self, pos: Tuple[float, float]):
        self.body.position = pixels_to_box2d_v(flip_y_position(pos))

    def get_position(self) -> Tuple[float, float]:
        return flip_y_position(box2d_to_pixels_v(self.body.position))


class CollisionType(Enum):
    Static = auto()
    Kinematic = auto()
    Dynamic = auto()


class CollisionInfo:
    def __init__(
            self,
            density=1,
            friction=0,
            restitution=1,
    ):
        self.density = density
        self.friction = friction
        self.restitution = restitution


class Rectangle:
    def __init__(self,
            world: Box2D.b2World,
            position: Tuple[float, float],
            size: Tuple[float, float],
            collision_type: CollisionType,
            collision_info: CollisionInfo,
            colour: Tuple[int, int, int, int]=(255, 255, 255, 255),
        ):
        # Box2D expects the position to be the centre point of the box, but I
        # find this calculation harder to understand. Thus, I move the position
        # to be the top left point (towards the pygame origin).
        position = (position[0] + size[0] / 2, position[1] + size[1] / 2)

        # It also expects the size to be the "radius" of the box. So we need to
        # halve it to get the size we expect.
        size = (size[0] / 2, size[1] / 2)

        # The fixture holds information like density and friction,
        # and also the shape.
        self.shape = Box2D.b2PolygonShape(
            box=pixels_to_box2d_v(size),
        )
        self.fixture: Box2D.b2Fixture = None
        if collision_type == CollisionType.Static:
            self.body: Box2D.b2Body = world.CreateStaticBody(
                position=pixels_to_box2d_v(flip_y_position(position)),
                shapes=self.shape,
            )
        elif collision_type == CollisionType.Kinematic:
            self.body: Box2D.b2Body = world.CreateKinematicBody(
                position=pixels_to_box2d_v(flip_y_position(position)),
                shapes=self.shape,
            )
        elif collision_type == CollisionType.Dynamic:
            self.body: Box2D.b2Body = world.CreateDynamicBody(
                position=pixels_to_box2d_v(flip_y_position(position)),
                shapes=self.shape,
            )
            assert collision_info is not None, "Must provide CollisionInfo for dynamic type"
            self.fixture = self.body.CreatePolygonFixture(
                box=pixels_to_box2d_v(size),
                density=collision_info.density,
                friction=collision_info.friction,
                restitution=collision_info.restitution,
            )
        else:
            assert False, "Must use a valid collision type"

        self.colour = colour

    def draw(self, screen: pygame.Surface):
        # We take the body's transform and multiply it with each
        # vertex, and then convert from meters to pixels with the scale
        # factor.
        vertices = [box2d_to_pixels_v(self.body.transform * v) for v in self.shape.vertices]

        # But wait! It's upside-down! Pygame and Box2D orient their
        # axes in different ways. Box2D is just like how you learned
        # in high school, with positive x and y directions going
        # right and up. Pygame, on the other hand, increases in the
        # right and downward directions. This means we must flip
        # the y components.
        vertices = [flip_y_position(v) for v in vertices]

        pygame.draw.polygon(screen, self.colour, vertices)

    def set_velocity(self, v: Tuple[float, float]):
        """Pixels per second"""
        self.body.linearVelocity = pixels_to_box2d_v(flip_y_velocity(v))

    def set_position(self, pos: Tuple[float, float]):
        self.body.position = pixels_to_box2d_v(flip_y_position(pos))

    def get_position(self) -> Tuple[float, float]:
        return flip_y_position(box2d_to_pixels_v(self.body.position))


class StaticLine:
    def __init__(
            self,
            world: Box2D.b2World,
            point_a: Tuple[float, float],
            point_b: Tuple[float, float],
            colour: Tuple[int, int, int, int]=(255, 255, 255, 255),
        ):
        self.body = world.CreateStaticBody(
            shapes=Box2D.b2EdgeShape(
                vertices=[
                    pixels_to_box2d_v(flip_y_position(point_a)),
                    pixels_to_box2d_v(flip_y_position(point_b)),
                ],
            ),
        )
        self.point_a = point_a
        self.point_b = point_b
        self.colour = colour
    
    def draw(self, screen: pygame.Surface):
        pygame.draw.line(screen, self.colour, self.point_a, self.point_b)


class KeyQuery:
    def __init__(self):
        self.keys_down = set()
        self.keys_pressed = set()
        self.keys_released = set()
    
    def is_key_down(self, key: int):
        return key in self.keys_down
    
    def is_key_pressed(self, key: int):
        return key in self.keys_pressed
    
    def is_key_released(self, key: int):
        return key in self.keys_released

    def mark_pressed(self, key: int):
        self.keys_down.add(key)
        self.keys_pressed.add(key)

    def mark_released(self, key: int):
        self.keys_down.remove(key)
        self.keys_released.add(key)

    def clear(self):
        self.keys_pressed.clear()
        self.keys_released.clear()
