from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Set
from enum import Enum, auto

import Box2D
import pygame

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


class Shape(ABC):
    @abstractmethod
    def draw(self, screen: pygame.Surface):
        pass

    def b2_get_body(self) -> Box2D.b2Body:
        return self.body
    
    def b2_get_shape(self) -> Box2D.b2Shape:
        return self.shape
    
    def b2_get_fixture(self) -> Optional[Box2D.b2Fixture]:
        """Only returns a fixture for Dynamic Bodies"""
        return self.fixture

    def get_position(self) -> Tuple[float, float]:
        return flip_y_position(box2d_to_pixels_v(self.b2_get_body().position))

    def set_position(self, position: Tuple[float, float]) -> Shape:
        self.b2_get_body().position = pixels_to_box2d_v(flip_y_position(position))
        return self

    def get_velocity(self) -> Tuple[float, float]:
        return box2d_to_pixels_v(flip_y_velocity(self.b2_get_body().linearVelocity))

    def set_velocity(self, velocity: Tuple[float, float]) -> Shape:
        """Pixels per second. This is what you should use to move a Kinematic
        Shape"""
        self.b2_get_body().linearVelocity = pixels_to_box2d_v(flip_y_velocity(velocity))
        return self

    def get_angular_velocity(self) -> float:
        return self.b2_get_body().angularVelocity

    def set_angular_velocity(self, angular_velocity: float) -> Shape:
        self.b2_get_body().angularVelocity = angular_velocity
        return self

    def get_density(self) -> float:
        return self.b2_get_fixture().density

    def set_density(self, density: float) -> Shape:
        self.b2_get_fixture().density = density
        return self
    
    def get_friction(self) -> float:
        return self.b2_get_fixture().friction

    def set_friction(self, friction: float) -> Shape:
        self.b2_get_fixture().friction = friction
        return self
    
    def get_restitution(self) -> float:
        return self.b2_get_fixture().restitution

    def set_restitution(self, restitution: float) -> Shape:
        self.b2_get_fixture().restitution = restitution


class ShapeRegister:
    def __init__(self, world: Box2D.b2World):
        self.world = world
        self.shapes: Set[Shape] = set()

    def add(self, shapes: List[Shape] | Shape):
        if not isinstance(shapes, list):
            shapes = [shapes]

        for shape in shapes:
            self.shapes.add(shape)

    def delete(self, shape: Shape):
        if shape in self.shapes:
            self.shapes.remove(shape)
            self.world.DestroyBody(shape.b2_get_body())
    
    def draw_shapes(self, screen: pygame.Surface):
        for shape in self.shapes:
            shape.draw(screen)


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


class CollisionType(Enum):
    Static = auto()
    Kinematic = auto()
    Dynamic = auto()


class __Circle(Shape):
    def __init__(
            self,
            world: Box2D.b2World,
            position: Tuple[float, float],
            radius: float,
            collision_type: CollisionType,
            collision_info: CollisionInfo,
            colour: Tuple[int, int, int, int]=(255, 255, 255, 255),
        ):
        position = pixels_to_box2d_v(flip_y_position(position))
        radius = pixels_to_box2d(radius)

        self.colour = colour
        self.shape = Box2D.b2CircleShape(
            radius=radius
        )
        self.fixture: Box2D.b2Fixture = None
        if collision_type == CollisionType.Static:
            self.body: Box2D.b2Body = world.CreateStaticBody(
                position=position,
                shapes=self.shape,
            )
        elif collision_type == CollisionType.Kinematic:
            self.body: Box2D.b2Body = world.CreateKinematicBody(
                position=position,
                shapes=self.shape,
            )
        elif collision_type == CollisionType.Dynamic:
            self.body: Box2D.b2Body = world.CreateDynamicBody(
                position=position,
                shapes=self.shape,
            )
            assert collision_info is not None, "Must provide CollisionInfo for dynamic type"
            self.fixture = self.body.CreateCircleFixture(
                radius=radius,
                density=collision_info.density,
                friction=collision_info.friction,
                restitution=collision_info.restitution,
                userData=self
            )
        else:
            assert False, "Must use a valid collision type"
        
        self.body.fixtures[0].userData = self

    def draw(self, screen: pygame.Surface):
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
            flip_y_position(box2d_to_pixels_v(self.body.transform * self.shape.pos)),
            box2d_to_pixels(self.shape.radius)
        )


class StaticCircle(__Circle):
    def __init__(
            self,
            world: Box2D.b2World,
            position: Tuple[float, float],
            radius: float,
            colour: Tuple[int, int, int, int]=(255, 255, 255, 255),
        ):
        super().__init__(world, position, radius, CollisionType.Static, None, colour)


class KinematicCircle(__Circle):
    def __init__(
            self,
            world: Box2D.b2World,
            position: Tuple[float, float],
            radius: float,
            colour: Tuple[int, int, int, int]=(255, 255, 255, 255),
        ):
        super().__init__(world, position, radius, CollisionType.Kinematic, None, colour)


class DynamicCircle(__Circle):
    def __init__(
            self,
            world: Box2D.b2World,
            position: Tuple[float, float],
            radius: float,
            collision_info: CollisionInfo,
            colour: Tuple[int, int, int, int]=(255, 255, 255, 255),
        ):
        super().__init__(world, position, radius, CollisionType.Dynamic, collision_info, colour)


