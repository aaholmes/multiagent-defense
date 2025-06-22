"""
Configuration parameters for the multi-agent defense simulation.
"""

# Simulation Parameters
TIMESTEP_DURATION = 0.05  # seconds per simulation step
MAX_SIMULATION_TIME = 30.0  # maximum simulation time in seconds
MAX_TIMESTEPS = int(MAX_SIMULATION_TIME / TIMESTEP_DURATION)

# World Parameters
WORLD_SIZE = 20.0  # world extends from -WORLD_SIZE to +WORLD_SIZE
PROTECTED_ZONE_CENTER = (0.0, 0.0)  # center of protected zone
PROTECTED_ZONE_RADIUS = 2.0  # radius of protected zone

# Agent Parameters
NUM_DEFENDERS = 3  # number of defender robots
DEFENDER_SPEED = 2.0  # maximum speed of defenders
INTRUDER_SPEED = 4.0  # speed of intruder (faster than defenders)

# Control Parameters
LEARNING_RATE = 0.8  # learning rate for gradient descent
W_REPEL = 2.0  # weight for overlap penalty in loss function
EPSILON = 0.3  # overlap tolerance threshold

# Initial Positions
DEFENDER_INITIAL_RADIUS = 8.0  # initial distance of defenders from center
INTRUDER_INITIAL_DISTANCE = 15.0  # initial distance of intruder from center
INTRUDER_INITIAL_ANGLE = 0.0  # initial angle of intruder (0 = positive x-axis)

# Visualization Parameters
VISUALIZATION_ENABLED = True
SAVE_FRAMES = False  # set to True to save individual frames
FRAME_DIRECTORY = "simulation_frames"
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
    'apollonian': ['blue', 'purple', 'orange', 'brown', 'pink'],
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
    """Generate initial positions for defenders in a semi-circle"""
    import math
    positions = []
    
    # Place defenders in a semi-circle between intruder and protected zone
    for i in range(NUM_DEFENDERS):
        # Spread defenders from 90 to 270 degrees (left semi-circle)
        angle = math.pi/2 + i * math.pi / (NUM_DEFENDERS - 1) if NUM_DEFENDERS > 1 else math.pi
        x = DEFENDER_INITIAL_RADIUS * math.cos(angle)
        y = DEFENDER_INITIAL_RADIUS * math.sin(angle)
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