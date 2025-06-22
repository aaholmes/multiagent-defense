# Project: Decentralized Dynamic Interception

Goal: Implement a multi-robot system where N defenders prevent a smart intruder from reaching a protected zone. This document includes the design for the defenders' three-state interception controller and the intruder's A* planning algorithm.

System Architecture: Hybrid Rust/Python Model

Rust Core Library (interception_core): A compiled library containing all performance-critical state management, geometric calculations, and defender control logic.
Python Simulation Layer: A Python package that imports the Rust library to initialize, run, and visualize simulations, and which will contain the new Intruder AI logic.
1. The Defender Three-State Control FSM (Rust Core)
Each defender's controller operates as a Finite State Machine with three possible states.

ControlState Enum:

Travel: Robot is too far; moving towards the objective.
Engage: Robot is in range; cooperating to form the defensive barrier.
Intercept: Robot has a guaranteed capture; breaking formation to intercept.
State Transitions:

Travel -> Engage: When the robot's Apollonian circle first intersects the protected_zone.
Engage -> Intercept: When the intruder's path intersects the robot's Apollonian circle.
Intercept is a terminal state representing full commitment.
(The detailed implementation of the defender logic remains as specified in our previous discussion).

2. Smart Intruder AI (A* Planner)
The "smart" intruder will not move in a straight line. Instead, it will use the A* search algorithm to find the safest path to the goal at every time step, reacting to the defenders' movements. This logic will reside in the Python Simulation Layer.

2.1. Grid and Discretization
To use A*, the continuous world must be represented as a discrete grid.

Lattice Type: Square Lattice 
Connectivity: 4-way (von Neumann neighborhood) 
Grid Size: A defined resolution, e.g., 100x100 cells.
Coordinate Mapping: Functions will be needed to map continuous world coordinates (x, y) to discrete grid coordinates (row, col) and back.
to_grid(world_pos) -> (row, col)
to_world(row, col) -> world_pos
2.2. Dynamic Cost Calculation ("Threat Map")
At the beginning of each simulation step, a new cost map for the grid is generated.

Initialize Costs: Create a 2D array representing the grid, with all cells initialized to a base traversal cost of 1.
Calculate Threat:
For each defender in the world_state: a. Calculate its current Apollonian circle. b. Iterate through every cell (row, col) in the grid. c. Convert the cell's (row, col) to its world position (x, y). d. If the point (x, y) is inside the defender's Apollonian circle, add a large THREAT_PENALTY (e.g., 1000.0) to the cost of that cell in the cost map.
2.3. A Search Implementation*
A standard A* algorithm implementation will be used.

Heuristic Function: The Manhattan distance is the appropriate heuristic for a 4-way connected grid.
h(a, b) = |a.row - b.row| + |a.col - b.col|
Inputs: start_node, goal_node, and the dynamic cost_map generated in the previous step.
Output: A list of nodes representing the cheapest path from start to goal.
2.4. Execution and Replanning Loop
The intruder's update method in Python will perform the following logic at each frame:

Generate the new cost_map based on the current positions of all defenders (as per section 2.2).
Get the intruder's current grid position start_node = to_grid(intruder.position).
Get the goal's grid position goal_node = to_grid(protected_zone.center).
Run the A* search on the cost_map from start_node to goal_node to get the path.
If a path is found: a. Get the next node in the path: next_node = path[1]. b. Convert this node back to a continuous world position: target_pos = to_world(next_node.row, next_node.col). c. Calculate the velocity vector pointing from the intruder's current position to target_pos. d. Set the intruder's velocity to this vector, clamped to its maximum speed.
If no path is found (the goal is completely surrounded), the intruder can stop or default to moving towards the closest defender to create an opening.
This entire process repeats every frame, allowing the intruder to react dynamically to the defenders' changing strategy.

3. Rust Core Library (interception_core) Modifications
New Geometric Utility (src/geometry.rs)
We need a robust function to detect the intersection between the intruder's path and the Apollonian circle.

calculate_line_segment_circle_intersection(p1: Point, p2: Point, circle: &Circle) -> Option<Point>
This function takes the start and end points of a line segment (the intruder's path) and a circle (the Apollonian circle).
It should solve for the intersection points mathematically.
Crucially, it must check if the intersection points lie on the segment between p1 and p2.
It returns the closest valid intersection point to the intruder (p1) if one exists, otherwise None. This point becomes the interception_point.
Updated Core Logic (src/lib.rs)
The main get_defender_velocity_commands function must be updated to implement the FSM. This requires tracking the current state for each defender.

Rust

// A simplified sketch of the new main loop logic
pub fn get_defender_velocity_commands(
    world_state: &WorldState,
    defender_states: &mut Vec<ControlState>, // Pass states in as mutable
    config: &SimConfig
) -> Vec<Point> {

    let mut velocity_commands = Vec::new();

    // 1. Calculate the intruder's path
    let intruder_path_start = world_state.intruder.position;
    let intruder_path_end = world_state.protected_zone.center;

    for i in 0..world_state.defenders.len() {
        let defender = &world_state.defenders[i];
        let apollon_circle = get_apollonian_circle(...);

        // 2. FSM State Transition Logic
        match defender_states[i] {
            ControlState::Travel => {
                if intersects(&apollon_circle, &world_state.protected_zone) {
                    defender_states[i] = ControlState::Engage;
                }
            },
            ControlState::Engage => {
                if let Some(_) = calculate_line_segment_circle_intersection(
                    intruder_path_start,
                    intruder_path_end,
                    &apollon_circle
                ) {
                    defender_states[i] = ControlState::Intercept;
                }
            },
            ControlState::Intercept => {
                // This is a terminal state, no transitions out.
            }
        }

        // 3. Action Logic (Calculate velocity based on current state)
        let vel_command = match defender_states[i] {
            ControlState::Travel => {
                // Calculate gradient of Loss_Travel and return velocity
                // ... (existing logic)
            },
            ControlState::Engage => {
                // Calculate gradient of Loss_Engage and return velocity
                // ... (existing logic)
            },
            ControlState::Intercept => {
                // New Interception Logic!
                // Recalculate the interception point this frame for accuracy.
                let target_point = calculate_line_segment_circle_intersection(...).unwrap();
                let direction_vector = target_point - defender.position;
                // Command robot to move at max speed towards the target.
                normalize(direction_vector) * config.defender_max_speed
            }
        };
        velocity_commands.push(vel_command);
    }

    velocity_commands
}

4. Python Simulation Layer Modifications
The Python layer needs a minor change to track and visualize the state of each defender.

run_simulation.py:

Initialize and maintain a list of defender states: defender_states = [interception_core.ControlState.Travel] * num_defenders.
Pass this list to the get_defender_velocity_commands function in each step of the simulation loop.
visualizer.py:

When drawing each defender, use its current state to determine its color. This is critical for debugging and for making the demo visually clear.
Travel state: GREY (not yet a factor)
Engage state: BLUE (cooperatively defending)
Intercept state: RED (committed to attack)
