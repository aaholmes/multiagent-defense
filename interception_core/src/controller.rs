use crate::structs::{Point, Circle, AgentState, WorldState, SimConfig, ControlState, Arc};
use crate::geometry::{calculate_apollonian_circle, calculate_arc_intersection_length, circle_intersection_points, calculate_line_segment_circle_intersection};
use std::f64::consts::PI;

/// Determine control state based on intended strategy priority
/// 1. Intercept if Apollonian circle intersects intruder's path (highest priority)
/// 2. Engage if Apollonian circle touches goal circle (use loss function)
/// 3. Travel if Apollonian circle doesn't touch goal (move circle towards goal)
pub fn determine_next_control_state(
    current_state: &ControlState,
    apollonian_circle: &Circle,
    protected_zone: &Circle,
    intruder_pos: &Point,
    protected_center: &Point,
) -> ControlState {
    // Intercept is terminal - once committed, stay committed
    if *current_state == ControlState::Intercept {
        return ControlState::Intercept;
    }
    
    // Priority 1: Check for interception opportunity FIRST (highest priority)
    if let Some(_) = calculate_line_segment_circle_intersection(
        intruder_pos,
        protected_center,
        apollonian_circle
    ) {
        return ControlState::Intercept;
    }
    
    // Priority 2: If Apollonian circle intersects protected zone, use cooperative defense
    if apollonian_circle.intersects(protected_zone) {
        ControlState::Engage
    } else {
        // Priority 3: Move Apollonian circle towards goal circle
        ControlState::Travel
    }
}

/// Calculate velocity for Travel state - simple vector from Apollonian center to goal center
pub fn calculate_travel_velocity(
    apollonian_center: &Point,
    goal_center: &Point,
    max_speed: f64,
) -> Point {
    let direction = Point::new(
        goal_center.x - apollonian_center.x,
        goal_center.y - apollonian_center.y,
    );
    
    let normalized = direction.normalize();
    Point::new(
        normalized.x * max_speed,
        normalized.y * max_speed,
    )
}

/// Calculate coverage arc length for a defender's Apollonian circle intersecting protected zone
pub fn calculate_coverage_arc(apollonian_circle: &Circle, protected_zone: &Circle) -> f64 {
    calculate_arc_intersection_length(apollonian_circle, protected_zone)
}

/// Calculate overlap arc length between two defenders' coverage areas
pub fn calculate_overlap_arc(
    defender1_circle: &Circle,
    defender2_circle: &Circle,
    protected_zone: &Circle,
) -> f64 {
    // Find intersection points between the two Apollonian circles
    let intersection_points = circle_intersection_points(defender1_circle, defender2_circle);
    
    if intersection_points.is_empty() {
        return 0.0;
    }
    
    // For each intersection point, check if it's inside the protected zone
    let mut overlap_length = 0.0;
    
    // Simplified calculation: if circles intersect and both intersect protected zone,
    // estimate overlap based on the smaller of the two coverage arcs
    let coverage1 = calculate_coverage_arc(defender1_circle, protected_zone);
    let coverage2 = calculate_coverage_arc(defender2_circle, protected_zone);
    
    if coverage1 > 0.0 && coverage2 > 0.0 {
        // Estimate overlap as fraction of smaller coverage
        let distance_between_centers = defender1_circle.center.distance_to(&defender2_circle.center);
        let combined_radii = defender1_circle.radius + defender2_circle.radius;
        
        if distance_between_centers < combined_radii {
            let overlap_fraction = (combined_radii - distance_between_centers) / combined_radii;
            overlap_length = overlap_fraction * coverage1.min(coverage2);
        }
    }
    
    overlap_length
}

/// Calculate loss function for Engage state
pub fn calculate_loss_engage(
    world_state: &WorldState,
    defender_index: usize,
    config: &SimConfig,
) -> f64 {
    let defender = &world_state.defenders[defender_index];
    
    // Calculate this defender's Apollonian circle
    let apollonian_circle = calculate_apollonian_circle(
        &defender.position,
        &world_state.intruder.position,
        config.speed_ratio(),
    );
    
    // Calculate coverage arc (positive contribution)
    let coverage = calculate_coverage_arc(&apollonian_circle, &world_state.protected_zone);
    
    // Calculate overlap penalties (negative contribution)
    let mut overlap_penalty = 0.0;
    
    for (i, other_defender) in world_state.defenders.iter().enumerate() {
        if i == defender_index {
            continue;
        }
        
        let other_apollonian = calculate_apollonian_circle(
            &other_defender.position,
            &world_state.intruder.position,
            config.speed_ratio(),
        );
        
        let overlap = calculate_overlap_arc(
            &apollonian_circle,
            &other_apollonian,
            &world_state.protected_zone,
        );
        
        if overlap > config.epsilon {
            overlap_penalty += overlap - config.epsilon;
        }
    }
    
    // Loss = w_repel * overlap_penalty - coverage
    // (We want to minimize this, so negative coverage is good)
    config.w_repel * overlap_penalty - coverage
}

