# Example 4: Lithic-L Robot Kinematics Chain

A high-level Lithic-L program defining a 2-joint robotic arm with circular trajectory arcs.

## The Language
Lithic-L compiles high-level geometric primitives (`chain`, `arc`, `snap`, `delta`) into Sovereign assembly (`.sas`).

## Compiling and Simulating
```bash
spu-lith examples/04_kinematics_chain/robot_arm.lith -o examples/04_kinematics_chain/robot_arm.sas
spu sim examples/04_kinematics_chain/robot_arm.sas --steps 20
```
Or directly via unified CLI:
```bash
spu sim examples/04_kinematics_chain/robot_arm.lith --steps 20
```
