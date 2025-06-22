use pyo3::prelude::*;

mod structs;
mod geometry;
mod controller;

use structs::*;
use geometry::*;
use controller::*;

/// Python module exports
#[pymodule]
fn interception_core(_py: Python, m: &PyModule) -> PyResult<()> {
    // Export data structures
    m.add_class::<Point>()?;
    m.add_class::<Circle>()?;
    m.add_class::<AgentState>()?;
    m.add_class::<WorldState>()?;
    m.add_class::<SimConfig>()?;
    
    // Export geometry functions
    m.add_function(wrap_pyfunction!(py_calculate_apollonian_circle, m)?)?;
    m.add_function(wrap_pyfunction!(py_calculate_arc_intersection_length, m)?)?;
    m.add_function(wrap_pyfunction!(py_circle_intersection_points, m)?)?;
    
    // Export main controller function
    m.add_function(wrap_pyfunction!(py_get_defender_velocity_commands, m)?)?;
    
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

/// Python wrapper for get_defender_velocity_commands
#[pyfunction]
fn py_get_defender_velocity_commands(
    world_state: &WorldState,
    config: &SimConfig,
) -> Vec<Point> {
    get_defender_velocity_commands(world_state, config)
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