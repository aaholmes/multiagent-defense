#!/usr/bin/env python3
"""
Test script to verify geometric calculations and visualization.
Run this to see the basic scenario with Apollonian circles.
"""

import sys
import os
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

# Add simulation directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'simulation'))

from geometry_pure import Point, Circle, calculate_apollonian_circle
from visualizer import SimulationVisualizer


def test_apollonian_calculations():
    """Test and visualize different Apollonian circle scenarios"""
    
    print("Testing Apollonian Circle Calculations...")
    
    # Test case 1: Basic scenario from our Rust tests
    defender = Point(0.0, 0.0)
    intruder = Point(4.0, 0.0)
    speed_ratio = 0.5
    
    circle = calculate_apollonian_circle(defender, intruder, speed_ratio)
    print(f"Test 1 - Speed ratio {speed_ratio}:")
    print(f"  Center: ({circle.center.x:.3f}, {circle.center.y:.3f})")
    print(f"  Radius: {circle.radius:.3f}")
    
    # Verify the circle passes through the correct points for k=0.5
    # Point 1: 1/3 of the way from defender to intruder (head-on interception)
    # Point 2: distance d behind the defender (where d = distance between defender and intruder)
    
    d = defender.distance_to(intruder)  # Should be 4.0
    print(f"  Distance between defender and intruder: {d:.3f}")
    
    # Point 1: 1/3 of the way from defender to intruder
    p1 = Point(
        defender.x + (1/3) * (intruder.x - defender.x),
        defender.y + (1/3) * (intruder.y - defender.y)
    )
    
    # Point 2: distance d behind the defender (opposite direction from intruder)
    direction_x = (intruder.x - defender.x) / d  # Unit vector toward intruder
    direction_y = (intruder.y - defender.y) / d
    p2 = Point(
        defender.x - d * direction_x,  # d units behind defender
        defender.y - d * direction_y
    )
    
    dist1 = circle.center.distance_to(p1)
    dist2 = circle.center.distance_to(p2)
    print(f"  Point 1 (1/3 toward intruder): ({p1.x:.3f}, {p1.y:.3f}), distance to center: {dist1:.3f}")
    print(f"  Point 2 (d behind defender): ({p2.x:.3f}, {p2.y:.3f}), distance to center: {dist2:.3f}")
    print(f"  Both distances should equal radius: {circle.radius:.3f}")
    print(f"  Test passes: {abs(dist1 - circle.radius) < 0.001 and abs(dist2 - circle.radius) < 0.001}")
    
    # Test case 2: Defender faster than intruder
    speed_ratio_fast = 1.5
    circle_fast = calculate_apollonian_circle(defender, intruder, speed_ratio_fast)
    print(f"\nTest 2 - Speed ratio {speed_ratio_fast}:")
    print(f"  Center: ({circle_fast.center.x:.3f}, {circle_fast.center.y:.3f})")
    print(f"  Radius: {circle_fast.radius:.3f}")
    
    return True


def create_multi_scenario_visualization():
    """Create visualization showing multiple scenarios"""
    
    # Protected zone
    protected_center = Point(0, 0)
    protected_radius = 1.5
    
    # Common intruder position
    intruder_pos = Point(16, 0)
    
    # Different defender positions and speed ratios (all defenders slower than intruder)
    scenarios = [
        {"pos": Point(4, 2), "speed": 0.2, "label": "Slow Defender (k=0.2)"},
        {"pos": Point(3, -3), "speed": 0.4, "label": "Medium Defender (k=0.4)"},  
        {"pos": Point(2, 4), "speed": 0.6, "label": "Fast Defender (k=0.6)"},
    ]
    
    viz = SimulationVisualizer(figsize=(12, 10))
    
    # Plot protected zone
    viz.plot_protected_zone(protected_center, protected_radius)
    
    # Plot intruder
    viz.plot_intruder(intruder_pos)
    
    # Plot each defender and their Apollonian circle
    colors = ['blue', 'purple', 'orange']
    for i, scenario in enumerate(scenarios):
        # Plot defender
        viz.plot_point(
            scenario["pos"], 
            color=colors[i], 
            size=120, 
            marker='s', 
            label=scenario["label"]
        )
        
        # Calculate and plot Apollonian circle
        apollonian = calculate_apollonian_circle(
            scenario["pos"], 
            intruder_pos, 
            scenario["speed"]
        )
        
        if apollonian.radius != float('inf'):
            viz.plot_circle(
                apollonian,
                color=colors[i],
                alpha=0.2,
                linestyle='--',
                linewidth=2,
                fill=True
            )
    
    viz.set_bounds(-5, 25, -12, 12)
    viz.set_title("Multi-Agent Defense: Apollonian Circles for Different Speed Ratios")
    viz.add_legend()
    
    return viz


if __name__ == "__main__":
    # Run tests
    test_apollonian_calculations()
    
    print("\nCreating visualization...")
    
    # Create and save visualization
    viz = create_multi_scenario_visualization()
    viz.save("apollonian_circles_test.png")
    
    print("Visualization saved to apollonian_circles_test.png")
