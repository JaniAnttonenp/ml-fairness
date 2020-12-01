# coding=utf-8
# Copyright 2019 The ML Fairness Gym Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Infrastructure for running attention allocation environment experiments.

For example useage please see attention_allocation_experiment_main.py
"""

from __future__ import absolute_import
from __future__ import division

from __future__ import print_function

import copy
import multiprocessing

import attr
import core
import run_util
from metrics import value_tracking_metrics
import numpy as np
from typing import Any, List, Mapping, Text, Tuple


@attr.s
class Experiment(object):
  """An encapsulation of an ML fairness gym experiment."""
  # The number of workers to run simulations - if 1, don't parallelize.
  num_workers = attr.ib(default=1)  # type: int

  # The number of times to run the simulation
  num_runs = attr.ib(default=50)  # type: int

  # The number of steps to simulate.
  num_steps = attr.ib(default=100)  # type: int

  # Random seed.
  seed = attr.ib(default=0)  # type: int

  # Parameterization of the environment.
  env_params = attr.ib(factory=core.Params)  # type: core.Params

  # Parameterization of the agent.
  agent_params = attr.ib(factory=core.Params)  # type: core.Params

  # Environment class to for this experiment.
  env_class = attr.ib(default=core.FairnessEnv)  # type: core.FairnessEnv

  # Agent class for this experiment.
  agent_class = attr.ib(default=core.Agent)  # type: core.Agent

  # Environment's relevant history.
  history = attr.ib(
      factory=lambda: [])  # type: List[Tuple[np.ndarray, np.ndarray]]

  def build_scenario(self):
    """Instantiates and returns an environment, agent pair."""
    env = self.env_class(self.env_params)

    if self.agent_class.__name__ == 'DummyAgent':
      agent = self.agent_class(
          env.action_space, env.observation_space, 0, seed=self.seed)
    else:
      agent = self.agent_class(
          action_space=env.action_space,
          observation_space=env.observation_space,
          reward_fn=lambda x: 0,
          params=self.agent_params)
      agent.rng.seed(self.seed)
    return env, agent


def _get_relevant_history(env):
  """Get incidents_occurred and actions from history and return in np.ndarray."""
  history = env._get_history()  # pylint: disable=protected-access
  relevant_history = np.array([
      np.array([history_item.state.incidents_occurred, history_item.action])
      for history_item in history
  ])
  return relevant_history


def run_generator(experiment):
  """Yield experiment object with seed incremented to run a simulation."""
  seed = experiment.seed
  for _ in range(experiment.num_runs):
    experiment_copy = copy.deepcopy(experiment)
    experiment_copy.seed = seed
    seed += 1
    yield experiment_copy


def run_single_simulation(experiment):
  """Create env, agent and metric objects and run a single run of an experiment."""
  env, agent = experiment.build_scenario()

  def _discovered_incidents_selection_fn(history_step):
    state, _ = history_step
    return state.incidents_seen

  discovered_incidents_metric = value_tracking_metrics.SummingMetric(
      env, _discovered_incidents_selection_fn)

  def _occurred_incidents_selection_fn(history_step):
    state, _ = history_step
    return state.incidents_occurred

  occurred_incidents_metric = value_tracking_metrics.SummingMetric(
      env, _occurred_incidents_selection_fn)

  metrics = [discovered_incidents_metric, occurred_incidents_metric]

  metric_results = run_util.run_simulation(env, agent, metrics,
                                           experiment.num_steps,
                                           experiment.seed)
  history = _get_relevant_history(env)
  metric_results.append(history)
  return metric_results


def run(experiment):
  """Run the experiment and report results."""
  experiments = [
      experiment_item
      for experiment_item in run_generator(copy.copy(experiment))
  ]

  if experiment.num_workers == 1:
    all_runs_metrics = list(map(run_single_simulation, experiments))
  else:
    pool = multiprocessing.Pool(experiment.num_workers)
    all_runs_metrics = pool.map(run_single_simulation, experiments)

  averaged_metrics = np.average(all_runs_metrics, axis=0).tolist()

  metric_names = ['discovered_incidents', 'occurred_incidents', 'history']

  named_metric_results = dict(zip(metric_names, averaged_metrics))

  return report(experiment, named_metric_results)


def report(experiment,
           named_metric_results):
  """Report results as a json string."""
  return core.to_json({
      'metrics': named_metric_results,
      'env_class': experiment.env_class.__name__,
      'agent_class': experiment.agent_class.__name__,
      'env_params': experiment.env_params,
      'agent_params': experiment.agent_params,
      'num_runs': experiment.num_runs,
      'num_steps': experiment.num_steps,
      'seed': experiment.seed
  })