class __Rectangle(Shape):
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
        position = pixels_to_box2d_v(flip_y_position(position))

        # It also expects the size to be the "radius" of the box. So we need to
        # halve it to get the size we expect.
        size = (size[0] / 2, size[1] / 2)
        size = pixels_to_box2d_v(size)

        # The fixture holds information like density and friction,
        # and also the shape.
        self.colour = colour
        self.shape = Box2D.b2PolygonShape(
            box=size,
        )
        self.fixture: Box2D.b2Fixture = None
        if collision_type == CollisionType.Static:
            self.body: Box2D.b2Body = world.CreateStaticBody(
                position=position,
                shapes=self.shape,
            )
        elif collision_type == CollisionType.Kinematic:
            self.body: Box2D.b2Body = world.CreateKinematicBody(
                position=position,
                shapes=self.shape,
            )
        elif collision_type == CollisionType.Dynamic:
            self.body: Box2D.b2Body = world.CreateDynamicBody(
                position=position,
                shapes=self.shape,
            )
            assert collision_info is not None, "Must provide CollisionInfo for dynamic type"
            self.fixture = self.body.CreatePolygonFixture(
                box=size,
                density=collision_info.density,
                friction=collision_info.friction,
                restitution=collision_info.restitution,
                userData=self
            )
        else:
            assert False, "Must use a valid collision type"
        
        self.body.fixtures[0].userData = self

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


class StaticRectangle(__Rectangle):
    def __init__(
            self,
            world: Box2D.b2World,
            position: Tuple[float, float],
            size: Tuple[float, float],
            colour: Tuple[int, int, int, int]=(255, 255, 255, 255),
    ):
        super().__init__(world, position, size, CollisionType.Static, None, colour)


class DynamicRectangle(__Rectangle):
    def __init__(
            self,
            world: Box2D.b2World,
            position: Tuple[float, float],
            size: Tuple[float, float],
            collision_info: CollisionInfo,
            colour: Tuple[int, int, int, int]=(255, 255, 255, 255),
    ):
        super().__init__(world, position, size, CollisionType.Dynamic, collision_info, colour)


class KinematicRectangle(__Rectangle):
    def __init__(
            self,
            world: Box2D.b2World,
            position: Tuple[float, float],
            size: Tuple[float, float],
            colour: Tuple[int, int, int, int]=(255, 255, 255, 255),
    ):
        super().__init__(world, position, size, CollisionType.Kinematic, None, colour)


class __Line(Shape):
    def __init__(
            self,
            world: Box2D.b2World,
            point_a: Tuple[float, float],
            point_b: Tuple[float, float],
            collision_type: CollisionType,
            collision_info: CollisionInfo,
            colour: Tuple[int, int, int, int]=(255, 255, 255, 255),
    ):
        point_a = pixels_to_box2d_v(flip_y_position(point_a))
        point_b = pixels_to_box2d_v(flip_y_position(point_b))
        point_a2 = pixels_to_box2d_v(flip_y_position((point_a[0], point_a[1] + 1)))
        point_b2 = pixels_to_box2d_v(flip_y_position((point_b[0], point_b[1] + 1)))
        
        self.colour = colour
        self.shape = Box2D.b2EdgeShape(
            vertices=[point_a, point_b],
        )
        self.fixture: Box2D.b2Fixture = None
        if collision_type == CollisionType.Static:
            self.body: Box2D.b2Body = world.CreateStaticBody(
                shapes=self.shape
            )
        elif collision_type == CollisionType.Kinematic:
            self.body: Box2D.b2Body = world.CreateKinematicBody(
                shapes=self.shape
            )
        elif collision_type == CollisionType.Dynamic:
            self.body: Box2D.b2Body = world.CreateDynamicBody(
                shapes=self.shape
            )
            assert collision_info is not None, "Must provide CollisionInfo for dynamic type"
            self.fixture = self.body.CreatePolygonFixture(
                vertices=[point_a, point_a2, point_b, point_b2],
                density=collision_info.density,
                friction=collision_info.friction,
                restitution=collision_info.restitution,
                userData=self
            )
        else:
            assert False, "Must use a valid collision type"
        
        self.body.fixtures[0].userData = self


    def draw(self, screen: pygame.Surface, width: int = 1):
        vertices = [box2d_to_pixels_v(self.body.transform * v) for v in self.shape.vertices]

        # But wait! It's upside-down! Pygame and Box2D orient their
        # axes in different ways. Box2D is just like how you learned
        # in high school, with positive x and y directions going
        # right and up. Pygame, on the other hand, increases in the
        # right and downward directions. This means we must flip
        # the y components.
        vertices = [flip_y_position(v) for v in vertices]
        pygame.draw.line(screen, self.colour, vertices[0], vertices[1], width)
    

class StaticLine(__Line):
    def __init__(
        self,
        world: Box2D.b2World,
        point_a: Tuple[float, float],
        point_b: Tuple[float, float],
        colour: Tuple[int, int, int, int]=(255, 255, 255, 255),
    ):
        super().__init__(world, point_a, point_b, CollisionType.Static, None, colour)


class KinematicLine(__Line):
    def __init__(
        self,
        world: Box2D.b2World,
        point_a: Tuple[float, float],
        point_b: Tuple[float, float],
        colour: Tuple[int, int, int, int]=(255, 255, 255, 255),
    ):
        super().__init__(world, point_a, point_b, CollisionType.Kinematic, None, colour)


class DynamicLine(__Line):
    def __init__(
        self,
        world: Box2D.b2World,
        point_a: Tuple[float, float],
        point_b: Tuple[float, float],
        collision_info: CollisionInfo,
        colour: Tuple[int, int, int, int]=(255, 255, 255, 255),
    ):
        super().__init__(world, point_a, point_b, CollisionType.Dynamic, collision_info, colour)
