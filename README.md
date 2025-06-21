# Decentralized Dynamic Interception using Apollonian Circles
A Rust/Python project implementing a decentralized multi-robot control strategy for a team of defenders to intercept a faster intruder before it reaches a protected zone. The core of the algorithm is based on the geometric properties of Apollonian Circles and a robust, hybrid control law.

(Placeholder for the most important part of the README: a GIF of the final simulation in action!)

Project Status
Status: Functional Prototype

The core algorithms are implemented in a high-performance Rust library with Python bindings. The Python simulation layer can run various scenarios and visualize the results in real-time, demonstrating the effectiveness of the hybrid control strategy.

The Core Algorithm: A Story of Design and Discovery
The strategy relies on a key geometric insight and an iteratively improved control law.

1. The Core Insight: Apollonian Circles
For a single defender at P_d and an intruder at P_i, the set of all possible interception points forms a circle known as the Circle of Apollonius. This circle is defined by the ratio of speeds k=s_d/s_i. Any point inside this circle is a location where the defender can guarantee an interception. We call this the robot's Region of Dominance.

2. The Initial Strategy: Gradient-Based Control
The team's goal is to arrange their individual Regions of Dominance to form an impenetrable barrier around the protected zone. The initial approach was to have each robot minimize a single loss function via gradient descent:

Loss = - (Covered_Perimeter) + (Redundant_Overlap_Penalty)

This function encourages robots to cover the protected perimeter while penalizing inefficient clustering.

3. The Critical Flaw: The Zero-Gradient Problem
Analysis revealed a fatal flaw: if a robot is too far away, its Region of Dominance doesn't touch the protected zone. In this state, the "Covered_Perimeter" term (and its gradient) is zero. The robot feels no "pull" towards the objective and fails to engage, allowing the intruder to win.

4. The Robust Solution: A Hybrid Controller
The final, robust solution is a two-state hybrid controller that makes the system far more intelligent:

Travel State: If a robot is too far away to help, it minimizes a simple loss function based on its distance to the protected zone. This creates a strong, long-range attraction force that says "Get to the fight!"
Engage State: Once its Region of Dominance overlaps with the protected zone, it switches to the sophisticated perimeter-coverage loss function. This allows it to fluidly integrate into the defensive barrier with its teammates.
This hybrid approach ensures robots first get to the action, then contribute intelligently to the team strategy, showcasing a complete cycle of design, analysis, and robustification.

Setup and Running the Simulation
This project uses maturin to build the Rust library and create Python bindings.

Clone the repository:
Bash

git clone https://github.com/your-username/dynamic-interception.git
cd dynamic-interception
Set up a Python virtual environment:
Bash

python3 -m venv .venv
source .venv/bin/activate
Install dependencies and build the Rust library:
Bash

pip install -r requirements.txt
maturin develop
Run a simulation:
Bash

python simulation/run_simulation.py
