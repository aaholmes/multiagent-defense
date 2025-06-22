# Project: Decentralized Dynamic Interception

Goal: Evolve the controller to allow defenders to break formation and commit to a direct interception of the intruder once a capture is guaranteed.

System Architecture: The existing Hybrid Rust/Python architecture remains unchanged. The following modifications apply to the Rust Core Library (interception_core).

1. The Three-State Control FSM
Each defender's controller will now operate as a Finite State Machine with three possible states. The ControlState enum in Rust should be updated:

Rust

// src/structs.rs
pub enum ControlState {
    Travel, // Robot is too far to help; moving towards the objective.
    Engage, // Robot is in range; cooperating to form the defensive barrier.
    Intercept, // Robot has a guaranteed capture; breaking formation to intercept.
}
State Transitions:
Here is the logic governing the transitions between states for a single defender:

Travel -> Engage

Trigger: When the robot's Apollonian circle (Apollon_i) first intersects the protected_zone.
Meaning: "I'm close enough to help form the barrier."
Engage -> Intercept

Trigger: When the intruder's intended path (a line segment from its current position to the center of the protected_zone) intersects Apollon_i.
Meaning: "I have a guaranteed capture. Committing now."
Intercept -> Engage (or other states)

For this design, the Intercept state is terminal. Once a robot commits, it will continue to pursue the calculated interception point until a simulation reset. This simplifies the initial implementation and represents a full commitment to the capture.
2. Rust Core Library (interception_core) Modifications
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
3. Python Simulation Layer Modifications
The Python layer needs a minor change to track and visualize the state of each defender.

run_simulation.py:

Initialize and maintain a list of defender states: defender_states = [interception_core.ControlState.Travel] * num_defenders.
Pass this list to the get_defender_velocity_commands function in each step of the simulation loop.
visualizer.py:

When drawing each defender, use its current state to determine its color. This is critical for debugging and for making the demo visually clear.
Travel state: GREY (not yet a factor)
Engage state: BLUE (cooperatively defending)
Intercept state: RED (committed to attack)
