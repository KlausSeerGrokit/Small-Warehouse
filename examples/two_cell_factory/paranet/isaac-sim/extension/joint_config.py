import re
from typing import Union
from dataclasses import dataclass

import numpy as np

@dataclass(kw_only=True)
class ImplicitActuatorCfg:
  joint_names_expr: list[str]
  effort_limit: Union[dict[str,float],float] = None
  velocity_limit: Union[dict[str,float],float] = None
  stiffness: Union[dict[str,float],float] = None
  damping: Union[dict[str,float],float] = None
  armature: Union[dict[str,float],float] = None

  def apply(joint_names, cfgs, view):
    joint_map = dict([(name, idx) for idx, name in enumerate(joint_names)])
    N = len(joint_names)
    joint_effort = nans((N,))
    joint_velocity = nans((N,))
    joint_stiffness = nans((N,))
    joint_damping = nans((N,))
    joint_armature = nans((N,))
    for name, cfg in cfgs.items():
      sel = filter_strings(joint_names, cfg.joint_names_expr)
      ImplicitActuatorCfg._apply_one(joint_map, sel, cfg.effort_limit, joint_effort)
      ImplicitActuatorCfg._apply_one(joint_map, sel, cfg.velocity_limit, joint_velocity)
      ImplicitActuatorCfg._apply_one(joint_map, sel, cfg.stiffness, joint_stiffness)
      ImplicitActuatorCfg._apply_one(joint_map, sel, cfg.damping, joint_damping)
      ImplicitActuatorCfg._apply_one(joint_map, sel, cfg.armature, joint_armature)

    if np.any(np.isnan(joint_stiffness)) or np.any(np.isnan(joint_damping)):
      raise Exception('Joint config stiffness/damping does not cover all joints')
    view.set_gains(joint_stiffness, joint_damping)

    indices = np.nonzero(~np.isnan(joint_effort))
    view.set_max_efforts(joint_effort[indices], joint_indices=indices)

    indices = np.nonzero(~np.isnan(joint_velocity))
    view.set_max_joint_velocities(joint_velocity[indices], joint_indices=indices)

    indices = np.nonzero(~np.isnan(joint_armature))
    view.set_armatures(joint_armature[indices], joint_indices=indices)

  def _apply_one(joint_map, selection, value, target):
    if value != None:
      if type(value) == float or type(value) == int:
        for name in selection:
          target[joint_map[name]] = value
      elif type(value) == dict:
        for expr,value1 in value.items():
          for name in filter_strings(selection, [expr]):
            target[joint_map[name]] = value1

def nans(shape):
  a = np.empty(shape)
  a[:] = np.nan
  return a

def filter_strings(all, exprs):
  matched = []
  for expr in exprs:
    cur = [s for s in all if re.fullmatch(expr, s)]
    matched.extend(cur)
  return matched
