#!/usr/bin/env python3
"""
Main simulation runner for the multi-agent defense system.

This script implements the complete simulation loop as described in the PRD:
1. Initialize world state with defenders and intruder
2. Run simulation loop:
   - Get velocity commands from Rust controller
   - Update defender positions
   - Move intruder toward goal
   - Check end conditions
   - Visualize current state
   - Repeat until win/loss/timeout
"""

import sys
import os
import math
import time
from typing import List, Tuple, Optional

# Add current directory to path for imports
current_dir = os.path.dirname(__file__)
if current_dir:
    sys.path.insert(0, current_dir)
else:
    # If __file__ is not available, assume we're in the simulation directory
    sys.path.insert(0, 'simulation')

try:
    import interception_core as ic
except ImportError:
    print("Error: interception_core not found. Make sure to run 'maturin develop' first.")
    sys.exit(1)

try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend for headless environments
    import matplotlib.pyplot as plt
except ImportError:
    print("Error: matplotlib not found. Install with 'pip install matplotlib'")
    sys.exit(1)

import config
from visualizer import SimulationVisualizer
from smart_intruder import SmartIntruder

class SimulationResult:
    """Stores the result of a simulation run"""
    def __init__(self, winner: str, time_elapsed: float, final_distance: float, reason: str):
        self.winner = winner
        self.time_elapsed = time_elapsed
        self.final_distance = final_distance
        self.reason = reason
    
    def __str__(self):
        return f"Result: {self.winner} wins after {self.time_elapsed:.2f}s (reason: {self.reason})"

