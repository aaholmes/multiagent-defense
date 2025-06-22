use pyo3::prelude::*;

mod structs;
mod geometry;
mod controller;
mod pathfinding;

use structs::*;
use geometry::*;
use controller::*;
use pathfinding::*;

/// Python module exports
#[pymodule]
fn interception_core(_py: Python, m: &PyModule) -> PyResult<()> {
    // Export data structures
    m.add_class::<Point>()?;
    m.add_class::<Circle>()?;
    m.add_class::<AgentState>()?;
    m.add_class::<WorldState>()?;
    m.add_class::<SimConfig>()?;
    m.add_class::<ControlState>()?;
    m.add_class::<GridConfig>()?;
    m.add_class::<GridNode>()?;
    m.add_class::<PathResult>()?;
    
    // Export geometry functions
    m.add_function(wrap_pyfunction!(py_calculate_apollonian_circle, m)?)?;
    m.add_function(wrap_pyfunction!(py_calculate_arc_intersection_length, m)?)?;
    m.add_function(wrap_pyfunction!(py_circle_intersection_points, m)?)?;
    
    // Export controller functions
    m.add_function(wrap_pyfunction!(py_get_defender_velocity_commands, m)?)?;
    m.add_function(wrap_pyfunction!(py_get_defender_velocity_commands_with_states, m)?)?;
    m.add_function(wrap_pyfunction!(py_calculate_line_segment_circle_intersection, m)?)?;
    
    // Export pathfinding functions
    m.add_function(wrap_pyfunction!(py_calculate_intruder_next_position, m)?)?;
    m.add_function(wrap_pyfunction!(py_calculate_intruder_full_path, m)?)?;
    m.add_function(wrap_pyfunction!(py_generate_threat_map, m)?)?;
    m.add_function(wrap_pyfunction!(py_to_grid_coords, m)?)?;
    m.add_function(wrap_pyfunction!(py_to_world_coords, m)?)?;
    
    Ok(())
}

/// Python wrapper for calculate_apollonian_circle
#[pyfunction]
fn py_calculate_apollonian_circle(
    defender_pos: &Point,
    intruder_pos: &Point,
    speed_ratio: f64,
) -> Circle {
    calculate_apollonian_circle(defender_pos, intruder_pos, speed_ratio)
}

/// Python wrapper for calculate_arc_intersection_length
#[pyfunction]
fn py_calculate_arc_intersection_length(circle1: &Circle, circle2: &Circle) -> f64 {
    calculate_arc_intersection_length(circle1, circle2)
}

/// Python wrapper for circle_intersection_points
#[pyfunction]
fn py_circle_intersection_points(circle1: &Circle, circle2: &Circle) -> Vec<Point> {
    circle_intersection_points(circle1, circle2)
}

/// Python wrapper for get_defender_velocity_commands (legacy)
#[pyfunction]
fn py_get_defender_velocity_commands(
    world_state: &WorldState,
    config: &SimConfig,
) -> Vec<Point> {
    get_defender_velocity_commands(world_state, config)
}

/// Python wrapper for get_defender_velocity_commands_with_states
/// Returns both velocities and updated states
#[pyfunction]
fn py_get_defender_velocity_commands_with_states(
    world_state: &WorldState,
    defender_states: Vec<ControlState>,
    config: &SimConfig,
) -> (Vec<Point>, Vec<ControlState>) {
    let mut states = defender_states;
    let velocities = get_defender_velocity_commands_with_states(world_state, &mut states, config);
    (velocities, states)
}

/// Python wrapper for calculate_line_segment_circle_intersection
#[pyfunction]
fn py_calculate_line_segment_circle_intersection(
    p1: &Point,
    p2: &Point,
    circle: &Circle,
) -> Option<Point> {
    calculate_line_segment_circle_intersection(p1, p2, circle)
}

/// Python wrapper for calculate_intruder_next_position
#[pyfunction]
fn py_calculate_intruder_next_position(
    world_state: &WorldState,
    grid_config: &GridConfig,
    sim_config: &SimConfig,
) -> Option<Point> {
    calculate_intruder_next_position(world_state, grid_config, sim_config)
}

/// Python wrapper for calculate_intruder_full_path
#[pyfunction]
fn py_calculate_intruder_full_path(
    world_state: &WorldState,
    grid_config: &GridConfig,
    sim_config: &SimConfig,
) -> PathResult {
    calculate_intruder_full_path(world_state, grid_config, sim_config)
}

/// Python wrapper for generate_threat_map
#[pyfunction]
fn py_generate_threat_map(
    world_state: &WorldState,
    grid_config: &GridConfig,
    sim_config: &SimConfig,
) -> Vec<Vec<f64>> {
    generate_threat_map(world_state, grid_config, sim_config)
}

/// Python wrapper for to_grid_coords
#[pyfunction]
fn py_to_grid_coords(world_pos: &Point, config: &GridConfig) -> Option<GridNode> {
    to_grid_coords(world_pos, config)
}

/// Python wrapper for to_world_coords
#[pyfunction]
fn py_to_world_coords(node: &GridNode, config: &GridConfig) -> Point {
    to_world_coords(node, config)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_integration_basic_scenario() {
        // Create a basic test scenario
        let defender = AgentState::new(
            Point::new(-3.0, 0.0),
            Point::new(0.0, 0.0),
        );
        let intruder = AgentState::new(
            Point::new(10.0, 0.0),
            Point::new(-1.0, 0.0),
        );
        let protected_zone = Circle::new(Point::new(0.0, 0.0), 2.0);
        
        let world_state = WorldState::new(
            vec![defender],
            intruder,
            protected_zone,
        );
        
        let config = SimConfig::new(
            0.1,   // learning_rate
            2.0,   // defender_speed
            4.0,   // intruder_speed
            1.0,   // w_repel
            0.1,   // epsilon
        );
        
        let velocities = get_defender_velocity_commands(&world_state, &config);
        
        assert_eq!(velocities.len(), 1);
        assert!(velocities[0].magnitude() <= config.defender_speed + 1e-10);
    }

    #[test]
    fn test_apollonian_circle_integration() {
        let defender = Point::new(0.0, 0.0);
        let intruder = Point::new(4.0, 0.0);
        let speed_ratio = 0.5;
        
        let circle = calculate_apollonian_circle(&defender, &intruder, speed_ratio);
        
        // Verify it passes through the expected points
        let p1 = Point::new(4.0/3.0, 0.0); // 1/3 toward intruder
        let p2 = Point::new(-4.0, 0.0);    // d behind defender
        
        let dist1 = circle.center.distance_to(&p1);
        let dist2 = circle.center.distance_to(&p2);
        
        assert!((dist1 - circle.radius).abs() < 1e-10);
        assert!((dist2 - circle.radius).abs() < 1e-10);
    }
}