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

"""Plotting functions for the attention allocation example experiments."""

import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# TODO() write tests for the plotting functions.

MEDIUM_FONTSIZE = 14
LARGE_FONTSIZE = 16


def create_dataframe_from_results(agent_names, value_to_report_dicts):
  """Turn json reports into a dataframe that can be used to plot the results.

  Args:
    agent_names: list of str names of each agent.
    value_to_report_dicts: list of dictionaries, where each dictionary
      corresponds to a set of experiments for each of the agents in agent_names.
      The dictionary maps a parameter value of dynamic factor to the json string
      report.

  Returns:
    A pandas dataframe.
  """
  pandas_df_data = []
  for agent_index in range(len(agent_names)):
    # TODO() clean up using pandas.read_json.
    # to make this code nicer.
    agent_name = agent_names[agent_index]
    # The keys of the value_to_report_dict should be the values of the varied
    # parameter, in this case, the dynamic rate.
    for value in value_to_report_dicts[agent_index].keys():
      df_row = {}
      df_row['agent_type'] = agent_name
      df_row['param_explored'] = 'dynamic factor'
      df_row['param_value'] = str(value)
      report = json.loads(value_to_report_dicts[agent_index][value])

      discovered_incidents = np.array(report['metrics']['discovered_incidents'])
      discovered_total = np.sum(discovered_incidents)
      missed_incidents = np.array(
          report['metrics']['occurred_incidents']) - np.array(
              report['metrics']['discovered_incidents'])
      missed_total = np.sum(missed_incidents)
      df_row['total_missed'] = missed_total
      df_row['total_discovered'] = discovered_total
      pandas_df_data.append(df_row)
  return pd.DataFrame(pandas_df_data)


def plot_occurence_action_single_dynamic(report, file_path=''):
  """Plot line charts of actions and incident occurences over time."""
  # History here is not a core.HistoryItem object. It is a list of lists
  # generated by attention_allocation_experiment's _get_relevant_history().
  history = report['metrics']['history']
  plt.figure(figsize=(16, 4))

  n_locations = report['env_params']['n_locations']

  action_data = np.asarray([item[1] for item in history])
  plt.subplot(1, 2, 1)
  for location in range(n_locations):
    plt.plot(action_data[:, location], label='loc=%d' % (location))
  plt.xlabel('Time steps', fontsize=16)
  plt.ylabel('Attention units allocated', fontsize=LARGE_FONTSIZE)
  plt.xticks(fontsize=MEDIUM_FONTSIZE)
  plt.yticks(fontsize=MEDIUM_FONTSIZE)

  incidents_data = np.asarray([item[0] for item in history])
  plt.subplot(1, 2, 2)
  for location in range(n_locations):
    plt.plot(incidents_data[:, location], label='loc=%d' % (location))
  plt.xlabel('Time steps', fontsize=16)
  plt.ylabel('Incidents occurred', fontsize=LARGE_FONTSIZE)
  plt.xticks(fontsize=MEDIUM_FONTSIZE)
  plt.yticks(fontsize=MEDIUM_FONTSIZE)
  plt.savefig(file_path + '.pdf', bbox_inches='tight')


def plot_total_miss_discovered(dataframe, file_path=''):
  """Plot bar charts comparing agents total missed and discovered incidents."""
  plot_height = 5
  aspect_ratio = 1.3
  sns.set_style('whitegrid')
  sns.despine()

  sns.catplot(
      x='param_value',
      y='total_missed',
      data=dataframe,
      hue='agent_type',
      kind='bar',
      palette='muted',
      height=plot_height,
      aspect=aspect_ratio,
      legend=False)
  plt.xlabel('Dynamic factor', fontsize=LARGE_FONTSIZE)
  plt.ylabel('Total missed incidents', fontsize=LARGE_FONTSIZE)
  plt.xticks(fontsize=MEDIUM_FONTSIZE)
  plt.yticks(fontsize=MEDIUM_FONTSIZE)
  plt.legend(fontsize=MEDIUM_FONTSIZE, title_fontsize=MEDIUM_FONTSIZE)
  plt.savefig(file_path + '_missed.pdf', bbox_inches='tight')

  sns.catplot(
      x='param_value',
      y='total_discovered',
      data=dataframe,
      hue='agent_type',
      kind='bar',
      palette='muted',
      height=plot_height,
      aspect=aspect_ratio,
      legend=False)
  plt.xlabel('Dynamic factor', fontsize=LARGE_FONTSIZE)
  plt.ylabel('Total discovered incidents', fontsize=LARGE_FONTSIZE)
  plt.xticks(fontsize=14)
  plt.yticks(fontsize=14)
  plt.legend(fontsize=MEDIUM_FONTSIZE, title_fontsize=MEDIUM_FONTSIZE)
  plt.savefig(file_path + '_discovered.pdf', bbox_inches='tight')