class DefenseSimulation:
    """Main simulation class that orchestrates the multi-agent defense"""
    
    def __init__(self, visualization_enabled: bool = True):
        self.visualization_enabled = visualization_enabled
        self.timestep = 0
        self.time_elapsed = 0.0
        
        # Initialize configuration
        self.sim_config = config.get_simulation_config()
        if self.sim_config is None:
            raise RuntimeError("Failed to create simulation configuration")
        
        # Initialize world state
        self.world_state = self._create_initial_world_state()
        
        # Initialize defender states for three-state FSM
        self.defender_states = [ic.ControlState.Travel for _ in range(len(self.world_state.defenders))]
        
        # Initialize grid configuration for pathfinding
        self.grid_config = ic.GridConfig(
            width=80,
            height=80,
            world_bounds=(-config.WORLD_SIZE, config.WORLD_SIZE, -config.WORLD_SIZE, config.WORLD_SIZE),
            base_cost=1.0,
            threat_penalty=1000.0
        )
        
        # Initialize smart intruder AI
        self.smart_intruder = SmartIntruder(
            initial_position=self.world_state.intruder.position,
            max_speed=config.INTRUDER_SPEED,
            grid_config=self.grid_config
        )
        
        # Initialize visualizer
        if self.visualization_enabled:
            self.visualizer = SimulationVisualizer(figsize=(12, 10))
            if config.SAVE_FRAMES:
                os.makedirs(config.FRAME_DIRECTORY, exist_ok=True)
        
        print("Defense Simulation initialized")
        print(f"Defenders: {len(self.world_state.defenders)}")
        print(f"Speed ratio: {self.sim_config.speed_ratio():.2f}")
    
    def _create_initial_world_state(self) -> ic.WorldState:
        """Create initial world state with defenders and intruder"""
        
        # Create protected zone
        protected_zone = ic.Circle(
            ic.Point(*config.PROTECTED_ZONE_CENTER),
            config.PROTECTED_ZONE_RADIUS
        )
        
        # Create defenders in semi-circle formation
        defenders = []
        defender_positions = config.get_initial_defender_positions()
        
        for x, y in defender_positions:
            defender = ic.AgentState(
                position=ic.Point(x, y),
                velocity=ic.Point(0.0, 0.0)  # Start stationary
            )
            defenders.append(defender)
        
        # Create intruder moving toward protected zone
        intruder_x, intruder_y = config.get_initial_intruder_position()
        
        # Calculate initial velocity toward protected zone center
        distance_to_goal = math.sqrt(intruder_x**2 + intruder_y**2)
        intruder_vel_x = -intruder_x / distance_to_goal * config.INTRUDER_SPEED
        intruder_vel_y = -intruder_y / distance_to_goal * config.INTRUDER_SPEED
        
        intruder = ic.AgentState(
            position=ic.Point(intruder_x, intruder_y),
            velocity=ic.Point(intruder_vel_x, intruder_vel_y)
        )
        
        return ic.WorldState(defenders, intruder, protected_zone)
    
    def _update_intruder(self, dt: float):
        """Update intruder position using smart AI pathfinding"""
        # Update smart intruder AI (this calculates new velocity based on A* pathfinding)
        self.smart_intruder.update(self.world_state, self.sim_config)
        
        # Move the smart intruder
        self.smart_intruder.move(dt)
        
        # Update world state with new intruder position and velocity
        new_intruder = ic.AgentState(
            position=self.smart_intruder.position,
            velocity=self.smart_intruder.velocity
        )
        
        # Create new world state with updated intruder
        self.world_state = ic.WorldState(
            self.world_state.defenders,
            new_intruder,
            self.world_state.protected_zone
        )
    
    def _update_defenders(self, dt: float):
        """Update defender positions using Rust controller with three-state FSM"""
        # Get velocity commands and updated states from Rust controller
        velocity_commands, updated_states = ic.py_get_defender_velocity_commands_with_states(
            self.world_state, 
            self.defender_states,
            self.sim_config
        )
        
        # Update stored defender states
        self.defender_states = updated_states
        
        # Create updated defenders
        updated_defenders = []
        for i, vel_cmd in enumerate(velocity_commands):
            if i < len(self.world_state.defenders):
                defender = self.world_state.defenders[i]
                
                # Calculate new position
                new_x = defender.position.x + vel_cmd.x * dt
                new_y = defender.position.y + vel_cmd.y * dt
                
                # Create new defender state
                updated_defender = ic.AgentState(
                    position=ic.Point(new_x, new_y),
                    velocity=ic.Point(vel_cmd.x, vel_cmd.y)
                )
                updated_defenders.append(updated_defender)
        
        # Create new world state with updated defenders
        self.world_state = ic.WorldState(
            updated_defenders,
            self.world_state.intruder,
            self.world_state.protected_zone
        )
    
    def _check_end_conditions(self) -> Optional[SimulationResult]:
        """Check if simulation should end and return result"""
        
        intruder_pos = self.world_state.intruder.position
        goal_pos = ic.Point(*config.PROTECTED_ZONE_CENTER)
        
        # Check if intruder reached protected zone
        distance_to_goal = intruder_pos.distance_to(goal_pos)
        if distance_to_goal <= config.INTRUDER_WIN_DISTANCE:
            return SimulationResult(
                "Intruder", 
                self.time_elapsed, 
                distance_to_goal,
                f"Reached protected zone (distance: {distance_to_goal:.2f})"
            )
        
        # Check if any defender caught intruder
        for i, defender in enumerate(self.world_state.defenders):
            distance_to_intruder = defender.position.distance_to(intruder_pos)
            if distance_to_intruder <= config.DEFENDER_WIN_DISTANCE:
                return SimulationResult(
                    "Defenders", 
                    self.time_elapsed, 
                    distance_to_intruder,
                    f"Defender {i} intercepted intruder (distance: {distance_to_intruder:.2f})"
                )
        
        # Check for timeout
        if self.time_elapsed >= config.MAX_SIMULATION_TIME:
            return SimulationResult(
                "Stalemate", 
                self.time_elapsed, 
                distance_to_goal,
                f"Simulation timeout ({config.MAX_SIMULATION_TIME}s)"
            )
        
        # Check for stalemate (intruder not making progress)
        if self.time_elapsed >= config.STALEMATE_TIME and distance_to_goal > config.PROTECTED_ZONE_RADIUS * 3:
            return SimulationResult(
                "Stalemate", 
                self.time_elapsed, 
                distance_to_goal,
                f"No progress after {config.STALEMATE_TIME}s"
            )
        
        return None
    
    def _visualize_current_state(self, save_frame: bool = False):
        """Visualize current simulation state"""
        if not self.visualization_enabled:
            return
        
        # Clear previous plot
        self.visualizer.clear()
        
        # Plot protected zone
        self.visualizer.plot_protected_zone(
            self.world_state.protected_zone.center,
            self.world_state.protected_zone.radius
        )
        
        # Plot intruder
        self.visualizer.plot_intruder(self.world_state.intruder.position)
        
        # Plot A* path if available
        try:
            path_result = self.smart_intruder.get_current_path(self.world_state, self.sim_config)
            if path_result.found and len(path_result.path) > 1:
                # Convert path to world coordinates, stopping at goal circle boundary
                path_x = []
                path_y = []
                goal_center = self.world_state.protected_zone.center
                goal_radius = self.world_state.protected_zone.radius
                
                for node in path_result.path[:min(20, len(path_result.path))]:  # Limit to first 20 steps for clarity
                    world_pos = ic.py_to_world_coords(node, self.grid_config)
                    
                    # Check if this point is inside the goal circle
                    distance_to_goal = math.sqrt(
                        (world_pos.x - goal_center.x)**2 + 
                        (world_pos.y - goal_center.y)**2
                    )
                    
                    if distance_to_goal <= goal_radius:
                        # This point is inside goal - stop path here
                        path_x.append(world_pos.x)
                        path_y.append(world_pos.y)
                        break
                    else:
                        path_x.append(world_pos.x)
                        path_y.append(world_pos.y)
                
                # Plot path
                if len(path_x) > 1:
                    self.visualizer.ax.plot(path_x, path_y, 'g--', alpha=0.6, linewidth=2, label='A* Path')
        except Exception as e:
            # Don't let path visualization errors break the simulation
            pass
        
        # Plot defenders and their Apollonian circles
        for i, defender in enumerate(self.world_state.defenders):
            color = config.COLORS['defenders'][i % len(config.COLORS['defenders'])]
            
            # Get defender state for color coding
            defender_state = self.defender_states[i] if i < len(self.defender_states) else ic.ControlState.Travel
            
            # Plot defender with state-based coloring
            self.visualizer.plot_defender(
                defender.position, 
                state=defender_state,
                label=f"Defender {i+1}"
            )
            
            # Plot Apollonian circle if enabled
            if config.SHOW_APOLLONIAN_CIRCLES:
                apollonian_circle = ic.py_calculate_apollonian_circle(
                    defender.position,
                    self.world_state.intruder.position,
                    self.sim_config.speed_ratio()
                )
                
                if apollonian_circle.radius != float('inf'):
                    self.visualizer.plot_circle(
                        apollonian_circle,
                        color=color,
                        alpha=config.APOLLONIAN_ALPHA,
                        linestyle='--',
                        linewidth=1,
                        fill=True
                    )
            
            # Plot velocity vectors if enabled
            if config.SHOW_VELOCITY_VECTORS:
                end_x = defender.position.x + defender.velocity.x
                end_y = defender.position.y + defender.velocity.y
                self.visualizer.ax.arrow(
                    defender.position.x, defender.position.y,
                    defender.velocity.x, defender.velocity.y,
                    head_width=0.3, head_length=0.2, 
                    fc=config.COLORS['velocity'], ec=config.COLORS['velocity'],
                    alpha=0.7
                )
        
        # Set plot properties
        self.visualizer.set_bounds(-config.WORLD_SIZE, config.WORLD_SIZE, 
                                  -config.WORLD_SIZE, config.WORLD_SIZE)
        self.visualizer.set_title(
            f"Multi-Agent Defense - Time: {self.time_elapsed:.1f}s\n"
            f"Intruder distance to goal: {self.world_state.intruder.position.distance_to(ic.Point(*config.PROTECTED_ZONE_CENTER)):.1f}"
        )
        self.visualizer.add_legend()
        
        # Save frame if requested
        if save_frame and config.SAVE_FRAMES:
            filename = os.path.join(config.FRAME_DIRECTORY, f"frame_{self.timestep:04d}.png")
            self.visualizer.save(filename, dpi=150)
    
    def run(self) -> SimulationResult:
        """Run the complete simulation"""
        print(f"Starting simulation...")
        print(f"Initial intruder distance: {self.world_state.intruder.position.distance_to(ic.Point(*config.PROTECTED_ZONE_CENTER)):.2f}")
        
        start_time = time.time()
        dt = config.TIMESTEP_DURATION
        
        # Initial visualization
        self._visualize_current_state(save_frame=True)
        
        # Main simulation loop
        while self.timestep < config.MAX_TIMESTEPS:
            # Update positions
            self._update_intruder(dt)
            self._update_defenders(dt)
            
            # Update time
            self.timestep += 1
            self.time_elapsed = self.timestep * dt
            
            # Check end conditions
            result = self._check_end_conditions()
            if result is not None:
                # Final visualization
                self._visualize_current_state(save_frame=True)
                
                if config.SAVE_FRAMES:
                    self.visualizer.save(f"final_result_{result.winner.lower()}.png")
                else:
                    self.visualizer.save("simulation_result.png")
                
                print(f"Simulation completed in {time.time() - start_time:.2f} real seconds")
                return result
            
            # Visualize every frame for smooth A* demonstration
            if self.timestep % 2 == 0:  # Visualize every 2nd timestep for smoother animation
                self._visualize_current_state(save_frame=config.SAVE_FRAMES)
                
                # Print progress
                if self.timestep % 10 == 0:  # Print progress less frequently
                    intruder_dist = self.world_state.intruder.position.distance_to(ic.Point(*config.PROTECTED_ZONE_CENTER))
                    print(f"t={self.time_elapsed:.1f}s: Intruder distance = {intruder_dist:.2f}")
        
        # Simulation ended without decisive result
        final_distance = self.world_state.intruder.position.distance_to(ic.Point(*config.PROTECTED_ZONE_CENTER))
        return SimulationResult("Timeout", self.time_elapsed, final_distance, "Maximum timesteps reached")

def main():
    """Main entry point"""
    print("=" * 50)
    print("Multi-Agent Defense Simulation")
    print("=" * 50)
    
    # Print configuration
    config.print_config()
    
    try:
        # Run simulation
        sim = DefenseSimulation(visualization_enabled=config.VISUALIZATION_ENABLED)
        result = sim.run()
        
        # Print results
        print("\n" + "=" * 50)
        print("SIMULATION RESULTS")
        print("=" * 50)
        print(result)
        
        if result.winner == "Defenders":
            print("🛡️  The defenders successfully protected the zone!")
        elif result.winner == "Intruder":
            print("🚨 The intruder breached the protected zone!")
        else:
            print("⏱️  Simulation ended in stalemate.")
        
        print(f"Final visualization saved to: simulation_result.png")
        
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user.")
    except Exception as e:
        print(f"Error during simulation: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())