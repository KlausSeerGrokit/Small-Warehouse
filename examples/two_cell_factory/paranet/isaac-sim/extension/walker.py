import math
import numpy as np


# Difference r1 - r2
def calc_rotation_error(r1, r2):
    err = r1 - r2
    if err > math.pi:
        return math.pi - err
    elif err < -math.pi:
        return -err - math.pi
    return err

def euler_from_quaternion(quat):
        w = quat[0]
        x = quat[1]
        y = quat[2]
        z = quat[3]

        """
        Convert a quaternion into euler angles (roll, pitch, yaw)
        roll is rotation around x in radians (counterclockwise)
        pitch is rotation around y in radians (counterclockwise)
        yaw is rotation around z in radians (counterclockwise)
        """
        t0 = +2.0 * (w * x + y * z)
        t1 = +1.0 - 2.0 * (x * x + y * y)
        roll_x = math.atan2(t0, t1)

        t2 = +2.0 * (w * y - z * x)
        t2 = +1.0 if t2 > +1.0 else t2
        t2 = -1.0 if t2 < -1.0 else t2
        pitch_y = math.asin(t2)

        t3 = +2.0 * (w * z + x * y)
        t4 = +1.0 - 2.0 * (y * y + z * z)
        yaw_z = math.atan2(t3, t4)

        return np.array([roll_x, pitch_y, yaw_z]) # in radians

# Helper to walk H1 towards a target
# Can only handle walking parallel to the x or y axis

class XYWalker:
    # position - current position
    # rotation - current rotation
    def __init__(self, robot, position, rotation):
        self.robot = robot
        self.position = position.copy()
        self.rotation = rotation
        self.counter = 0
        self.rotating = False
        self.walking = False
        self.stopping = False
        self.stop_count = 0
        self.holding = True
        self.previous = position
        self.axis = 0
        self.facing = 1

    # axis: 0=x, 1=y
    # direction: +1, -1
    def orient(self, axis, direction):
        self.axis = axis
        self.facing = direction
        if axis == 0:
            self.rotation = 0.0 if direction > 0 else math.pi
        else:
            self.rotation = math.pi/2 if direction > 0 else -math.pi/2
        self.rotating = True
        self.holding = False

    # axis: to walk along (0=x, 1=y)
    # position: target position along axis
    def set_target(self, target):
        self.position[self.axis] = target
        current, _ = self.robot.get_world_pose()
        if self.facing > 0:
            # facing positive direction
            self.walk_dir = 'forward' if target > current[self.axis] else 'backward'
        else:
            # facing negative direction
            self.walk_dir = 'forward' if target < current[self.axis] else 'backward'
        self.rotating = False
        self.walking = True
        self.stopping = False
        self.holding = False
        xy_names = ['x', 'y']
        print(f"Targeting {xy_names[self.axis]}={target} ({self.walk_dir})")

    def get_command(self, debug=False):
        cmd = np.zeros((3,))
        current, rot = self.robot.get_world_pose()
        if self.facing > 0:
            err = current - self.position
        else:
            err = self.position - current
        target_dir = 'forward' if err[self.axis] < 0 else 'backward'
        dist = np.abs(err)[self.axis]
        if self.walking:
            # if close or we've gone past the target
            if dist <= 0.001 or target_dir != self.walk_dir:
                self.walking = False
                self.stopping = True
                self.stop_count = 0
            elif dist > 1:
                # can't go backwards to quickly
                cmd[0] = 0.75 if target_dir == 'forward' else -0.25
            else:
                vel = dist * 0.5
                # can't go backwards to quickly
                cmd[0] = max(vel, 0.2) if target_dir == 'forward' else min(-vel/2, -0.2)
        if self.stopping:
            if dist > 0.005:
                cmd[0] = 0.25 if target_dir == 'forward' else -0.25
                self.stop_count = 0
            else:
                self.stop_count += 1
            if self.stop_count > 20:
                self.stopping = False
                self.holding = True
        if self.holding:
            if dist > 0.001:
                cmd[0] = 0.2 if target_dir == 'forward' else -0.2

        self.counter += 1
        auto_correct = self.counter % 5 == 0
        if auto_correct:
            other_axis = 1 - self.axis
            lock_axis = [0, 1] if self.rotating else [other_axis]
            for a in lock_axis:
                if np.abs(err)[a] > 0.001:
                    current[a] = self.position[a]
                    self.robot.set_world_pose(position=current)
        if auto_correct or self.rotating:
            rot = euler_from_quaternion(rot)
            rot_err = calc_rotation_error(rot[2], self.rotation)
            vel = 0.5 if self.rotating else 0.75
            if abs(rot_err) > 0.01:
                cmd[2] = vel if rot_err < 0 else -vel
            elif self.rotating:
                self.rotating = False
                self.holding = True
        if auto_correct and debug:
            print(cmd, target_dir, self.rotating, self.walking, self.stopping, self.holding)
        return cmd