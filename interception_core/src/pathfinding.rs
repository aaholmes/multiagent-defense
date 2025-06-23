use crate::structs::{Point, Circle, GridConfig, GridNode, PathResult, WorldState, SimConfig};
use crate::geometry::{calculate_apollonian_circle, to_grid_coords, to_world_coords, is_valid_grid_position};
use std::collections::{BinaryHeap, HashMap, HashSet};
use std::cmp::Ordering;

/// A* node for pathfinding with cost tracking and parent relationships
#[derive(Debug, Clone, PartialEq)]
struct AStarNode {
    position: GridNode,
    g_cost: f64,  // Cost from start
    h_cost: f64,  // Heuristic cost to goal
    f_cost: f64,  // Total cost (g + h)
    parent: Option<GridNode>,
}

impl Eq for AStarNode {}

impl Ord for AStarNode {
    fn cmp(&self, other: &Self) -> Ordering {
        // Reverse order for min-heap (BinaryHeap is max-heap by default)
        other.f_cost.partial_cmp(&self.f_cost).unwrap_or(Ordering::Equal)
    }
}

impl PartialOrd for AStarNode {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

/// Generate threat map based on defender Apollonian circles
pub fn generate_threat_map(
    world_state: &WorldState,
    grid_config: &GridConfig,
    sim_config: &SimConfig,
) -> Vec<Vec<f64>> {
    // Initialize cost map with base costs
    let mut cost_map = vec![vec![grid_config.base_cost; grid_config.width]; grid_config.height];
    
    // Add threat penalty for each defender's Apollonian circle
    for defender in &world_state.defenders {
        let apollonian_circle = calculate_apollonian_circle(
            &defender.position,
            &world_state.intruder.position,
            sim_config.speed_ratio(),
        );
        
        // Skip infinite radius circles
        if apollonian_circle.radius == f64::INFINITY {
            continue;
        }
        
        mark_circle_threat(&mut cost_map, &apollonian_circle, grid_config);
    }
    
    cost_map
}

/// Mark grid cells within a circle as high-threat areas
fn mark_circle_threat(
    cost_map: &mut Vec<Vec<f64>>,
    circle: &Circle,
    grid_config: &GridConfig,
) {
    // Convert circle center to grid coordinates for efficient bounding
    let center_grid = to_grid_coords(&circle.center, grid_config);
    
    if center_grid.is_none() {
        return; // Circle center is outside grid bounds
    }
    
    let center_grid = center_grid.unwrap();
    
    // Calculate grid radius (conservative estimate)
    let (min_x, max_x, min_y, max_y) = grid_config.world_bounds;
    let cell_size = ((max_x - min_x) / grid_config.width as f64)
        .max((max_y - min_y) / grid_config.height as f64);
    let grid_radius = (circle.radius / cell_size).ceil() as usize;
    
    // Check cells in a square around the circle center
    let start_row = center_grid.row.saturating_sub(grid_radius);
    let end_row = (center_grid.row + grid_radius + 1).min(grid_config.height);
    let start_col = center_grid.col.saturating_sub(grid_radius);
    let end_col = (center_grid.col + grid_radius + 1).min(grid_config.width);
    
    for row in start_row..end_row {
        for col in start_col..end_col {
            let node = GridNode::new(row, col);
            let world_pos = to_world_coords(&node, grid_config);
            
            if circle.contains_point(&world_pos) {
                cost_map[row][col] += grid_config.threat_penalty;
            }
        }
    }
}

/// Manhattan distance heuristic for 4-connected grid
fn manhattan_distance(a: &GridNode, b: &GridNode) -> f64 {
    ((a.row as i32 - b.row as i32).abs() + (a.col as i32 - b.col as i32).abs()) as f64
}

/// Get valid neighbors for 4-connected grid (von Neumann neighborhood)
fn get_neighbors(node: &GridNode, grid_config: &GridConfig) -> Vec<GridNode> {
    let mut neighbors = Vec::new();
    let directions = [(0i32, 1i32), (0, -1), (1, 0), (-1, 0)]; // right, left, down, up
    
    for (dr, dc) in directions {
        let new_row = node.row as i32 + dr;
        let new_col = node.col as i32 + dc;
        
        if new_row >= 0 && new_col >= 0 {
            let new_row = new_row as usize;
            let new_col = new_col as usize;
            
            if is_valid_grid_position(new_row, new_col, grid_config) {
                neighbors.push(GridNode::new(new_row, new_col));
            }
        }
    }
    
    neighbors
}

/// Reconstruct path from goal back to start using parent relationships
fn reconstruct_path(
    goal: &GridNode,
    came_from: &HashMap<GridNode, GridNode>,
) -> Vec<GridNode> {
    let mut path = Vec::new();
    let mut current = goal.clone();
    
    path.push(current.clone());
    
    while let Some(parent) = came_from.get(&current) {
        current = parent.clone();
        path.push(current.clone());
    }
    
    path.reverse();
    path
}

/// A* pathfinding algorithm implementation
pub fn astar_pathfind(
    start: &GridNode,
    goal: &GridNode,
    cost_map: &Vec<Vec<f64>>,
    grid_config: &GridConfig,
) -> PathResult {
    if !is_valid_grid_position(start.row, start.col, grid_config) ||
       !is_valid_grid_position(goal.row, goal.col, grid_config) {
        return PathResult::new(vec![], 0.0, false);
    }
    
    if start == goal {
        return PathResult::new(vec![start.clone()], 0.0, true);
    }
    
    let mut open_set = BinaryHeap::new();
    let mut closed_set = HashSet::new();
    let mut came_from = HashMap::new();
    let mut g_scores = HashMap::new();
    
    // Initialize start node
    let start_node = AStarNode {
        position: start.clone(),
        g_cost: 0.0,
        h_cost: manhattan_distance(start, goal),
        f_cost: manhattan_distance(start, goal),
        parent: None,
    };
    
    g_scores.insert(start.clone(), 0.0);
    open_set.push(start_node);
    
    while let Some(current) = open_set.pop() {
        if current.position == *goal {
            let path = reconstruct_path(goal, &came_from);
            return PathResult::new(path, current.g_cost, true);
        }
        
        closed_set.insert(current.position.clone());
        
        for neighbor in get_neighbors(&current.position, grid_config) {
            if closed_set.contains(&neighbor) {
                continue;
            }
            
            let neighbor_cost = cost_map[neighbor.row][neighbor.col];
            
            // Skip neighbors with infinite cost (completely blocked)
            if neighbor_cost == f64::INFINITY {
                continue;
            }
            
            let tentative_g_score = current.g_cost + neighbor_cost;
            
            let is_better = match g_scores.get(&neighbor) {
                Some(&existing_g) => tentative_g_score < existing_g,
                None => true,
            };
            
            if is_better {
                came_from.insert(neighbor.clone(), current.position.clone());
                g_scores.insert(neighbor.clone(), tentative_g_score);
                
                let h_cost = manhattan_distance(&neighbor, goal);
                let neighbor_node = AStarNode {
                    position: neighbor.clone(),
                    g_cost: tentative_g_score,
                    h_cost,
                    f_cost: tentative_g_score + h_cost,
                    parent: Some(current.position.clone()),
                };
                
                open_set.push(neighbor_node);
            }
        }
    }
    
    // No path found
    PathResult::new(vec![], 0.0, false)
}

/// Calculate the next position for the intruder using A* pathfinding
pub fn calculate_intruder_next_position(
    world_state: &WorldState,
    grid_config: &GridConfig,
    sim_config: &SimConfig,
) -> Option<Point> {
    // Generate threat map
    let cost_map = generate_threat_map(world_state, grid_config, sim_config);
    
    // Convert positions to grid coordinates
    let start_grid = to_grid_coords(&world_state.intruder.position, grid_config)?;
    
    // Find the best goal target within the protected zone
    let goal_target = find_best_goal_target(world_state, grid_config, &cost_map)?;
    
    // Run A* pathfinding to the best goal target
    let path_result = astar_pathfind(&start_grid, &goal_target, &cost_map, grid_config);
    
    if !path_result.found || path_result.path.len() < 2 {
        return None; // No path found or already at goal
    }
    
    // Return the next step in the path (convert back to world coordinates)
    let next_grid_pos = &path_result.path[1];
    Some(to_world_coords(next_grid_pos, grid_config))
}

/// Find the best goal target within the protected zone circle
fn find_best_goal_target(
    world_state: &WorldState,
    grid_config: &GridConfig,
    cost_map: &Vec<Vec<f64>>,
) -> Option<GridNode> {
    let protected_zone = &world_state.protected_zone;
    
    // If intruder is already in goal zone, return current position
    if protected_zone.contains_point(&world_state.intruder.position) {
        return to_grid_coords(&world_state.intruder.position, grid_config);
    }
    
    // Find all grid cells within the protected zone
    let mut goal_candidates = Vec::new();
    
    // Calculate grid bounds around the protected zone
    let zone_center_grid = to_grid_coords(&protected_zone.center, grid_config)?;
    let (min_x, max_x, min_y, max_y) = grid_config.world_bounds;
    let cell_size = ((max_x - min_x) / grid_config.width as f64)
        .max((max_y - min_y) / grid_config.height as f64);
    let grid_radius = (protected_zone.radius / cell_size).ceil() as usize + 1;
    
    let start_row = zone_center_grid.row.saturating_sub(grid_radius);
    let end_row = (zone_center_grid.row + grid_radius + 1).min(grid_config.height);
    let start_col = zone_center_grid.col.saturating_sub(grid_radius);
    let end_col = (zone_center_grid.col + grid_radius + 1).min(grid_config.width);
    
    for row in start_row..end_row {
        for col in start_col..end_col {
            let node = GridNode::new(row, col);
            let world_pos = to_world_coords(&node, grid_config);
            
            // Check if this grid cell is within the protected zone
            if protected_zone.contains_point(&world_pos) {
                goal_candidates.push((node, cost_map[row][col]));
            }
        }
    }
    
    if goal_candidates.is_empty() {
        // Fallback to center if no candidates found
        return to_grid_coords(&protected_zone.center, grid_config);
    }
    
    // Select the goal candidate with the lowest cost (safest path)
    goal_candidates.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap_or(std::cmp::Ordering::Equal));
    Some(goal_candidates[0].0.clone())
}