/// Calculate numerical gradient using finite differences
pub fn calculate_gradient(
    world_state: &WorldState,
    defender_index: usize,
    config: &SimConfig,
    h: f64,
) -> Point {
    let original_pos = world_state.defenders[defender_index].position.clone();
    
    // Calculate gradient in x direction
    let mut world_state_x_plus = world_state.clone();
    world_state_x_plus.defenders[defender_index].position.x += h;
    let loss_x_plus = calculate_loss_engage(&world_state_x_plus, defender_index, config);
    
    let mut world_state_x_minus = world_state.clone();
    world_state_x_minus.defenders[defender_index].position.x -= h;
    let loss_x_minus = calculate_loss_engage(&world_state_x_minus, defender_index, config);
    
    let grad_x = (loss_x_plus - loss_x_minus) / (2.0 * h);
    
    // Calculate gradient in y direction
    let mut world_state_y_plus = world_state.clone();
    world_state_y_plus.defenders[defender_index].position.y += h;
    let loss_y_plus = calculate_loss_engage(&world_state_y_plus, defender_index, config);
    
    let mut world_state_y_minus = world_state.clone();
    world_state_y_minus.defenders[defender_index].position.y -= h;
    let loss_y_minus = calculate_loss_engage(&world_state_y_minus, defender_index, config);
    
    let grad_y = (loss_y_plus - loss_y_minus) / (2.0 * h);
    
    Point::new(grad_x, grad_y)
}

/// Calculate velocity for Engage state using gradient descent
pub fn calculate_engage_velocity(
    world_state: &WorldState,
    defender_index: usize,
    config: &SimConfig,
) -> Point {
    let h = 1e-4; // Small perturbation for numerical gradient
    let gradient = calculate_gradient(world_state, defender_index, config, h);
    
    // Velocity is negative gradient scaled by learning rate
    let velocity = Point::new(
        -config.learning_rate * gradient.x,
        -config.learning_rate * gradient.y,
    );
    
    // Clamp to maximum speed
    clamp_velocity(&velocity, config.defender_speed)
}

/// Calculate velocity for Intercept state - move directly toward interception point
pub fn calculate_intercept_velocity(
    defender_pos: &Point,
    apollonian_circle: &Circle,
    intruder_pos: &Point,
    protected_center: &Point,
    max_speed: f64,
) -> Point {
    // Recalculate interception point for accuracy
    if let Some(target_point) = calculate_line_segment_circle_intersection(
        intruder_pos,
        protected_center,
        apollonian_circle
    ) {
        // Direction vector from defender to interception point
        let direction = Point::new(
            target_point.x - defender_pos.x,
            target_point.y - defender_pos.y,
        );
        
        // Move at max speed toward the target
        let normalized = direction.normalize();
        Point::new(
            normalized.x * max_speed,
            normalized.y * max_speed,
        )
    } else {
        // Fallback: if no intersection found, stop moving
        Point::new(0.0, 0.0)
    }
}

/// Clamp velocity to maximum speed while preserving direction
pub fn clamp_velocity(velocity: &Point, max_speed: f64) -> Point {
    let current_speed = velocity.magnitude();
    if current_speed <= max_speed {
        velocity.clone()
    } else {
        let normalized = velocity.normalize();
        Point::new(
            normalized.x * max_speed,
            normalized.y * max_speed,
        )
    }
}

