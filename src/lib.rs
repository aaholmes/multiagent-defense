pub mod geometry;

pub use geometry::{Point, Circle, calculate_apollonian_circle, calculate_arc_intersection_length, calculate_arc_overlap_length};

#[cfg(test)]
mod tests {
    use super::*;
    use std::f64::consts::PI;

    #[test]
    fn test_apollonian_circle_basic() {
        let defender = Point::new(0.0, 0.0);
        let intruder = Point::new(4.0, 0.0);
        let speed_ratio = 0.5; // Defender is half as fast
        
        let circle = calculate_apollonian_circle(defender, intruder, speed_ratio);
        
        // For k=0.5, k²=0.25, t=k²/(k²-1)=0.25/(-0.75)=-1/3
        // center = (0 + (-1/3)*4)/(1 + (-1/3)) = (-4/3)/(2/3) = -2
        // radius = k*d/|k²-1| = 0.5*4/0.75 = 8/3
        assert!((circle.center.x - (-2.0)).abs() < 1e-10);
        assert!((circle.center.y - 0.0).abs() < 1e-10);
        assert!((circle.radius - 8.0/3.0).abs() < 1e-10);
    }

    #[test]
    fn test_apollonian_circle_equal_speeds() {
        let defender = Point::new(0.0, 0.0);
        let intruder = Point::new(2.0, 0.0);
        let speed_ratio = 1.0; // Equal speeds
        
        let circle = calculate_apollonian_circle(defender, intruder, speed_ratio);
        
        // Should return infinite radius (perpendicular bisector case)
        assert!(circle.radius.is_infinite());
        // Center should be at midpoint
        assert!((circle.center.x - 1.0).abs() < 1e-10);
        assert!((circle.center.y - 0.0).abs() < 1e-10);
    }

    #[test]
    fn test_circle_intersection() {
        let circle1 = Circle::new(Point::new(0.0, 0.0), 2.0);
        let circle2 = Circle::new(Point::new(3.0, 0.0), 2.0);
        
        assert!(circle1.intersects(&circle2));
        
        let intersections = circle1.intersection_points(&circle2);
        assert!(intersections.is_some());
        
        if let Some((p1, p2)) = intersections {
            // For circles at (0,0) r=2 and (3,0) r=2:
            // a = (4 - 4 + 9)/(2*3) = 1.5
            // h = sqrt(4 - 2.25) = sqrt(1.75)
            // Points are at (1.5, ±sqrt(1.75))
            assert!((p1.x - 1.5).abs() < 1e-10);
            assert!((p2.x - 1.5).abs() < 1e-10);
            assert!((p1.y.abs() - (1.75_f64.sqrt())).abs() < 1e-10);
            assert!((p2.y.abs() - (1.75_f64.sqrt())).abs() < 1e-10);
        }
    }

    #[test]
    fn test_arc_intersection_length() {
        // Two unit circles with centers 1 unit apart
        let circle1 = Circle::new(Point::new(0.0, 0.0), 1.0);
        let circle2 = Circle::new(Point::new(1.0, 0.0), 1.0);
        
        let arc_length = calculate_arc_intersection_length(&circle1, &circle2);
        
        // Using law of cosines: cos(θ/2) = (1² + 1² - 1²)/(2*1*1) = 1/2
        // So θ/2 = π/3, θ = 2π/3, arc length = r*θ = 1 * 2π/3
        let expected = (2.0/3.0) * PI;
        assert!((arc_length - expected).abs() < 1e-10);
    }

    #[test]
    fn test_arc_intersection_no_overlap() {
        let circle1 = Circle::new(Point::new(0.0, 0.0), 1.0);
        let circle2 = Circle::new(Point::new(3.0, 0.0), 1.0);
        
        let arc_length = calculate_arc_intersection_length(&circle1, &circle2);
        assert_eq!(arc_length, 0.0);
    }

    #[test]
    fn test_arc_intersection_complete_containment() {
        let small_circle = Circle::new(Point::new(0.0, 0.0), 1.0);
        let large_circle = Circle::new(Point::new(0.0, 0.0), 2.0);
        
        // small_circle completely inside large_circle
        let arc_length = calculate_arc_intersection_length(&small_circle, &large_circle);
        let expected = 2.0 * PI; // Full circumference of small circle
        assert!((arc_length - expected).abs() < 1e-10);
        
        // large_circle with small_circle inside - no arc of large circle is inside small circle
        let arc_length_reverse = calculate_arc_intersection_length(&large_circle, &small_circle);
        assert_eq!(arc_length_reverse, 0.0);
    }

    #[test]
    fn test_point_distance() {
        let p1 = Point::new(0.0, 0.0);
        let p2 = Point::new(3.0, 4.0);
        
        assert_eq!(p1.distance_to(&p2), 5.0);
    }

    #[test]
    fn test_point_angle() {
        let p1 = Point::new(0.0, 0.0);
        let p2 = Point::new(1.0, 1.0);
        
        let angle = p1.angle_to(&p2);
        assert!((angle - PI/4.0).abs() < 1e-10);
    }
}