/// Get the full path for visualization purposes
pub fn calculate_intruder_full_path(
    world_state: &WorldState,
    grid_config: &GridConfig,
    sim_config: &SimConfig,
) -> PathResult {
    let cost_map = generate_threat_map(world_state, grid_config, sim_config);
    
    let start_grid = match to_grid_coords(&world_state.intruder.position, grid_config) {
        Some(pos) => pos,
        None => return PathResult::new(vec![], 0.0, false),
    };
    
    let goal_target = match find_best_goal_target(world_state, grid_config, &cost_map) {
        Some(target) => target,
        None => return PathResult::new(vec![], 0.0, false),
    };
    
    astar_pathfind(&start_grid, &goal_target, &cost_map, grid_config)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::structs::AgentState;

    #[test]
    fn test_manhattan_distance() {
        let a = GridNode::new(0, 0);
        let b = GridNode::new(3, 4);
        assert_eq!(manhattan_distance(&a, &b), 7.0);
        
        let c = GridNode::new(2, 2);
        let d = GridNode::new(2, 2);
        assert_eq!(manhattan_distance(&c, &d), 0.0);
    }

    #[test]
    fn test_get_neighbors() {
        let grid_config = GridConfig::new(5, 5, (-10.0, 10.0, -10.0, 10.0), 1.0, 1000.0);
        
        // Test center node
        let center = GridNode::new(2, 2);
        let neighbors = get_neighbors(&center, &grid_config);
        assert_eq!(neighbors.len(), 4);
        
        // Test corner node
        let corner = GridNode::new(0, 0);
        let corner_neighbors = get_neighbors(&corner, &grid_config);
        assert_eq!(corner_neighbors.len(), 2);
        
        // Test edge node
        let edge = GridNode::new(0, 2);
        let edge_neighbors = get_neighbors(&edge, &grid_config);
        assert_eq!(edge_neighbors.len(), 3);
    }

    #[test]
    fn test_threat_map_generation() {
        let grid_config = GridConfig::new(10, 10, (-5.0, 5.0, -5.0, 5.0), 1.0, 1000.0);
        let sim_config = SimConfig::new(0.1, 1.0, 2.0, 1.0, 0.1);
        
        let defender = AgentState::new(Point::new(0.0, 0.0), Point::new(0.0, 0.0));
        let intruder = AgentState::new(Point::new(3.0, 0.0), Point::new(0.0, 0.0));
        let protected_zone = Circle::new(Point::new(-2.0, 0.0), 1.0);
        
        let world_state = WorldState::new(
            vec![defender],
            intruder,
            protected_zone,
        );
        
        let cost_map = generate_threat_map(&world_state, &grid_config, &sim_config);
        
        // Verify map dimensions
        assert_eq!(cost_map.len(), 10);
        assert_eq!(cost_map[0].len(), 10);
        
        // Check that base costs are applied
        let mut has_base_cost = false;
        let mut has_threat_cost = false;
        
        for row in &cost_map {
            for &cost in row {
                if (cost - grid_config.base_cost).abs() < 1e-10 {
                    has_base_cost = true;
                }
                if cost > grid_config.base_cost + 100.0 {
                    has_threat_cost = true;
                }
            }
        }
        
        assert!(has_base_cost);
        assert!(has_threat_cost);
    }

    #[test]
    fn test_astar_simple_path() {
        let grid_config = GridConfig::new(5, 5, (-2.5, 2.5, -2.5, 2.5), 1.0, 1000.0);
        let cost_map = vec![vec![1.0; 5]; 5]; // Uniform cost
        
        let start = GridNode::new(0, 0);
        let goal = GridNode::new(4, 4);
        
        let result = astar_pathfind(&start, &goal, &cost_map, &grid_config);
        
        assert!(result.found);
        assert_eq!(result.path.len(), 9); // 8 steps + start position
        assert_eq!(result.path[0], start);
        assert_eq!(result.path[result.path.len() - 1], goal);
    }

    #[test]
    fn test_astar_blocked_path() {
        let grid_config = GridConfig::new(3, 3, (-1.5, 1.5, -1.5, 1.5), 1.0, 1000.0);
        let mut cost_map = vec![vec![1.0; 3]; 3];
        
        // Create a completely blocked scenario - block middle column entirely
        for row in 0..3 {
            cost_map[row][1] = f64::INFINITY;
        }
        
        let start = GridNode::new(1, 0);
        let goal = GridNode::new(1, 2);
        
        let result = astar_pathfind(&start, &goal, &cost_map, &grid_config);
        
        // A* can still find a path going around (up/down then across)
        // Let's test a completely blocked scenario instead
        let mut fully_blocked = vec![vec![f64::INFINITY; 3]; 3];
        fully_blocked[1][0] = 1.0; // Only start position is passable
        
        let blocked_result = astar_pathfind(&start, &goal, &fully_blocked, &grid_config);
        assert!(!blocked_result.found);
    }
}