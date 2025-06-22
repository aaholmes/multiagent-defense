#!/usr/bin/env python3
"""
Create an animated GIF of the multi-agent defense simulation for the README.

This script runs a simulation optimized for creating a compelling animation
that demonstrates the Apollonian circle-based defense strategy.
"""

import sys
import os
import shutil
from typing import Optional

# Add current directory to path for imports
current_dir = os.path.dirname(__file__)
if current_dir:
    sys.path.insert(0, current_dir)
else:
    sys.path.insert(0, 'simulation')

try:
    import interception_core as ic
except ImportError:
    print("Error: interception_core not found. Make sure to run 'maturin develop' first.")
    sys.exit(1)

try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
except ImportError:
    print("Error: matplotlib not found. Install with 'pip install matplotlib'")
    sys.exit(1)

import config
from visualizer import SimulationVisualizer
from run_simulation import DefenseSimulation, SimulationResult

# Animation-specific configuration
ANIMATION_CONFIG = {
    'timestep': 0.02,  # Smaller timestep for smoother animation
    'max_time': 8.0,   # Shorter simulation for demo
    'frame_rate': 10,  # Save every 10th frame for reasonable file size
    'figure_size': (10, 8),
    'dpi': 100,
    'world_bounds': 12,  # Tighter bounds for better view
    'show_trails': True,  # Add position trails
    'trail_length': 20,   # Number of trail points
}

