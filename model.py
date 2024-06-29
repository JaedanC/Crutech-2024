from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Tuple, Set
from enum import Enum, auto, Flag

import Box2D
import pygame
from settings import *


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
        self.mouse_relative: Tuple[int, int] = None
    
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

    def clear_pressed(self):
        self.keys_pressed.clear()
        self.keys_released.clear()

    def mark_mouse_relative(self, rel: Tuple[int, int]):
        self.mouse_relative = rel

    def get_mouse_relative(self) -> Tuple[int, int]:
        return self.mouse_relative


class Shape(ABC):
    @abstractmethod
    def draw(self, screen: pygame.Surface):
        pass

    def b2_get_body(self) -> Box2D.b2Body:
        return self.body
    
    def b2_get_shape(self) -> Box2D.b2Shape:
        return self.shape
    
    def b2_get_fixture(self) -> Box2D.b2Fixture:
        if len(self.b2_get_body().fixtures) > 1:
            print(self.b2_get_body().fixtures)
        assert len(self.b2_get_body().fixtures) == 1

        return self.b2_get_body().fixtures[0]

    def set_collision_group(self, my_group: Flag, can_collide_with_groups: Flag):
        self.b2_get_fixture().filterData = Box2D.b2Filter(
        categoryBits=my_group.value,
        maskBits=can_collide_with_groups.value
    )

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


class ShapeRegistry:
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
                fixtures=Box2D.b2FixtureDef(
                    shape=self.shape,
                    density=collision_info.density,
                    friction=collision_info.friction,
                    restitution=collision_info.restitution,
                )
            )
        else:
            assert False, "Must use a valid collision type"
        
        self.b2_get_fixture().userData = self

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
                fixtures=Box2D.b2FixtureDef(
                    shape=self.shape,
                    density=collision_info.density,
                    friction=collision_info.friction,
                    restitution=collision_info.restitution,
                )
            )
        else:
            assert False, "Must use a valid collision type"
        
        self.b2_get_fixture().userData = self

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
        self.is_secretly_polygon = False
        self.point_a = pixels_to_box2d_v(flip_y_position(point_a))
        self.point_b = pixels_to_box2d_v(flip_y_position(point_b))
        self.point_a2 = pixels_to_box2d_v(flip_y_position((point_a[0], point_a[1] + 1)))
        self.point_b2 = pixels_to_box2d_v(flip_y_position((point_b[0], point_b[1] + 1)))

        
        self.colour = colour
        self.shape = Box2D.b2EdgeShape(
            vertices=[self.point_a, self.point_b],
        )
        if collision_type == CollisionType.Static:
            self.body: Box2D.b2Body = world.CreateStaticBody(
                shapes=self.shape
            )
        elif collision_type == CollisionType.Kinematic:
            self.body: Box2D.b2Body = world.CreateKinematicBody(
                shapes=self.shape
            )
        elif collision_type == CollisionType.Dynamic:
            assert collision_info is not None, "Must provide CollisionInfo for dynamic type"
            # We cheat with DynamicLine. It's actually a very small polygon.
            self.is_secretly_polygon = True
            self.polygon_shape = Box2D.b2PolygonShape(
                vertices=[self.point_a, self.point_a2, self.point_b, self.point_b2]
            )
            self.body: Box2D.b2Body = world.CreateDynamicBody(
                fixtures=Box2D.b2FixtureDef(
                    shape=self.polygon_shape,
                    density=collision_info.density,
                    friction=collision_info.friction,
                    restitution=collision_info.restitution,
                )
            )
            print(self.point_a)
            print(self.point_b)
            print(self.point_a2)
            print(self.point_b2)
        else:
            assert False, "Must use a valid collision type"
        
        self.b2_get_fixture().userData = self

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

        if self.is_secretly_polygon and False:
            # We take the body's transform and multiply it with each
            # vertex, and then convert from meters to pixels with the scale
            # factor.
            vertices = [box2d_to_pixels_v(self.body.transform * v) for v in self.polygon_shape.vertices]

            # But wait! It's upside-down! Pygame and Box2D orient their
            # axes in different ways. Box2D is just like how you learned
            # in high school, with positive x and y directions going
            # right and up. Pygame, on the other hand, increases in the
            # right and downward directions. This means we must flip
            # the y components.
            vertices = [flip_y_position(v) for v in vertices]

            pygame.draw.polygon(screen, (255, 255, 255, 100), vertices)
        

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
