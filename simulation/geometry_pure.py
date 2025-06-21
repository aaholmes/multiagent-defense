"""
Pure Python implementation of geometric functions for testing visualization
before the Rust library is compiled with Python bindings.
"""
import math
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class Point:
    x: float
    y: float
    
    def distance_to(self, other: 'Point') -> float:
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
    
    def angle_to(self, other: 'Point') -> float:
        return math.atan2(other.y - self.y, other.x - self.x)


@dataclass 
class Circle:
    center: Point
    radius: float
    
    def intersects(self, other: 'Circle') -> bool:
        distance = self.center.distance_to(other.center)
        return distance <= (self.radius + other.radius)


def calculate_apollonian_circle(
    defender_pos: Point,
    intruder_pos: Point, 
    speed_ratio: float  # k = defender_speed / intruder_speed
) -> Circle:
    """
    Calculate the Apollonian circle for a defender and intruder.
    
    The Apollonian circle is the locus of points P such that:
    distance(P, defender) / distance(P, intruder) = k (speed ratio)
    
    For k = 0.5 (defender half as fast), the circle passes through:
    - Point 1: 1/3 of the way from defender to intruder
    - Point 2: distance d behind the defender (opposite direction)
    """
    if speed_ratio == 1.0:
        # Special case: equal speeds result in a line (perpendicular bisector)
        midpoint = Point(
            (defender_pos.x + intruder_pos.x) / 2.0,
            (defender_pos.y + intruder_pos.y) / 2.0
        )
        return Circle(midpoint, float('inf'))

    k = speed_ratio
    
    # Vector from defender to intruder
    dx = intruder_pos.x - defender_pos.x
    dy = intruder_pos.y - defender_pos.y
    d = math.sqrt(dx*dx + dy*dy)
    
    # Unit vector from defender toward intruder
    ux = dx / d
    uy = dy / d
    
    if k < 1.0:
        # Defender is slower
        # For Apollonian circle with ratio k, the two intersection points on the line are:
        # Point 1: at distance d * k/(1+k) from defender toward intruder  
        # Point 2: at distance d * k/(1-k) from defender away from intruder
        
        # Distance from defender toward intruder
        d1 = d * k / (1.0 + k)  # For k=0.5: d*0.5/1.5 = d/3
        p1 = Point(
            defender_pos.x + d1 * ux,
            defender_pos.y + d1 * uy
        )
        
        # Distance from defender away from intruder  
        d2 = d * k / (1.0 - k)  # For k=0.5: d*0.5/0.5 = d
        p2 = Point(
            defender_pos.x - d2 * ux,
            defender_pos.y - d2 * uy
        )
        
        # Circle center is midpoint of p1 and p2
        center = Point((p1.x + p2.x) / 2.0, (p1.y + p2.y) / 2.0)
        radius = center.distance_to(p1)
        
    else:
        # Defender is faster - different geometry
        t1 = k / (k + 1.0)
        t2 = k / (k - 1.0)
        
        p1 = Point(defender_pos.x + t1 * dx, defender_pos.y + t1 * dy)
        p2 = Point(defender_pos.x + t2 * dx, defender_pos.y + t2 * dy)
        
        center = Point((p1.x + p2.x) / 2.0, (p1.y + p2.y) / 2.0)
        radius = center.distance_to(p1)

    return Circle(center, radius)


def calculate_arc_intersection_length(circle1: Circle, circle2: Circle) -> float:
    """Calculate the arc length of intersection between two circles"""
    if not circle1.intersects(circle2):
        return 0.0

    distance = circle1.center.distance_to(circle2.center)
    
    # If circle1 is completely inside circle2
    if distance + circle1.radius <= circle2.radius:
        return 2.0 * math.pi * circle1.radius  # Full circumference
    
    # If circle2 is completely inside circle1, no arc of circle1 is inside circle2
    if distance + circle2.radius <= circle1.radius:
        return 0.0

    # Calculate the central angle of the intersection arc using law of cosines
    cos_half_angle = (circle1.radius**2 + distance**2 - circle2.radius**2) / (2.0 * circle1.radius * distance)
    
    # Clamp to valid range for acos
    cos_half_angle = max(-1.0, min(1.0, cos_half_angle))
    half_angle = math.acos(cos_half_angle)
    full_angle = 2.0 * half_angle

    return circle1.radius * full_angle