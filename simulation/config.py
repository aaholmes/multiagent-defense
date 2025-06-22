"""
Configuration parameters for the multi-agent defense simulation.
"""

# Simulation Parameters
TIMESTEP_DURATION = 0.05  # seconds per simulation step
MAX_SIMULATION_TIME = 30.0  # maximum simulation time in seconds
MAX_TIMESTEPS = int(MAX_SIMULATION_TIME / TIMESTEP_DURATION)

# World Parameters
WORLD_SIZE = 30.0  # world extends from -WORLD_SIZE to +WORLD_SIZE
PROTECTED_ZONE_CENTER = (0.0, 0.0)  # center of protected zone
PROTECTED_ZONE_RADIUS = 2.0  # radius of protected zone

# Agent Parameters
NUM_DEFENDERS = 3  # number of defender robots
DEFENDER_SPEED = 3.0  # maximum speed of defenders (balanced for challenging but winnable defense)
INTRUDER_SPEED = 4.0  # speed of intruder (faster than defenders)

# Control Parameters
LEARNING_RATE = 0.8  # learning rate for gradient descent
W_REPEL = 2.0  # weight for overlap penalty in loss function
EPSILON = 0.3  # overlap tolerance threshold

# Initial Positions  
DEFENDER_INITIAL_RADIUS = 6.0  # average distance of defenders from center (for reference)
INTRUDER_INITIAL_DISTANCE = 25.0  # initial distance of intruder from center
INTRUDER_INITIAL_ANGLE = 0.785398  # initial angle of intruder (45 degrees northeast for better lattice demonstration)

# Visualization Parameters
VISUALIZATION_ENABLED = True
SAVE_FRAMES = True  # set to True to save individual frames for GIF creation
FRAME_DIRECTORY = "animation_frames"
SHOW_APOLLONIAN_CIRCLES = True
SHOW_VELOCITY_VECTORS = True
APOLLONIAN_ALPHA = 0.15  # transparency of Apollonian circles

# End Conditions
INTRUDER_WIN_DISTANCE = PROTECTED_ZONE_RADIUS * 0.9  # intruder wins if closer than this
DEFENDER_WIN_DISTANCE = 0.5  # defender wins if within this distance of intruder
STALEMATE_TIME = 25.0  # declare stalemate after this many seconds

# Colors for visualization
COLORS = {
    'protected_zone': 'green',
    'intruder': 'red', 
    'defenders': ['blue', 'purple', 'orange', 'brown', 'pink'],
    'apollonian': ['blue', 'blue', 'blue', 'blue', 'blue'],
    'velocity': 'black'
}

def get_simulation_config():
    """Create a SimConfig object for the Rust library"""
    try:
        import interception_core as ic
        return ic.SimConfig(
            learning_rate=LEARNING_RATE,
            defender_speed=DEFENDER_SPEED,
            intruder_speed=INTRUDER_SPEED,
            w_repel=W_REPEL,
            epsilon=EPSILON
        )
    except ImportError:
        print("Warning: interception_core not available, returning None")
        return None

def get_initial_defender_positions():
    """Generate defender positions around different sides of the goal circle"""
    import math
    import random
    positions = []
    
    # Set seed for reproducible positions
    random.seed(42)
    
    # Position defenders NNE, SSE, and West of goal (intruder coming from East)
    # This creates a more challenging and realistic scenario
    base_angles = [
        math.pi * 1/6,    # 30 degrees (NNE - North-North-East)
        math.pi * 11/6,   # 330 degrees (SSE - South-South-East) 
        math.pi          # 180 degrees (West)
    ]
    
    for i in range(NUM_DEFENDERS):
        if i < len(base_angles):
            angle = base_angles[i]
        else:
            # If more than 3 defenders, distribute remaining randomly
            angle = random.uniform(0, 2 * math.pi)
        
        # Distance chosen so Apollonian circles partially overlap but don't fully cover goal
        distance = random.uniform(14.0, 18.0)  # Further distance for partial coverage only
        
        x = distance * math.cos(angle)
        y = distance * math.sin(angle)
        positions.append((x, y))
    
    return positions

def get_initial_intruder_position():
    """Generate initial position for intruder"""
    import math
    angle = INTRUDER_INITIAL_ANGLE
    x = INTRUDER_INITIAL_DISTANCE * math.cos(angle)
    y = INTRUDER_INITIAL_DISTANCE * math.sin(angle)
    return (x, y)

def print_config():
    """Print current configuration for debugging"""
    print("=== Simulation Configuration ===")
    print(f"Timestep: {TIMESTEP_DURATION}s, Max time: {MAX_SIMULATION_TIME}s")
    print(f"World size: ±{WORLD_SIZE}")
    print(f"Protected zone: center{PROTECTED_ZONE_CENTER}, radius={PROTECTED_ZONE_RADIUS}")
    print(f"Defenders: {NUM_DEFENDERS} robots, speed={DEFENDER_SPEED}")
    print(f"Intruder: speed={INTRUDER_SPEED}")
    print(f"Control: lr={LEARNING_RATE}, w_repel={W_REPEL}, ε={EPSILON}")
    
    defender_positions = get_initial_defender_positions()
    intruder_position = get_initial_intruder_position()
    print(f"Initial defender positions: {defender_positions}")
    print(f"Initial intruder position: {intruder_position}")
    print("=" * 35)

if __name__ == "__main__":
    print_config()