/// Main controller function - calculates velocity commands for all defenders
/// Now supports three-state FSM with state persistence
pub fn get_defender_velocity_commands_with_states(
    world_state: &WorldState,
    defender_states: &mut Vec<ControlState>,
    config: &SimConfig,
) -> Vec<Point> {
    let mut velocity_commands = Vec::new();
    
    // Ensure we have enough states for all defenders
    while defender_states.len() < world_state.defenders.len() {
        defender_states.push(ControlState::Travel);
    }
    
    for (i, defender) in world_state.defenders.iter().enumerate() {
        // Calculate Apollonian circle for this defender
        let apollonian_circle = calculate_apollonian_circle(
            &defender.position,
            &world_state.intruder.position,
            config.speed_ratio(),
        );
        
        // Update state based on FSM transitions
        defender_states[i] = determine_next_control_state(
            &defender_states[i],
            &apollonian_circle,
            &world_state.protected_zone,
            &world_state.intruder.position,
            &world_state.protected_zone.center,
        );
        
        // Calculate velocity based on current state
        let velocity = match defender_states[i] {
            ControlState::Travel => calculate_travel_velocity(
                &apollonian_circle.center,
                &world_state.protected_zone.center,
                config.defender_speed,
            ),
            ControlState::Engage => calculate_engage_velocity(world_state, i, config),
            ControlState::Intercept => calculate_intercept_velocity(
                &defender.position,
                &apollonian_circle,
                &world_state.intruder.position,
                &world_state.protected_zone.center,
                config.defender_speed,
            ),
        };
        
        velocity_commands.push(velocity);
    }
    
    velocity_commands
}

/// Legacy controller function for backward compatibility
pub fn get_defender_velocity_commands(
    world_state: &WorldState,
    config: &SimConfig,
) -> Vec<Point> {
    let mut states = vec![ControlState::Travel; world_state.defenders.len()];
    get_defender_velocity_commands_with_states(world_state, &mut states, config)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_travel_velocity() {
        let apollonian_center = Point::new(5.0, 0.0);
        let goal_center = Point::new(0.0, 0.0);
        let max_speed = 2.0;
        
        let velocity = calculate_travel_velocity(&apollonian_center, &goal_center, max_speed);
        
        assert!((velocity.magnitude() - max_speed).abs() < 1e-10);
        assert!(velocity.x < 0.0); // Should move toward goal (negative x)
        assert!(velocity.y.abs() < 1e-10); // Should be purely horizontal
    }

    #[test]
    fn test_control_state_determination() {
        let protected_zone = Circle::new(Point::new(0.0, 0.0), 2.0);
        let protected_center = Point::new(0.0, 0.0);
        
        // Test case 1: Interception opportunity (highest priority)
        // Line from intruder to goal clearly intersects Apollonian circle
        let intercepting_circle = Circle::new(Point::new(2.0, 0.0), 3.0);  
        let intruder_pos = Point::new(6.0, 0.0);  // Intruder on x-axis, line passes through circle
        
        let intercept_state = determine_next_control_state(
            &ControlState::Travel,  // Any current state
            &intercepting_circle,
            &protected_zone,
            &intruder_pos,
            &protected_center
        );
        assert_eq!(intercept_state, ControlState::Intercept);
        
        // Test case 2: No interception, circle intersects goal -> Engage
        let intersecting_circle = Circle::new(Point::new(3.0, 0.0), 2.0);
        let safe_intruder = Point::new(10.0, 10.0);  // Intruder not on direct path
        
        let engage_state = determine_next_control_state(
            &ControlState::Travel,
            &intersecting_circle,
            &protected_zone, 
            &safe_intruder,
            &protected_center
        );
        assert_eq!(engage_state, ControlState::Engage);
        
        // Test case 3: No interception, no goal intersection -> Travel
        let far_circle = Circle::new(Point::new(10.0, 0.0), 1.0);
        
        let travel_state = determine_next_control_state(
            &ControlState::Travel,
            &far_circle,
            &protected_zone,
            &safe_intruder,
            &protected_center
        );
        assert_eq!(travel_state, ControlState::Travel);
        
        // Test case 4: Intercept state is terminal
        let stay_intercept = determine_next_control_state(
            &ControlState::Intercept,
            &far_circle,  // Doesn't matter - should stay Intercept
            &protected_zone,
            &safe_intruder,
            &protected_center
        );
        assert_eq!(stay_intercept, ControlState::Intercept);
    }

    #[test]
    fn test_velocity_clamping() {
        let high_velocity = Point::new(10.0, 10.0);
        let max_speed = 5.0;
        
        let clamped = clamp_velocity(&high_velocity, max_speed);
        
        assert!((clamped.magnitude() - max_speed).abs() < 1e-10);
        // Direction should be preserved
        let original_normalized = high_velocity.normalize();
        let clamped_normalized = clamped.normalize();
        assert!((original_normalized.x - clamped_normalized.x).abs() < 1e-10);
        assert!((original_normalized.y - clamped_normalized.y).abs() < 1e-10);
    }
}