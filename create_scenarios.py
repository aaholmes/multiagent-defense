#!/usr/bin/env python3
"""
Create multiple simulation scenarios to demonstrate different strategies and outcomes.

This script generates various GIF demonstrations showing:
1. Successful defense with intercept strategy
2. Intruder breakthrough with smart pathfinding
3. Engage state cooperative defense  
4. Travel state positioning
5. Stalemate scenarios
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

class ScenarioGenerator:
    """Generates different simulation scenarios with varying parameters"""
    
    def __init__(self):
        self.base_frame_dir = "animation_frames"
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
            'VISUALIZATION_ENABLED': config.VISUALIZATION_ENABLED
        }
    
    def restore_original_config(self):
        """Restore original config values"""
        for key, value in self.original_config.items():
            setattr(config, key, value)
    
    def set_scenario_config(self, scenario_config):
        """Apply scenario-specific configuration"""
        for key, value in scenario_config.items():
            setattr(config, key, value)
    
    def get_initial_positions(self, scenario_type):
        """Get scenario-specific initial positions"""
        if scenario_type == "intercept_success":
            # Position defenders to enable intercept strategy
            defender_positions = [
                (12.0, 6.0),   # NE defender
                (8.0, -8.0),   # SE defender  
                (-10.0, 2.0)   # W defender
            ]
            intruder_pos = (20.0, 15.0)  # From NE
            
        elif scenario_type == "intruder_breakthrough":
            # Fewer/slower defenders, faster intruder
            defender_positions = [
                (15.0, 10.0),  # Far NE
                (-8.0, -8.0)   # SW only
            ]
            intruder_pos = (18.0, -12.0)  # From SE, avoiding defenders
            
        elif scenario_type == "engage_cooperative":
            # Position defenders for engage state (no direct intercept)
            defender_positions = [
                (8.0, 0.0),    # E of goal
                (0.0, 8.0),    # N of goal
                (-6.0, -6.0)   # SW of goal
            ]
            intruder_pos = (15.0, 15.0)  # From NE diagonal
            
        elif scenario_type == "travel_positioning":
            # Defenders far from goal, need to travel first
            defender_positions = [
                (20.0, 5.0),   # Far E
                (5.0, -20.0),  # Far S
                (-25.0, 0.0)   # Far W
            ]
            intruder_pos = (12.0, 20.0)  # From N
            
        elif scenario_type == "stalemate":
            # Balanced scenario likely to result in stalemate
            defender_positions = [
                (10.0, 8.0),
                (10.0, -8.0),
                (-12.0, 0.0)
            ]
            intruder_pos = (25.0, 0.0)  # Direct approach from E
            
        return defender_positions, intruder_pos
    
    def override_initial_positions(self, defender_positions, intruder_pos):
        """Override config functions to return specific positions"""
        config.get_initial_defender_positions = lambda: defender_positions
        config.get_initial_intruder_position = lambda: intruder_pos
    
    def run_scenario(self, scenario_name, scenario_config, scenario_type):
        """Run a single scenario and save frames"""
        print(f"\n🎬 Creating Scenario: {scenario_name}")
        print("=" * 60)
        
        # Set up scenario
        self.set_scenario_config(scenario_config)
        defender_positions, intruder_pos = self.get_initial_positions(scenario_type)
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
    
    def create_gif_from_frames(self, frame_dir, output_gif):
        """Create GIF from frame directory"""
        try:
            # Use the existing create_gif script
            cmd = [
                sys.executable, "simulation/create_gif.py", 
                frame_dir, output_gif, "0.1"  # 0.1 second per frame
            ]
            subprocess.run(cmd, check=True)
            print(f"✅ GIF created: {output_gif}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create GIF: {e}")
        except FileNotFoundError:
            print("❌ create_gif.py not found, creating manual GIF...")
            self.create_manual_gif(frame_dir, output_gif)
    
    def create_manual_gif(self, frame_dir, output_gif):
        """Create GIF manually if create_gif.py not available"""
        try:
            import matplotlib.pyplot as plt
            from PIL import Image
            import glob
            
            # Get all frame files
            frame_files = sorted(glob.glob(os.path.join(frame_dir, "frame_*.png")))
            
            if not frame_files:
                print("❌ No frame files found")
                return
            
            # Load images
            images = []
            for frame_file in frame_files:
                img = Image.open(frame_file)
                images.append(img)
            
            # Save as GIF
            images[0].save(
                output_gif,
                save_all=True,
                append_images=images[1:],
                duration=100,  # 100ms per frame
                loop=0
            )
            print(f"✅ Manual GIF created: {output_gif}")
            
        except Exception as e:
            print(f"❌ Manual GIF creation failed: {e}")
    
    def generate_all_scenarios(self):
        """Generate all demonstration scenarios"""
        self.backup_original_config()
        
        scenarios = [
            {
                "name": "scenario1_intercept_success",
                "type": "intercept_success", 
                "config": {
                    "NUM_DEFENDERS": 3,
                    "DEFENDER_SPEED": 3.5,
                    "INTRUDER_SPEED": 4.0,
                    "SAVE_FRAMES": True,
                    "VISUALIZATION_ENABLED": True,
                    "MAX_SIMULATION_TIME": 15.0
                },
                "description": "Successful defense using intercept strategy"
            },
            {
                "name": "scenario2_intruder_breakthrough", 
                "type": "intruder_breakthrough",
                "config": {
                    "NUM_DEFENDERS": 2,
                    "DEFENDER_SPEED": 2.5,
                    "INTRUDER_SPEED": 4.5,
                    "SAVE_FRAMES": True,
                    "VISUALIZATION_ENABLED": True,
                    "MAX_SIMULATION_TIME": 20.0
                },
                "description": "Intruder breakthrough with smart pathfinding"
            },
            {
                "name": "scenario3_engage_cooperative",
                "type": "engage_cooperative",
                "config": {
                    "NUM_DEFENDERS": 3,
                    "DEFENDER_SPEED": 3.0,
                    "INTRUDER_SPEED": 3.8,
                    "SAVE_FRAMES": True,
                    "VISUALIZATION_ENABLED": True,
                    "MAX_SIMULATION_TIME": 18.0
                },
                "description": "Cooperative defense using engage state"
            },
            {
                "name": "scenario4_travel_positioning",
                "type": "travel_positioning", 
                "config": {
                    "NUM_DEFENDERS": 3,
                    "DEFENDER_SPEED": 4.0,
                    "INTRUDER_SPEED": 3.5,
                    "SAVE_FRAMES": True,
                    "VISUALIZATION_ENABLED": True,
                    "MAX_SIMULATION_TIME": 25.0
                },
                "description": "Defenders repositioning using travel state"
            },
            {
                "name": "scenario5_stalemate",
                "type": "stalemate",
                "config": {
                    "NUM_DEFENDERS": 3,
                    "DEFENDER_SPEED": 3.0,
                    "INTRUDER_SPEED": 4.0,
                    "SAVE_FRAMES": True,
                    "VISUALIZATION_ENABLED": True,
                    "MAX_SIMULATION_TIME": 20.0,
                    "STALEMATE_TIME": 15.0
                },
                "description": "Balanced scenario resulting in stalemate"
            }
        ]
        
        results = {}
        
        for scenario in scenarios:
            print(f"\n🎯 {scenario['description']}")
            result = self.run_scenario(
                scenario["name"], 
                scenario["config"], 
                scenario["type"]
            )
            results[scenario["name"]] = result
        
        self.restore_original_config()
        
        # Print summary
        print("\n" + "=" * 80)
        print("🎬 SCENARIO GENERATION COMPLETE")
        print("=" * 80)
        
        for scenario_name, result in results.items():
            if result:
                print(f"✅ {scenario_name}: {result.winner} wins ({result.time_elapsed:.1f}s)")
            else:
                print(f"❌ {scenario_name}: Failed to complete")
        
        print(f"\n📁 All GIFs saved to: {self.scenarios_dir}/")
        print("📋 Available scenarios:")
        for scenario in scenarios:
            print(f"   - {scenario['name']}.gif: {scenario['description']}")

def main():
    """Main entry point"""
    print("🎬 Multi-Agent Defense Scenario Generator")
    print("=" * 80)
    print("Creating multiple demonstration scenarios...")
    
    generator = ScenarioGenerator()
    generator.generate_all_scenarios()

if __name__ == "__main__":
    main()