#!/usr/bin/env python3

import sys
import os

# Add venv to path  
venv_site_packages = os.path.join(os.path.dirname(__file__), 'venv', 'lib', 'python3.9', 'site-packages')
sys.path.insert(0, venv_site_packages)

print("🧪 Running Comprehensive Integration Tests")
print("=" * 50)

# Test 1: Basic imports
print("Test 1: Core imports...")
try:
    import interception_core as ic
    import matplotlib
    print("✅ All core modules imported successfully")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Rust library functionality
print("\nTest 2: Rust library functionality...")
try:
    # Test Apollonian circle calculation
    defender = ic.Point(0.0, 0.0)
    intruder = ic.Point(4.0, 0.0)
    circle = ic.py_calculate_apollonian_circle(defender, intruder, 0.5)
    
    # Verify correctness
    p1 = ic.Point(4.0/3.0, 0.0)  # 1/3 toward intruder
    p2 = ic.Point(-4.0, 0.0)     # d behind defender
    dist1 = circle.center.distance_to(p1)
    dist2 = circle.center.distance_to(p2)
    
    assert abs(dist1 - circle.radius) < 1e-10, f"Expected {circle.radius}, got {dist1}"
    assert abs(dist2 - circle.radius) < 1e-10, f"Expected {circle.radius}, got {dist2}"
    print("✅ Apollonian circle calculation verified")
except Exception as e:
    print(f"❌ Rust functionality test failed: {e}")
    sys.exit(1)

# Test 3: Controller functionality  
print("\nTest 3: Controller functionality...")
try:
    defender_state = ic.AgentState(ic.Point(-3.0, 0.0), ic.Point(0.0, 0.0))
    intruder_state = ic.AgentState(ic.Point(10.0, 0.0), ic.Point(-1.0, 0.0))
    protected_zone = ic.Circle(ic.Point(0.0, 0.0), 2.0)
    world_state = ic.WorldState([defender_state], intruder_state, protected_zone)
    config = ic.SimConfig(0.1, 2.0, 4.0, 1.0, 0.1)
    
    velocities = ic.py_get_defender_velocity_commands(world_state, config)
    assert len(velocities) == 1, f"Expected 1 velocity command, got {len(velocities)}"
    assert velocities[0].magnitude() <= config.defender_speed + 1e-10, "Velocity exceeds max speed"
    print("✅ Controller generates valid velocity commands")
except Exception as e:
    print(f"❌ Controller test failed: {e}")
    sys.exit(1)

# Test 4: Configuration system
print("\nTest 4: Configuration system...")
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'simulation'))
    import config
    
    sim_config = config.get_simulation_config()
    assert sim_config is not None, "Failed to create simulation config"
    assert sim_config.speed_ratio() == 0.5, f"Expected speed ratio 0.5, got {sim_config.speed_ratio()}"
    
    defender_positions = config.get_initial_defender_positions()
    assert len(defender_positions) == config.NUM_DEFENDERS, "Wrong number of initial positions"
    print("✅ Configuration system working")
except Exception as e:
    print(f"❌ Configuration test failed: {e}")
    sys.exit(1)

# Test 5: Visualization system
print("\nTest 5: Visualization system...")
try:
    from visualizer import SimulationVisualizer
    
    viz = SimulationVisualizer(figsize=(6, 6))
    viz.plot_protected_zone(ic.Point(0.0, 0.0), 2.0)
    viz.plot_intruder(ic.Point(5.0, 0.0))
    viz.plot_defender(ic.Point(-3.0, 0.0))
    print("✅ Visualization system working")
except Exception as e:
    print(f"❌ Visualization test failed: {e}")
    sys.exit(1)

# Test 6: Full simulation (abbreviated)
print("\nTest 6: Complete simulation...")
try:
    # Import and run simulation for a few steps
    from run_simulation import DefenseSimulation
    
    sim = DefenseSimulation(visualization_enabled=False)
    
    # Run a few timesteps manually
    initial_distance = sim.world_state.intruder.position.distance_to(ic.Point(0.0, 0.0))
    
    # Update once
    sim._update_intruder(0.05)
    sim._update_defenders(0.05)
    sim.timestep += 1
    sim.time_elapsed = 0.05
    
    new_distance = sim.world_state.intruder.position.distance_to(ic.Point(0.0, 0.0))
    
    assert new_distance < initial_distance, f"Intruder not moving: {initial_distance} -> {new_distance}"
    print(f"✅ Complete simulation working (intruder moved from {initial_distance:.1f} to {new_distance:.1f})")
except Exception as e:
    print(f"❌ Full simulation test failed: {e}")
    sys.exit(1)

print("\n" + "=" * 50)
print("🎉 ALL TESTS PASSED! System is fully functional.")
print("✅ Rust core library: Working")
print("✅ Python bindings: Working") 
print("✅ Controller AI: Working")
print("✅ Configuration: Working")
print("✅ Visualization: Working")
print("✅ Full simulation: Working")
print("=" * 50)