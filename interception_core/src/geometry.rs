use crate::structs::{Point, Circle};
use std::f64::consts::PI;

/// Calculate the Apollonian circle for a defender and intruder.
/// 
/// The Apollonian circle is the locus of points P such that:
/// distance(P, defender) / distance(P, intruder) = k (speed ratio)
/// 
/// For k < 1 (defender slower), the circle passes through two points on the line:
/// - Point 1: at distance d * k/(1+k) from defender toward intruder
/// - Point 2: at distance d * k/(1-k) from defender away from intruder
pub fn calculate_apollonian_circle(
    defender_pos: &Point,
    intruder_pos: &Point,
    speed_ratio: f64,
) -> Circle {
    if (speed_ratio - 1.0).abs() < 1e-10 {
        // Special case: equal speeds result in perpendicular bisector
        let midpoint = Point::new(
            (defender_pos.x + intruder_pos.x) / 2.0,
            (defender_pos.y + intruder_pos.y) / 2.0,
        );
        return Circle::new(midpoint, f64::INFINITY);
    }

    let k = speed_ratio;
    
    // Vector from defender to intruder
    let dx = intruder_pos.x - defender_pos.x;
    let dy = intruder_pos.y - defender_pos.y;
    let d = (dx * dx + dy * dy).sqrt();
    
    // Unit vector from defender toward intruder
    let ux = dx / d;
    let uy = dy / d;
    
    if k < 1.0 {
        // Defender is slower
        // Distance from defender toward intruder
        let d1 = d * k / (1.0 + k);
        let p1 = Point::new(
            defender_pos.x + d1 * ux,
            defender_pos.y + d1 * uy,
        );
        
        // Distance from defender away from intruder  
        let d2 = d * k / (1.0 - k);
        let p2 = Point::new(
            defender_pos.x - d2 * ux,
            defender_pos.y - d2 * uy,
        );
        
        // Circle center is midpoint of p1 and p2
        let center = Point::new((p1.x + p2.x) / 2.0, (p1.y + p2.y) / 2.0);
        let radius = center.distance_to(&p1);
        
        Circle::new(center, radius)
    } else {
        // Defender is faster - circle lies between defender and intruder
        let t1 = k / (k + 1.0);
        let t2 = k / (k - 1.0);
        
        let p1 = Point::new(
            defender_pos.x + t1 * dx, 
            defender_pos.y + t1 * dy
        );
        let p2 = Point::new(
            defender_pos.x + t2 * dx, 
            defender_pos.y + t2 * dy
        );
        
        let center = Point::new((p1.x + p2.x) / 2.0, (p1.y + p2.y) / 2.0);
        let radius = center.distance_to(&p1);
        
        Circle::new(center, radius)
    }
}

/// Calculate the arc length of intersection between a circle and another circle
pub fn calculate_arc_intersection_length(circle1: &Circle, circle2: &Circle) -> f64 {
    if !circle1.intersects(circle2) || circle1.radius == f64::INFINITY || circle2.radius == f64::INFINITY {
        return 0.0;
    }

    let distance = circle1.center.distance_to(&circle2.center);
    
    // If circle1 is completely inside circle2
    if distance + circle1.radius <= circle2.radius {
        return 2.0 * PI * circle1.radius; // Full circumference
    }
    
    // If circle2 is completely inside circle1, no arc of circle1 is inside circle2
    if distance + circle2.radius <= circle1.radius {
        return 0.0;
    }

    // Calculate the central angle of the intersection arc using law of cosines
    let cos_half_angle = (circle1.radius.powi(2) + distance.powi(2) - circle2.radius.powi(2)) 
        / (2.0 * circle1.radius * distance);
    
    // Clamp to valid range for acos
    let cos_half_angle = cos_half_angle.max(-1.0).min(1.0);
    let half_angle = cos_half_angle.acos();
    let full_angle = 2.0 * half_angle;

    circle1.radius * full_angle
}

/// Calculate the intersection points between two circles
pub fn circle_intersection_points(circle1: &Circle, circle2: &Circle) -> Vec<Point> {
    if !circle1.intersects(circle2) || circle1.radius == f64::INFINITY || circle2.radius == f64::INFINITY {
        return vec![];
    }

    let d = circle1.center.distance_to(&circle2.center);
    
    // Check for coincident circles
    if d == 0.0 && (circle1.radius - circle2.radius).abs() < 1e-10 {
        return vec![]; // Infinite intersection points
    }
    
    // Check if one circle is inside the other
    if d + circle1.radius.min(circle2.radius) < circle1.radius.max(circle2.radius) {
        return vec![];
    }

    let a = (circle1.radius.powi(2) - circle2.radius.powi(2) + d.powi(2)) / (2.0 * d);
    let h = (circle1.radius.powi(2) - a.powi(2)).sqrt();
    
    // Point on line between centers
    let p = Point::new(
        circle1.center.x + a * (circle2.center.x - circle1.center.x) / d,
        circle1.center.y + a * (circle2.center.y - circle1.center.y) / d,
    );
    
    // If h is very small, circles touch at one point
    if h.abs() < 1e-10 {
        return vec![p];
    }
    
    // Two intersection points
    let intersection1 = Point::new(
        p.x + h * (circle2.center.y - circle1.center.y) / d,
        p.y - h * (circle2.center.x - circle1.center.x) / d,
    );
    let intersection2 = Point::new(
        p.x - h * (circle2.center.y - circle1.center.y) / d,
        p.y + h * (circle2.center.x - circle1.center.x) / d,
    );
    
    vec![intersection1, intersection2]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_apollonian_circle_basic() {
        let defender = Point::new(0.0, 0.0);
        let intruder = Point::new(4.0, 0.0);
        let speed_ratio = 0.5;
        
        let circle = calculate_apollonian_circle(&defender, &intruder, speed_ratio);
        
        // Check that circle passes through expected points
        let p1 = Point::new(4.0/3.0, 0.0); // 1/3 toward intruder
        let p2 = Point::new(-4.0, 0.0);    // d behind defender
        
        let dist1 = circle.center.distance_to(&p1);
        let dist2 = circle.center.distance_to(&p2);
        
        assert!((dist1 - circle.radius).abs() < 1e-10);
        assert!((dist2 - circle.radius).abs() < 1e-10);
    }

    #[test]
    fn test_circle_intersection() {
        let circle1 = Circle::new(Point::new(0.0, 0.0), 2.0);
        let circle2 = Circle::new(Point::new(3.0, 0.0), 2.0);
        
        assert!(circle1.intersects(&circle2));
        
        let points = circle_intersection_points(&circle1, &circle2);
        assert_eq!(points.len(), 2);
        
        // Both points should be on both circles
        for point in &points {
            assert!((circle1.center.distance_to(point) - circle1.radius).abs() < 1e-10);
            assert!((circle2.center.distance_to(point) - circle2.radius).abs() < 1e-10);
        }
    }
}