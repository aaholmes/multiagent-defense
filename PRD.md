# Project: Decentralized Dynamic Interception

Goal: Implement a multi-robot system where N defenders (speed s_d) prevent a single intruder (speed s_is_d) from reaching a circular protected zone. The solution must be decentralized and implemented as a Rust/Python hybrid project.

System Architecture: Hybrid Rust/Python Model

Rust Core Library (interception_core): A compiled library containing all performance-critical state management, geometric calculations, and control logic.
Python Simulation Layer: A Python package that imports the Rust library to initialize, run, and visualize simulations.
1. Rust Core Library (interception_core)
Crate: interception_core
Dependencies: pyo3 (for Python bindings), numpy (for sharing data efficiently).

Data Structures (src/structs.rs)
Rust

// Exposed to Python via PyO3
#[pyclass]
#[derive(Clone)]
pub struct Point { x: f64, y: f64 }

#[pyclass]
#[derive(Clone)]
pub struct AgentState { pub position: Point, pub velocity: Point }

#[pyclass]
#[derive(Clone)]
pub struct Circle { pub center: Point, pub radius: f64 }

#[pyclass]
#[derive(Clone)]
pub struct WorldState {
    pub defenders: Vec<AgentState>,
    pub intruder: AgentState,
    pub protected_zone: Circle,
}

// Internal (not exposed to Python)
pub struct Arc { pub start_angle: f64, pub end_angle: f64 }
pub enum ControlState { Travel, Engage }
Core Logic (src/lib.rs)
The main function exposed to Python will be get_defender_velocity_commands, which orchestrates the calls below.

determine_control_state(defender_circle: &Circle, protected_zone: &Circle) -> ControlState

Checks if the defender's Apollonian circle intersects the protected zone.
Returns ControlState::Engage if they intersect, otherwise ControlState::Travel.
calculate_loss_engage(world_state: &WorldState, defender_index: usize) -> f64

Calculates all coverage arcs g_i and overlap arcs h_ij.
Returns Loss = w_repel * sum(max(0, h_ij - ε)) - g_i.
calculate_loss_travel(defender_state: &AgentState, protected_zone: &Circle) -> f64

Calculates the squared distance from the defender to the perimeter of the protected zone.
Returns Loss = w_travel * distance^2.
calculate_gradient(loss_fn: F, world_state: &WorldState, defender_index: usize) -> Point

A generic function that takes a loss function (F) as input.
Numerically calculates the gradient of the given loss function with respect to the defender's position using finite differences.
Returns the 2D gradient vector.
get_defender_velocity_commands(world_state: &WorldState, config: &SimConfig) -> Vec<Point>

This is the main entry point called from Python.
It iterates through each defender i: a. Calculates the defender's Apollonian circle. b. Calls determine_control_state to get the current state (Travel or Engage). c. Based on the state, selects the appropriate loss function (calculate_loss_engage or calculate_loss_travel). d. Calls calculate_gradient with the selected loss function to get the gradient grad. e. Calculates the final velocity command: vel = -config.learning_rate * grad. f. Clamps the velocity to the maximum defender speed.
Returns a Vec<Point> of velocity commands for all defenders.
Python Bindings (using #[pymodule])
Expose the Point, AgentState, Circle, and WorldState structs.
Expose the main function get_defender_velocity_commands.
2. Python Simulation Layer
Dependencies: matplotlib, numpy, interception_core (the compiled Rust wheel).

Structure:

simulation/run_simulation.py: The main script for running a simulation.
simulation/config.py: Defines simulation parameters (number of agents, speeds, learning rate, world size).
simulation/visualizer.py: A class Visualizer that uses Matplotlib to draw the world state.
Main Loop Logic in run_simulation.py
Initialization:

Load parameters from config.py.
Create an initial WorldState object (e.g., defenders in a semi-circle, intruder at the edge).
Instantiate the Visualizer.
Simulation Loop (runs for T timesteps):
a. Call the single, efficient Rust core function to get all velocity commands at once:
velocity_commands = interception_core.get_defender_velocity_commands(current_world_state, config)
b. Update defender states in Python:
for i, vel in enumerate(velocity_commands): defenders[i].position += vel * dt
c. Update Intruder State: Move intruder along its path.
d. Check for End Conditions (intruder reached goal, etc.).
e. Visualize: Call the Visualizer to draw the new WorldState, including the semi-transparent Apollonian circles for each defender.
f. Repeat.
