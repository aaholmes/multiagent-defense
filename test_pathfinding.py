#!/usr/bin/env python3
"""
Test script for the new smart intruder A* pathfinding functionality.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'simulation'))

import interception_core as ic
from smart_intruder import SmartIntruder
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
import numpy as np


def test_pathfinding_basic():
    """Test basic pathfinding functionality."""
    print("Testing basic A* pathfinding...")
    
    # Create grid configuration
    grid_config = ic.GridConfig(
        width=50,
        height=50,
        world_bounds=(-10.0, 10.0, -10.0, 10.0),
        base_cost=1.0,
        threat_penalty=1000.0
    )
    
    # Create simulation configuration
    sim_config = ic.SimConfig(
        learning_rate=0.1,
        defender_speed=1.0,
        intruder_speed=2.0,
        w_repel=1.0,
        epsilon=0.1
    )
    
    # Create test scenario
    defender = ic.AgentState(
        position=ic.Point(0.0, 0.0),
        velocity=ic.Point(0.0, 0.0)
    )
    
    intruder = ic.AgentState(
        position=ic.Point(8.0, 0.0),
        velocity=ic.Point(0.0, 0.0)
    )
    
    protected_zone = ic.Circle(
        center=ic.Point(-8.0, 0.0),
        radius=1.0
    )
    
    world_state = ic.WorldState(
        defenders=[defender],
        intruder=intruder,
        protected_zone=protected_zone
    )
    
    # Create smart intruder
    smart_intruder = SmartIntruder(
        initial_position=ic.Point(8.0, 0.0),
        max_speed=2.0,
        grid_config=grid_config
    )
    
    # Test pathfinding
    smart_intruder.update(world_state, sim_config)
    path_result = smart_intruder.get_current_path(world_state, sim_config)
    
    print(f"Path found: {path_result.found}")
    print(f"Path length: {len(path_result.path)}")
    print(f"Total cost: {path_result.total_cost}")
    print(f"Smart intruder velocity: ({smart_intruder.velocity.x:.2f}, {smart_intruder.velocity.y:.2f})")
    
    return path_result.found


def test_threat_map_generation():
    """Test threat map generation."""
    print("\nTesting threat map generation...")
    
    # Create grid configuration
    grid_config = ic.GridConfig(
        width=20,
        height=20,
        world_bounds=(-5.0, 5.0, -5.0, 5.0),
        base_cost=1.0,
        threat_penalty=100.0
    )
    
    sim_config = ic.SimConfig(
        learning_rate=0.1,
        defender_speed=1.0,
        intruder_speed=2.0,
        w_repel=1.0,
        epsilon=0.1
    )
    
    # Create test scenario with defender in center
    defender = ic.AgentState(
        position=ic.Point(0.0, 0.0),
        velocity=ic.Point(0.0, 0.0)
    )
    
    intruder = ic.AgentState(
        position=ic.Point(3.0, 0.0),
        velocity=ic.Point(0.0, 0.0)
    )
    
    protected_zone = ic.Circle(
        center=ic.Point(-3.0, 0.0),
        radius=0.5
    )
    
    world_state = ic.WorldState(
        defenders=[defender],
        intruder=intruder,
        protected_zone=protected_zone
    )
    
    # Create smart intruder and get threat map
    smart_intruder = SmartIntruder(
        initial_position=ic.Point(3.0, 0.0),
        max_speed=2.0,
        grid_config=grid_config
    )
    
    threat_map = smart_intruder.get_threat_map(world_state, sim_config)
    
    print(f"Threat map dimensions: {len(threat_map)} x {len(threat_map[0])}")
    
    # Check for threat and base costs
    has_threat_areas = False
    has_base_areas = False
    
    for row in threat_map:
        for cost in row:
            if cost > grid_config.base_cost + 50.0:
                has_threat_areas = True
            if abs(cost - grid_config.base_cost) < 0.1:
                has_base_areas = True
    
    print(f"Has threat areas: {has_threat_areas}")
    print(f"Has base cost areas: {has_base_areas}")
    
    return has_threat_areas and has_base_areas


def visualize_pathfinding():
    """Create a visualization of the pathfinding in action."""
    print("\nCreating pathfinding visualization...")
    
    # Create grid configuration
    grid_config = ic.GridConfig(
        width=30,
        height=30,
        world_bounds=(-6.0, 6.0, -6.0, 6.0),
        base_cost=1.0,
        threat_penalty=500.0
    )
    
    sim_config = ic.SimConfig(
        learning_rate=0.1,
        defender_speed=1.0,
        intruder_speed=2.0,
        w_repel=1.0,
        epsilon=0.1
    )
    
    # Create test scenario with multiple defenders
    defenders = [
        ic.AgentState(position=ic.Point(-1.0, 0.0), velocity=ic.Point(0.0, 0.0)),
        ic.AgentState(position=ic.Point(1.0, 2.0), velocity=ic.Point(0.0, 0.0)),
        ic.AgentState(position=ic.Point(1.0, -2.0), velocity=ic.Point(0.0, 0.0))
    ]
    
    intruder = ic.AgentState(
        position=ic.Point(5.0, 0.0),
        velocity=ic.Point(0.0, 0.0)
    )
    
    protected_zone = ic.Circle(
        center=ic.Point(-5.0, 0.0),
        radius=1.0
    )
    
    world_state = ic.WorldState(
        defenders=defenders,
        intruder=intruder,
        protected_zone=protected_zone
    )
    
    # Create smart intruder
    smart_intruder = SmartIntruder(
        initial_position=ic.Point(5.0, 0.0),
        max_speed=2.0,
        grid_config=grid_config
    )
    
    # Get threat map and path
    threat_map = smart_intruder.get_threat_map(world_state, sim_config)
    smart_intruder.update(world_state, sim_config)
    path_result = smart_intruder.get_current_path(world_state, sim_config)
    
    # Create visualization
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Plot 1: Threat map
    threat_array = np.array(threat_map)
    im1 = ax1.imshow(threat_array, origin='lower', extent=[-6, 6, -6, 6], cmap='Reds', alpha=0.7)
    ax1.set_title('Threat Map')
    ax1.set_xlabel('X')
    ax1.set_ylabel('Y')
    plt.colorbar(im1, ax=ax1)
    
    # Add defenders
    for i, defender in enumerate(defenders):
        ax1.plot(defender.position.x, defender.position.y, 'bs', markersize=10, label=f'Defender {i+1}')
    
    # Add intruder
    ax1.plot(intruder.position.x, intruder.position.y, 'ro', markersize=10, label='Intruder')
    
    # Add protected zone
    circle = plt.Circle((protected_zone.center.x, protected_zone.center.y), 
                       protected_zone.radius, color='green', alpha=0.3, label='Protected Zone')
    ax1.add_patch(circle)
    
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Path planning
    ax2.set_xlim(-6, 6)
    ax2.set_ylim(-6, 6)
    ax2.set_title('A* Path Planning')
    ax2.set_xlabel('X')
    ax2.set_ylabel('Y')
    
    # Plot path if found
    if path_result.found and len(path_result.path) > 0:
        path_x = []
        path_y = []
        for node in path_result.path:
            world_pos = ic.py_to_world_coords(node, grid_config)
            path_x.append(world_pos.x)
            path_y.append(world_pos.y)
        
        ax2.plot(path_x, path_y, 'g-', linewidth=3, alpha=0.7, label=f'A* Path ({len(path_result.path)} steps)')
        ax2.plot(path_x[0], path_y[0], 'go', markersize=8, label='Start')
        ax2.plot(path_x[-1], path_y[-1], 'r*', markersize=12, label='Goal')
    
    # Add defenders with Apollonian circles
    for i, defender in enumerate(defenders):
        ax2.plot(defender.position.x, defender.position.y, 'bs', markersize=10)
        
        # Calculate and draw Apollonian circle
        apollonian_circle = ic.py_calculate_apollonian_circle(
            defender.position, 
            intruder.position, 
            sim_config.speed_ratio()
        )
        
        if apollonian_circle.radius != float('inf') and apollonian_circle.radius < 20:
            circle = plt.Circle((apollonian_circle.center.x, apollonian_circle.center.y), 
                               apollonian_circle.radius, color='blue', alpha=0.2, linestyle='--')
            ax2.add_patch(circle)
    
    # Add intruder
    ax2.plot(intruder.position.x, intruder.position.y, 'ro', markersize=10)
    
    # Add protected zone
    circle = plt.Circle((protected_zone.center.x, protected_zone.center.y), 
                       protected_zone.radius, color='green', alpha=0.3)
    ax2.add_patch(circle)
    
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('pathfinding_test.png', dpi=150, bbox_inches='tight')
    # plt.show()  # Skip GUI display to avoid tkinter issues
    
    print(f"Visualization saved as 'pathfinding_test.png'")
    print(f"Path found: {path_result.found}")
    if path_result.found:
        print(f"Path length: {len(path_result.path)} steps")
        print(f"Total cost: {path_result.total_cost:.2f}")


def main():
    """Run all pathfinding tests."""
    print("=== Smart Intruder A* Pathfinding Tests ===\n")
    
    try:
        # Test basic functionality
        basic_test = test_pathfinding_basic()
        threat_test = test_threat_map_generation()
        
        print(f"\nTest Results:")
        print(f"Basic pathfinding: {'PASS' if basic_test else 'FAIL'}")
        print(f"Threat map generation: {'PASS' if threat_test else 'FAIL'}")
        
        # Create visualization
        visualize_pathfinding()
        
        if basic_test and threat_test:
            print("\n✅ All tests passed! Smart intruder A* pathfinding is working correctly.")
        else:
            print("\n❌ Some tests failed. Check the implementation.")
            
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()