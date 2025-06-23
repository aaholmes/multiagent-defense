#!/usr/bin/env python3
"""
Create extreme scenarios to demonstrate intruder breakthrough and edge cases.
"""

import os
import sys
import shutil
import math
import subprocess

# Add simulation directory to path
sys.path.append('simulation')
import config
from run_simulation import DefenseSimulation
import interception_core as ic

class ExtremeScenarioGenerator:
    """Generate extreme scenarios with intruder breakthroughs and edge cases"""
    
    def __init__(self):
        self.scenarios_dir = "scenario_gifs"
        os.makedirs(self.scenarios_dir, exist_ok=True)
    
    def backup_original_config(self):
        """Backup original config values"""
        self.original_config = {
            'NUM_DEFENDERS': config.NUM_DEFENDERS,
            'DEFENDER_SPEED': config.DEFENDER_SPEED,
            'INTRUDER_SPEED': config.INTRUDER_SPEED,
            'INTRUDER_INITIAL_DISTANCE': config.INTRUDER_INITIAL_DISTANCE,
            'INTRUDER_INITIAL_ANGLE': config.INTRUDER_INITIAL_ANGLE,
            'SAVE_FRAMES': config.SAVE_FRAMES,
            'VISUALIZATION_ENABLED': config.VISUALIZATION_ENABLED,
            'DEFENDER_WIN_DISTANCE': config.DEFENDER_WIN_DISTANCE,
            'get_initial_defender_positions': config.get_initial_defender_positions,
            'get_initial_intruder_position': config.get_initial_intruder_position
        }
    
    def restore_original_config(self):
        """Restore original config values"""
        for key, value in self.original_config.items():
            setattr(config, key, value)
    
    def set_scenario_config(self, scenario_config):
        """Apply scenario-specific configuration"""
        for key, value in scenario_config.items():
            setattr(config, key, value)
    
    def override_initial_positions(self, defender_positions, intruder_pos):
        """Override config functions to return specific positions"""
        config.get_initial_defender_positions = lambda: defender_positions
        config.get_initial_intruder_position = lambda: intruder_pos
    
    def create_gif_from_frames(self, frame_dir, output_gif):
        """Create GIF from frame directory"""
        try:
            cmd = [
                sys.executable, "simulation/create_gif.py", 
                frame_dir, output_gif, "0.08"  # Faster animation
            ]
            subprocess.run(cmd, check=True)
            print(f"✅ GIF created: {output_gif}")
        except Exception as e:
            print(f"❌ Failed to create GIF: {e}")
    
    def run_scenario(self, scenario_name, scenario_config, defender_positions, intruder_pos):
        """Run a single scenario"""
        print(f"\n🎬 Creating Scenario: {scenario_name}")
        print("=" * 60)
        
        # Set up scenario
        self.set_scenario_config(scenario_config)
        self.override_initial_positions(defender_positions, intruder_pos)
        
        # Create scenario-specific frame directory
        scenario_frame_dir = f"{self.scenarios_dir}/{scenario_name}_frames"
        if os.path.exists(scenario_frame_dir):
            shutil.rmtree(scenario_frame_dir)
        os.makedirs(scenario_frame_dir)
        
        # Update frame directory
        original_frame_dir = config.FRAME_DIRECTORY
        config.FRAME_DIRECTORY = scenario_frame_dir
        
        try:
            # Run simulation
            sim = DefenseSimulation(visualization_enabled=True)
            result = sim.run()
            
            print(f"📊 Result: {result}")
            print(f"📁 Frames saved to: {scenario_frame_dir}")
            
            # Create GIF from frames
            self.create_gif_from_frames(scenario_frame_dir, f"{self.scenarios_dir}/{scenario_name}.gif")
            
            return result
            
        except Exception as e:
            print(f"❌ Error in scenario {scenario_name}: {e}")
            return None
        finally:
            # Restore frame directory
            config.FRAME_DIRECTORY = original_frame_dir
    
    def generate_extreme_scenarios(self):
        """Generate extreme demonstration scenarios"""
        self.backup_original_config()
        
        scenarios = [
            {
                "name": "fast_intruder_breakthrough",
                "config": {
                    "NUM_DEFENDERS": 2,
                    "DEFENDER_SPEED": 2.0,
                    "INTRUDER_SPEED": 6.0,  # Very fast intruder
                    "SAVE_FRAMES": True,
                    "VISUALIZATION_ENABLED": True,
                    "MAX_SIMULATION_TIME": 15.0,
                    "DEFENDER_WIN_DISTANCE": 0.8  # Harder to catch
                },
                "defender_positions": [
                    (15.0, 15.0),  # NE, far from optimal
                    (-10.0, -10.0)  # SW, far from optimal
                ],
                "intruder_pos": (20.0, 5.0),  # From E, avoiding defenders
                "description": "Fast intruder breakthrough with poor defender positioning"
            },
            {
                "name": "single_defender_overwhelmed", 
                "config": {
                    "NUM_DEFENDERS": 1,
                    "DEFENDER_SPEED": 3.0,
                    "INTRUDER_SPEED": 4.5,
                    "SAVE_FRAMES": True,
                    "VISUALIZATION_ENABLED": True,
                    "MAX_SIMULATION_TIME": 12.0
                },
                "defender_positions": [
                    (8.0, 8.0)  # Single defender, suboptimal position
                ],
                "intruder_pos": (18.0, -12.0),  # Approach from opposite side
                "description": "Single defender overwhelmed by fast intruder"
            },
            {
                "name": "smart_pathfinding_around_defenders",
                "config": {
                    "NUM_DEFENDERS": 3,
                    "DEFENDER_SPEED": 2.8,
                    "INTRUDER_SPEED": 5.0,  # Much faster
                    "SAVE_FRAMES": True,
                    "VISUALIZATION_ENABLED": True,
                    "MAX_SIMULATION_TIME": 18.0
                },
                "defender_positions": [
                    (10.0, 0.0),   # E of goal
                    (0.0, 10.0),   # N of goal  
                    (-10.0, 0.0)   # W of goal
                ],
                "intruder_pos": (22.0, 22.0),  # Far NE diagonal
                "description": "Smart pathfinding navigating around defensive formation"
            },
            {
                "name": "close_call_near_miss",
                "config": {
                    "NUM_DEFENDERS": 2,
                    "DEFENDER_SPEED": 3.8,
                    "INTRUDER_SPEED": 4.0,  # Slight speed advantage
                    "SAVE_FRAMES": True,
                    "VISUALIZATION_ENABLED": True,
                    "MAX_SIMULATION_TIME": 20.0,
                    "DEFENDER_WIN_DISTANCE": 0.3  # Very close catch required
                },
                "defender_positions": [
                    (12.0, 8.0),   # NE
                    (8.0, -12.0)   # SE
                ],
                "intruder_pos": (25.0, 2.0),  # From E
                "description": "Close call with near-miss interception attempts"
            },
            {
                "name": "actual_stalemate",
                "config": {
                    "NUM_DEFENDERS": 3,
                    "DEFENDER_SPEED": 3.0,
                    "INTRUDER_SPEED": 4.0,
                    "SAVE_FRAMES": True,
                    "VISUALIZATION_ENABLED": True,
                    "MAX_SIMULATION_TIME": 12.0,
                    "STALEMATE_TIME": 10.0  # Force stalemate
                },
                "defender_positions": [
                    (20.0, 10.0),   # Far NE
                    (20.0, -10.0),  # Far SE
                    (-25.0, 0.0)    # Very far W
                ],
                "intruder_pos": (28.0, 0.0),  # Far E, direct approach
                "description": "True stalemate with distant defenders"
            }
        ]
        
        results = {}
        
        for scenario in scenarios:
            print(f"\n🎯 {scenario['description']}")
            result = self.run_scenario(
                scenario["name"], 
                scenario["config"], 
                scenario["defender_positions"],
                scenario["intruder_pos"]
            )
            results[scenario["name"]] = result
        
        self.restore_original_config()
        
        # Print summary
        print("\n" + "=" * 80)
        print("🎬 EXTREME SCENARIO GENERATION COMPLETE")
        print("=" * 80)
        
        for scenario_name, result in results.items():
            if result:
                print(f"✅ {scenario_name}: {result.winner} wins ({result.time_elapsed:.1f}s)")
            else:
                print(f"❌ {scenario_name}: Failed to complete")
        
        print(f"\n📁 All GIFs saved to: {self.scenarios_dir}/")

def main():
    """Main entry point"""
    print("🎬 Extreme Multi-Agent Defense Scenarios")
    print("=" * 80)
    print("Creating scenarios designed for intruder breakthroughs...")
    
    generator = ExtremeScenarioGenerator()
    generator.generate_extreme_scenarios()

if __name__ == "__main__":
    main()