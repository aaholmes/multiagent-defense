use pyo3::prelude::*;
use std::f64::consts::PI;

#[pyclass]
#[derive(Clone, Debug)]
pub struct Point {
    #[pyo3(get, set)]
    pub x: f64,
    #[pyo3(get, set)]
    pub y: f64,
}

#[pymethods]
impl Point {
    #[new]
    pub fn new(x: f64, y: f64) -> Self {
        Point { x, y }
    }

    pub fn distance_to(&self, other: &Point) -> f64 {
        ((self.x - other.x).powi(2) + (self.y - other.y).powi(2)).sqrt()
    }

    pub fn angle_to(&self, other: &Point) -> f64 {
        (other.y - self.y).atan2(other.x - self.x)
    }

    pub fn normalize(&self) -> Point {
        let mag = (self.x * self.x + self.y * self.y).sqrt();
        if mag == 0.0 {
            Point { x: 0.0, y: 0.0 }
        } else {
            Point { 
                x: self.x / mag, 
                y: self.y / mag 
            }
        }
    }

    pub fn magnitude(&self) -> f64 {
        (self.x * self.x + self.y * self.y).sqrt()
    }

    pub fn __add__(&self, other: &Point) -> Point {
        Point {
            x: self.x + other.x,
            y: self.y + other.y,
        }
    }

    pub fn __sub__(&self, other: &Point) -> Point {
        Point {
            x: self.x - other.x,
            y: self.y - other.y,
        }
    }

    pub fn __mul__(&self, scalar: f64) -> Point {
        Point {
            x: self.x * scalar,
            y: self.y * scalar,
        }
    }

    pub fn __repr__(&self) -> String {
        format!("Point({:.3}, {:.3})", self.x, self.y)
    }
}

#[pyclass]
#[derive(Clone, Debug)]
pub struct Circle {
    #[pyo3(get, set)]
    pub center: Point,
    #[pyo3(get, set)]
    pub radius: f64,
}

#[pymethods]
impl Circle {
    #[new]
    pub fn new(center: Point, radius: f64) -> Self {
        Circle { center, radius }
    }

    pub fn intersects(&self, other: &Circle) -> bool {
        if self.radius == f64::INFINITY || other.radius == f64::INFINITY {
            return false;
        }
        let distance = self.center.distance_to(&other.center);
        distance <= (self.radius + other.radius)
    }

    pub fn contains_point(&self, point: &Point) -> bool {
        if self.radius == f64::INFINITY {
            return false;
        }
        self.center.distance_to(point) <= self.radius
    }

    pub fn __repr__(&self) -> String {
        format!("Circle(center={}, radius={:.3})", self.center.__repr__(), self.radius)
    }
}

#[pyclass]
#[derive(Clone, Debug)]
pub struct AgentState {
    #[pyo3(get, set)]
    pub position: Point,
    #[pyo3(get, set)]
    pub velocity: Point,
}

#[pymethods]
impl AgentState {
    #[new]
    pub fn new(position: Point, velocity: Point) -> Self {
        AgentState { position, velocity }
    }

    pub fn __repr__(&self) -> String {
        format!(
            "AgentState(pos={}, vel={})", 
            self.position.__repr__(), 
            self.velocity.__repr__()
        )
    }
}

#[pyclass]
#[derive(Clone, Debug)]
pub struct WorldState {
    #[pyo3(get, set)]
    pub defenders: Vec<AgentState>,
    #[pyo3(get, set)]
    pub intruder: AgentState,
    #[pyo3(get, set)]
    pub protected_zone: Circle,
}

#[pymethods]
impl WorldState {
    #[new]
    pub fn new(defenders: Vec<AgentState>, intruder: AgentState, protected_zone: Circle) -> Self {
        WorldState {
            defenders,
            intruder,
            protected_zone,
        }
    }

    pub fn __repr__(&self) -> String {
        format!(
            "WorldState(defenders={}, intruder={}, protected_zone={})",
            self.defenders.len(),
            self.intruder.__repr__(),
            self.protected_zone.__repr__()
        )
    }
}

#[pyclass]
#[derive(Clone, Debug)]
pub struct SimConfig {
    #[pyo3(get, set)]
    pub learning_rate: f64,
    #[pyo3(get, set)]
    pub defender_speed: f64,
    #[pyo3(get, set)]
    pub intruder_speed: f64,
    #[pyo3(get, set)]
    pub w_repel: f64,  // Weight for overlap penalty
    #[pyo3(get, set)]
    pub epsilon: f64,  // Overlap tolerance
}

#[pymethods]
impl SimConfig {
    #[new]
    pub fn new(
        learning_rate: f64,
        defender_speed: f64,
        intruder_speed: f64,
        w_repel: f64,
        epsilon: f64,
    ) -> Self {
        SimConfig {
            learning_rate,
            defender_speed,
            intruder_speed,
            w_repel,
            epsilon,
        }
    }

    pub fn speed_ratio(&self) -> f64 {
        self.defender_speed / self.intruder_speed
    }
}

// Internal enums (not exposed to Python)
#[derive(Debug, Clone, PartialEq)]
pub enum ControlState {
    Travel,
    Engage,
}

#[derive(Debug, Clone)]
pub struct Arc {
    pub start_angle: f64,
    pub end_angle: f64,
}

impl Arc {
    pub fn new(start_angle: f64, end_angle: f64) -> Self {
        Arc { start_angle, end_angle }
    }

    pub fn length(&self) -> f64 {
        let mut length = self.end_angle - self.start_angle;
        if length < 0.0 {
            length += 2.0 * PI;
        }
        length
    }

    pub fn overlaps(&self, other: &Arc) -> f64 {
        // Calculate overlap between two arcs (simplified implementation)
        let start = self.start_angle.max(other.start_angle);
        let end = self.end_angle.min(other.end_angle);
        if start <= end {
            end - start
        } else {
            0.0
        }
    }
}