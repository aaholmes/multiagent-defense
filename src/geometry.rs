use std::f64::consts::PI;

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Point {
    pub x: f64,
    pub y: f64,
}

impl Point {
    pub fn new(x: f64, y: f64) -> Self {
        Point { x, y }
    }

    pub fn distance_to(&self, other: &Point) -> f64 {
        ((self.x - other.x).powi(2) + (self.y - other.y).powi(2)).sqrt()
    }

    pub fn angle_to(&self, other: &Point) -> f64 {
        (other.y - self.y).atan2(other.x - self.x)
    }
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Circle {
    pub center: Point,
    pub radius: f64,
}

impl Circle {
    pub fn new(center: Point, radius: f64) -> Self {
        Circle { center, radius }
    }

    /// Check if this circle intersects with another circle
    pub fn intersects(&self, other: &Circle) -> bool {
        let distance = self.center.distance_to(&other.center);
        // Circles intersect if they touch externally, overlap, or one contains the other
        distance <= (self.radius + other.radius)
    }

    /// Calculate the intersection points of two circles
    /// Returns None if circles don't intersect, Some((p1, p2)) if they do
    pub fn intersection_points(&self, other: &Circle) -> Option<(Point, Point)> {
        let d = self.center.distance_to(&other.center);
        
        // No intersection cases
        if d > self.radius + other.radius || d < (self.radius - other.radius).abs() || d == 0.0 {
            return None;
        }

        let a = (self.radius.powi(2) - other.radius.powi(2) + d.powi(2)) / (2.0 * d);
        let h = (self.radius.powi(2) - a.powi(2)).sqrt();

        let p2_x = self.center.x + a * (other.center.x - self.center.x) / d;
        let p2_y = self.center.y + a * (other.center.y - self.center.y) / d;

        let intersection1 = Point::new(
            p2_x + h * (other.center.y - self.center.y) / d,
            p2_y - h * (other.center.x - self.center.x) / d,
        );

        let intersection2 = Point::new(
            p2_x - h * (other.center.y - self.center.y) / d,
            p2_y + h * (other.center.x - self.center.x) / d,
        );

        Some((intersection1, intersection2))
    }
}

/// Calculate the Apollonian circle for a defender and intruder
/// 
/// The Apollonian circle is the locus of points P such that the ratio of distances
/// |P - defender| / |P - intruder| = k (speed ratio)
/// 
/// Returns the circle representing the defender's region of dominance
pub fn calculate_apollonian_circle(
    defender_pos: Point,
    intruder_pos: Point,
    speed_ratio: f64, // k = defender_speed / intruder_speed
) -> Circle {
    if speed_ratio == 1.0 {
        // Special case: equal speeds result in a line (perpendicular bisector)
        // For practical purposes, return a very large circle
        let midpoint = Point::new(
            (defender_pos.x + intruder_pos.x) / 2.0,
            (defender_pos.y + intruder_pos.y) / 2.0,
        );
        return Circle::new(midpoint, f64::INFINITY);
    }

    let k = speed_ratio;
    let k_sq = k * k;
    
    // Distance between defender and intruder  
    let d = defender_pos.distance_to(&intruder_pos);
    
    // Apollonian circle radius
    let radius = (k * d) / (k_sq - 1.0).abs();
    
    // Apollonian circle center - corrected formula
    let t = k_sq / (k_sq - 1.0);
    let center = Point::new(
        (defender_pos.x + t * intruder_pos.x) / (1.0 + t),
        (defender_pos.y + t * intruder_pos.y) / (1.0 + t),
    );

    Circle::new(center, radius)
}

/// Calculate the arc length of intersection between a circle and another circle
/// Returns the arc length on the first circle that lies within the second circle
pub fn calculate_arc_intersection_length(circle1: &Circle, circle2: &Circle) -> f64 {
    if !circle1.intersects(circle2) {
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
    let cos_half_angle = cos_half_angle.clamp(-1.0, 1.0);
    let half_angle = cos_half_angle.acos();
    let full_angle = 2.0 * half_angle;

    circle1.radius * full_angle
}

/// Calculate the overlap arc length between two circles on a reference circle
/// This is used to calculate redundant coverage when multiple defenders' regions overlap
pub fn calculate_arc_overlap_length(
    reference_circle: &Circle,
    circle1: &Circle,
    circle2: &Circle,
) -> f64 {
    // Get intersection arcs of both circles with the reference circle
    let arc1_length = calculate_arc_intersection_length(reference_circle, circle1);
    let arc2_length = calculate_arc_intersection_length(reference_circle, circle2);

    if arc1_length == 0.0 || arc2_length == 0.0 {
        return 0.0;
    }

    // For a more precise calculation, we need to find the actual overlap
    // This is a simplified version - a full implementation would need to
    // calculate the angular positions of the intersection arcs
    
    // Get intersection points of each circle with the reference circle
    let intersections1 = reference_circle.intersection_points(circle1);
    let intersections2 = reference_circle.intersection_points(circle2);

    match (intersections1, intersections2) {
        (Some((p1_start, p1_end)), Some((p2_start, p2_end))) => {
            // Calculate angles for each arc
            let angle1_start = reference_circle.center.angle_to(&p1_start);
            let angle1_end = reference_circle.center.angle_to(&p1_end);
            let angle2_start = reference_circle.center.angle_to(&p2_start);
            let angle2_end = reference_circle.center.angle_to(&p2_end);

            // Normalize angles to [0, 2π)
            let normalize_angle = |angle: f64| {
                let mut a = angle % (2.0 * PI);
                if a < 0.0 { a += 2.0 * PI; }
                a
            };

            let a1_start = normalize_angle(angle1_start);
            let a1_end = normalize_angle(angle1_end);
            let a2_start = normalize_angle(angle2_start);
            let a2_end = normalize_angle(angle2_end);

            // Calculate overlap (simplified - assumes no wraparound)
            let overlap_start = a1_start.max(a2_start);
            let overlap_end = a1_end.min(a2_end);

            if overlap_end > overlap_start {
                reference_circle.radius * (overlap_end - overlap_start)
            } else {
                0.0
            }
        }
        _ => 0.0,
    }
}