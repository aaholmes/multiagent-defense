"""
Smart Intruder AI using A* pathfinding to avoid defender Apollonian circles.
"""

import interception_core as ic
from typing import Optional


class SmartIntruder:
    """
    An intelligent intruder that uses A* pathfinding to navigate around 
    defender threat zones (Apollonian circles) while trying to reach the goal.
    """
    
    def __init__(self, initial_position: ic.Point, max_speed: float, grid_config: ic.GridConfig):
        """
        Initialize the smart intruder.
        
        Args:
            initial_position: Starting position of the intruder
            max_speed: Maximum movement speed
            grid_config: Grid configuration for pathfinding
        """
        self.position = initial_position
        self.max_speed = max_speed
        self.grid_config = grid_config
        self.velocity = ic.Point(0.0, 0.0)
        self.current_path = []
        self.target_position = None
        
    def update(self, world_state: ic.WorldState, sim_config: ic.SimConfig) -> None:
        """
        Update intruder movement using A* pathfinding.
        
        This method:
        1. Generates a threat map based on current defender positions
        2. Plans a new path using A* from current position to goal
        3. Calculates velocity toward the next waypoint
        4. Handles fallback behaviors if no path is found
        
        Args:
            world_state: Current state of the simulation world
            sim_config: Simulation configuration parameters
        """
        # Update current position in world state
        world_state.intruder.position = self.position
        
        # Calculate next target position using Rust A* pathfinding
        next_target = ic.py_calculate_intruder_next_position(
            world_state, 
            self.grid_config, 
            sim_config
        )
        
        if next_target is not None:
            # Calculate velocity toward next target
            direction = ic.Point(
                next_target.x - self.position.x,
                next_target.y - self.position.y
            )
            
            # Normalize and scale to max speed
            direction_magnitude = direction.magnitude()
            if direction_magnitude > 0:
                normalized = direction.normalize()
                self.velocity = ic.Point(
                    normalized.x * self.max_speed,
                    normalized.y * self.max_speed
                )
                self.target_position = next_target
            else:
                # Already at target
                self.velocity = ic.Point(0.0, 0.0)
        else:
            # No path found - try fallback behavior
            self._handle_no_path_fallback(world_state, sim_config)
    
    def _handle_no_path_fallback(self, world_state: ic.WorldState, sim_config: ic.SimConfig) -> None:
        """
        Handle case where no path to goal is found (e.g., completely surrounded).
        
        Fallback strategies:
        1. Move toward the closest defender to try to create an opening
        2. Move toward goal directly (simple greedy approach)
        3. Stop moving
        
        Args:
            world_state: Current world state
            sim_config: Simulation configuration
        """
        if len(world_state.defenders) == 0:
            # No defenders, move directly toward goal
            self._move_toward_goal(world_state.protected_zone.center)
            return
        
        # Strategy 1: Move toward closest defender to create opening
        closest_defender = None
        min_distance = float('inf')
        
        for defender in world_state.defenders:
            distance = self.position.distance_to(defender.position)
            if distance < min_distance:
                min_distance = distance
                closest_defender = defender
        
        if closest_defender is not None:
            # Move toward closest defender at reduced speed
            direction = ic.Point(
                closest_defender.position.x - self.position.x,
                closest_defender.position.y - self.position.y
            )
            
            direction_magnitude = direction.magnitude()
            if direction_magnitude > 0:
                normalized = direction.normalize()
                # Use reduced speed for cautious approach
                self.velocity = ic.Point(
                    normalized.x * self.max_speed * 0.5,
                    normalized.y * self.max_speed * 0.5
                )
            else:
                self.velocity = ic.Point(0.0, 0.0)
        else:
            # Fallback: move directly toward goal
            self._move_toward_goal(world_state.protected_zone.center)
    
    def _move_toward_goal(self, goal_center: ic.Point) -> None:
        """
        Simple direct movement toward goal (ignoring threats).
        
        Args:
            goal_center: Center of the protected zone (goal)
        """
        direction = ic.Point(
            goal_center.x - self.position.x,
            goal_center.y - self.position.y
        )
        
        direction_magnitude = direction.magnitude()
        if direction_magnitude > 0:
            normalized = direction.normalize()
            self.velocity = ic.Point(
                normalized.x * self.max_speed,
                normalized.y * self.max_speed
            )
        else:
            self.velocity = ic.Point(0.0, 0.0)
    
    def move(self, dt: float) -> None:
        """
        Update position based on current velocity.
        
        Args:
            dt: Time step for integration
        """
        self.position.x += self.velocity.x * dt
        self.position.y += self.velocity.y * dt
    
    def get_current_path(self, world_state: ic.WorldState, sim_config: ic.SimConfig) -> ic.PathResult:
        """
        Get the full planned path for visualization purposes.
        
        Args:
            world_state: Current world state
            sim_config: Simulation configuration
            
        Returns:
            PathResult containing the full planned path
        """
        # Update world state with current position
        world_state.intruder.position = self.position
        
        return ic.py_calculate_intruder_full_path(
            world_state,
            self.grid_config,
            sim_config
        )
    
    def get_threat_map(self, world_state: ic.WorldState, sim_config: ic.SimConfig) -> list:
        """
        Get the current threat map for visualization purposes.
        
        Args:
            world_state: Current world state
            sim_config: Simulation configuration
            
        Returns:
            2D list representing the threat cost map
        """
        # Update world state with current position
        world_state.intruder.position = self.position
        
        return ic.py_generate_threat_map(
            world_state,
            self.grid_config,
            sim_config
        )