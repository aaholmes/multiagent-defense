"""
Visualization module for the multi-agent defense simulation.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from typing import List, Optional
try:
    # Try to use Rust implementation first
    import interception_core as ic
    Point = ic.Point
    Circle = ic.Circle
    calculate_apollonian_circle = ic.py_calculate_apollonian_circle
except ImportError:
    # Fall back to pure Python implementation
    from geometry_pure import Point, Circle, calculate_apollonian_circle


class SimulationVisualizer:
    def __init__(self, figsize=(10, 10)):
        self.fig, self.ax = plt.subplots(figsize=figsize)
        self.ax.set_aspect('equal')
        self.ax.grid(True, alpha=0.3)
        
    def clear(self):
        """Clear the current plot"""
        self.ax.clear()
        self.ax.set_aspect('equal')
        self.ax.grid(True, alpha=0.3)
        
    def plot_circle(self, circle: Circle, color='blue', alpha=0.3, linestyle='-', linewidth=2, fill=True):
        """Plot a circle on the visualization"""
        if circle.radius == float('inf'):
            # Skip infinite circles
            return
            
        circle_patch = patches.Circle(
            (circle.center.x, circle.center.y), 
            circle.radius,
            color=color,
            alpha=alpha,
            fill=fill,
            linestyle=linestyle,
            linewidth=linewidth
        )
        self.ax.add_patch(circle_patch)
        
    def plot_point(self, point: Point, color='red', size=100, marker='o', label=None):
        """Plot a point on the visualization"""
        self.ax.scatter(point.x, point.y, c=color, s=size, marker=marker, label=label)
        
    def plot_protected_zone(self, center: Point, radius: float):
        """Plot the protected zone (goal area)"""
        self.plot_circle(
            Circle(center, radius),
            color='green',
            alpha=0.2,
            linewidth=3,
            fill=True
        )
        self.plot_point(center, color='darkgreen', size=50, marker='*', label='Protected Zone')
        
    def plot_defender(self, position: Point, label: Optional[str] = None):
        """Plot a defender robot"""
        display_label = label or 'Defender'
        self.plot_point(position, color='blue', size=150, marker='s', label=display_label)
        
    def plot_intruder(self, position: Point):
        """Plot the intruder"""
        self.plot_point(position, color='red', size=150, marker='^', label='Intruder')
        
    def plot_apollonian_circle(self, defender_pos: Point, intruder_pos: Point, speed_ratio: float):
        """Plot the Apollonian circle (defender's region of dominance)"""
        apollonian = calculate_apollonian_circle(defender_pos, intruder_pos, speed_ratio)
        
        if apollonian.radius != float('inf'):
            self.plot_circle(
                apollonian,
                color='blue',
                alpha=0.15,
                linestyle='--',
                linewidth=2,
                fill=True
            )
        
    def set_bounds(self, x_min=-10, x_max=10, y_min=-10, y_max=10):
        """Set the plot bounds"""
        self.ax.set_xlim(x_min, x_max)
        self.ax.set_ylim(y_min, y_max)
        
    def add_legend(self):
        """Add legend to the plot"""
        self.ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
    def set_title(self, title: str):
        """Set the plot title"""
        self.ax.set_title(title, fontsize=14, fontweight='bold')
        
    def show(self):
        """Display the plot"""
        plt.tight_layout()
        plt.show()
        
    def save(self, filename: str, dpi=300):
        """Save the plot to file"""
        plt.tight_layout()
        plt.savefig(filename, dpi=dpi, bbox_inches='tight')


def create_basic_scenario():
    """Create a basic test scenario for visualization"""
    
    # Scene setup
    protected_zone_center = Point(0, 0)
    protected_zone_radius = 2.0
    
    # Positions
    intruder_pos = Point(8, 0)
    defender_pos = Point(-5, 3)
    
    # Speed ratio (defender is slower)
    speed_ratio = 0.7  # defender_speed / intruder_speed
    
    return {
        'protected_zone_center': protected_zone_center,
        'protected_zone_radius': protected_zone_radius,
        'intruder_pos': intruder_pos,
        'defender_pos': defender_pos,
        'speed_ratio': speed_ratio
    }


if __name__ == "__main__":
    # Create and display a basic scenario
    scenario = create_basic_scenario()
    viz = SimulationVisualizer()
    
    # Plot the scene
    viz.plot_protected_zone(
        scenario['protected_zone_center'], 
        scenario['protected_zone_radius']
    )
    
    viz.plot_intruder(scenario['intruder_pos'])
    viz.plot_defender(scenario['defender_pos'])
    
    # Plot the Apollonian circle
    viz.plot_apollonian_circle(
        scenario['defender_pos'],
        scenario['intruder_pos'], 
        scenario['speed_ratio']
    )
    
    viz.set_bounds(-8, 10, -6, 6)
    viz.set_title(f"Multi-Agent Defense: Apollonian Circle Demo\nSpeed Ratio = {scenario['speed_ratio']}")
    viz.add_legend()
    viz.show()