class AnimationSimulation(DefenseSimulation):
    """Enhanced simulation class for creating animations"""
    
    def __init__(self):
        super().__init__(visualization_enabled=True)
        
        # Override configuration for animation
        self.animation_config = ANIMATION_CONFIG
        self.frame_count = 0
        self.frames_dir = "animation_frames"
        
        # Position history for trails
        self.position_history = {
            'intruder': [],
            'defenders': [[] for _ in range(len(self.world_state.defenders))]
        }
        
        # Setup frames directory
        if os.path.exists(self.frames_dir):
            shutil.rmtree(self.frames_dir)
        os.makedirs(self.frames_dir)
        
        # Configure visualizer for animation
        self.visualizer = SimulationVisualizer(figsize=self.animation_config['figure_size'])
        
        print(f"Animation setup complete")
        print(f"Frames will be saved to: {self.frames_dir}/")
    
    def _update_position_history(self):
        """Update position trails for animation"""
        # Add current intruder position
        intruder_pos = (
            self.world_state.intruder.position.x,
            self.world_state.intruder.position.y
        )
        self.position_history['intruder'].append(intruder_pos)
        
        # Add current defender positions
        for i, defender in enumerate(self.world_state.defenders):
            defender_pos = (defender.position.x, defender.position.y)
            self.position_history['defenders'][i].append(defender_pos)
        
        # Limit trail length
        max_trail = self.animation_config['trail_length']
        if len(self.position_history['intruder']) > max_trail:
            self.position_history['intruder'] = self.position_history['intruder'][-max_trail:]
        
        for i in range(len(self.position_history['defenders'])):
            if len(self.position_history['defenders'][i]) > max_trail:
                self.position_history['defenders'][i] = self.position_history['defenders'][i][-max_trail:]
    
    def _plot_trails(self):
        """Plot position trails for animation effect"""
        if not self.animation_config['show_trails']:
            return
        
        # Plot intruder trail
        if len(self.position_history['intruder']) > 1:
            trail_x = [pos[0] for pos in self.position_history['intruder']]
            trail_y = [pos[1] for pos in self.position_history['intruder']]
            
            # Create fading trail effect
            for i in range(len(trail_x) - 1):
                alpha = (i + 1) / len(trail_x) * 0.6  # Fade from 0 to 0.6
                self.visualizer.ax.plot(
                    trail_x[i:i+2], trail_y[i:i+2],
                    color='red', alpha=alpha, linewidth=2
                )
        
        # Plot defender trails
        defender_colors = config.COLORS['defenders']
        for i, trail in enumerate(self.position_history['defenders']):
            if len(trail) > 1:
                trail_x = [pos[0] for pos in trail]
                trail_y = [pos[1] for pos in trail]
                color = defender_colors[i % len(defender_colors)]
                
                for j in range(len(trail_x) - 1):
                    alpha = (j + 1) / len(trail_x) * 0.4
                    self.visualizer.ax.plot(
                        trail_x[j:j+2], trail_y[j:j+2],
                        color=color, alpha=alpha, linewidth=1.5
                    )
    
    def _visualize_animation_frame(self):
        """Create a frame optimized for animation"""
        # Clear previous plot
        self.visualizer.clear()
        
        # Plot trails first (behind other elements)
        self._plot_trails()
        
        # Plot protected zone
        self.visualizer.plot_protected_zone(
            self.world_state.protected_zone.center,
            self.world_state.protected_zone.radius
        )
        
        # Plot intruder with enhanced visibility
        self.visualizer.plot_intruder(self.world_state.intruder.position)
        
        # Add intruder velocity vector
        intruder_vel = self.world_state.intruder.velocity
        if intruder_vel.magnitude() > 0.1:
            scale = 1.5  # Scale factor for visibility
            self.visualizer.ax.arrow(
                self.world_state.intruder.position.x,
                self.world_state.intruder.position.y,
                intruder_vel.x * scale,
                intruder_vel.y * scale,
                head_width=0.4, head_length=0.3,
                fc='darkred', ec='darkred', alpha=0.8, linewidth=2
            )
        
        # Plot defenders and their Apollonian circles
        for i, defender in enumerate(self.world_state.defenders):
            color = config.COLORS['defenders'][i % len(config.COLORS['defenders'])]
            
            # Plot defender
            self.visualizer.plot_defender(
                defender.position,
                label=f"Defender {i+1}" if self.frame_count == 0 else None
            )
            
            # Plot Apollonian circle
            apollonian_circle = ic.py_calculate_apollonian_circle(
                defender.position,
                self.world_state.intruder.position,
                self.sim_config.speed_ratio()
            )
            
            if apollonian_circle.radius != float('inf') and apollonian_circle.radius < 50:
                self.visualizer.plot_circle(
                    apollonian_circle,
                    color=color,
                    alpha=0.15,
                    linestyle='--',
                    linewidth=1.5,
                    fill=True
                )
            
            # Add defender velocity vector
            defender_vel = defender.velocity
            if defender_vel.magnitude() > 0.1:
                scale = 1.2
                self.visualizer.ax.arrow(
                    defender.position.x, defender.position.y,
                    defender_vel.x * scale, defender_vel.y * scale,
                    head_width=0.3, head_length=0.2,
                    fc=color, ec=color, alpha=0.7, linewidth=1.5
                )
        
        # Set plot properties
        bounds = self.animation_config['world_bounds']
        self.visualizer.set_bounds(-bounds, bounds, -bounds, bounds)
        
        # Title with simulation info
        intruder_distance = self.world_state.intruder.position.distance_to(
            ic.Point(*config.PROTECTED_ZONE_CENTER)
        )
        self.visualizer.set_title(
            f"Multi-Agent Defense: Apollonian Circle Strategy\n"
            f"Time: {self.time_elapsed:.1f}s | Intruder Distance: {intruder_distance:.1f}"
        )
        
        # Add legend only for first frame
        if self.frame_count == 0:
            self.visualizer.add_legend()
        
        # Save frame
        frame_filename = os.path.join(self.frames_dir, f"frame_{self.frame_count:04d}.png")
        self.visualizer.save(frame_filename, dpi=self.animation_config['dpi'])
        
        self.frame_count += 1
    
    def run_animation(self) -> SimulationResult:
        """Run simulation optimized for animation creation"""
        print(f"Starting animation simulation...")
        print(f"Target duration: {self.animation_config['max_time']}s")
        
        dt = self.animation_config['timestep']
        max_timesteps = int(self.animation_config['max_time'] / dt)
        frame_rate = self.animation_config['frame_rate']
        
        # Initial frame
        self._update_position_history()
        self._visualize_animation_frame()
        
        # Main simulation loop
        for step in range(max_timesteps):
            # Update simulation
            self._update_intruder(dt)
            self._update_defenders(dt)
            
            self.timestep += 1
            self.time_elapsed = self.timestep * dt
            
            # Update position history
            self._update_position_history()
            
            # Check end conditions
            result = self._check_end_conditions()
            if result is not None:
                # Final frame
                self._visualize_animation_frame()
                print(f"Animation completed: {result.reason}")
                return result
            
            # Save frame at specified rate
            if step % frame_rate == 0:
                self._visualize_animation_frame()
                if step % (frame_rate * 10) == 0:  # Progress update every 10 frames
                    intruder_dist = self.world_state.intruder.position.distance_to(
                        ic.Point(*config.PROTECTED_ZONE_CENTER)
                    )
                    print(f"t={self.time_elapsed:.1f}s: Frame {self.frame_count}, Distance = {intruder_dist:.1f}")
        
        # Simulation ended without decisive result
        final_distance = self.world_state.intruder.position.distance_to(
            ic.Point(*config.PROTECTED_ZONE_CENTER)
        )
        return SimulationResult("Timeout", self.time_elapsed, final_distance, "Animation duration reached")

def main():
    """Create animation frames for GIF generation"""
    print("=" * 60)
    print("Creating Multi-Agent Defense Animation")
    print("=" * 60)
    
    try:
        # Run animation simulation
        sim = AnimationSimulation()
        result = sim.run_animation()
        
        print(f"\n" + "=" * 60)
        print("ANIMATION CREATION RESULTS")
        print("=" * 60)
        print(f"Simulation result: {result}")
        print(f"Total frames created: {sim.frame_count}")
        print(f"Frames directory: {sim.frames_dir}/")
        print(f"\nTo create GIF, run:")
        print(f"python simulation/create_gif.py")
        
    except KeyboardInterrupt:
        print("\nAnimation creation interrupted by user.")
        return 1
    except Exception as e:
        print(f"Error during animation creation: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())