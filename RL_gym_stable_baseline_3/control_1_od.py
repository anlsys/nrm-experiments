#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 19 09:27:26 2020

@author: sophiecerf
"""

# Libraries
import os
import pandas as pd
import matplotlib.pyplot as plt
import yaml
import math
# For data modeling
import scipy.optimize as opt
import numpy as np
import tarfile
from matplotlib import cm
import seaborn as sns

exp_type = 'controller'  # ex: 'stairs' 'identification' 'static_characteristic' 'controller' XXX
# experiment_dir = os.getcwd() + '/Documents/ctrl-rapl/euro-par-2021-artifacts/dataset/'+exp_type+'/experiments-data/' # XXX
experiment_dir = '/home/akhilesh.raj/Desktop/ANL_repo/europar-96-artifacts/dataset/' + exp_type + '/experiments-data/'
clusters = next(os.walk(experiment_dir))[1]  # clusters are name of folders
# if (exp_type == 'stairs') or (exp_type == 'static_characteristic'):
#     experiment_type = 'controller'
# else:
#     experiment_type = exp_type
experiment_type = 'controller'
cluster = 'gros'
traces = {}
traces_tmp = {}
traces[cluster] = pd.DataFrame()

traces[cluster][0] = next(os.walk(experiment_dir + cluster))[1]

data = {}
data[cluster] = {}

for trace in traces[cluster][0]:
    data[cluster][trace] = {}
    folder_path = experiment_dir + cluster + '/' + trace
    # Trace experimental plan: parameters or log
    if os.path.isfile(folder_path + '/SUCCESS'):
        data[cluster][trace]['SUCCESS'] = True
    else:
        data[cluster][trace]['SUCCESS'] = False
    if os.path.isfile(folder_path + '/parameters.yaml'):
        with open(folder_path + "/parameters.yaml") as file:
            data[cluster][trace]['parameters'] = yaml.load(file, Loader=yaml.FullLoader)
            with open(folder_path + '/' + data[cluster][trace]['parameters']['config-file']) as file:
                data[cluster][trace]['parameters']['config-file'] = yaml.load(file, Loader=yaml.FullLoader)
    data[cluster][trace]['identification-runner-log'] = pd.read_csv(
        folder_path + "/" + experiment_type + "-runner.log", sep='\0',
        names=['created', 'levelname', 'process', 'funcName', 'message'])
    data[cluster][trace]['enforce_powercap'] = data[cluster][trace]['identification-runner-log'][
        data[cluster][trace]['identification-runner-log']['funcName'] == 'enforce_powercap']
    data[cluster][trace]['enforce_powercap'] = data[cluster][trace]['enforce_powercap'].set_index('created')
    data[cluster][trace]['enforce_powercap']['powercap'] = [
        ''.join(c for c in data[cluster][trace]['enforce_powercap']['message'][i] if c.isdigit()) for i in
        data[cluster][trace]['enforce_powercap'].index]
    # Loading sensors data files
    pubMeasurements = pd.read_csv(folder_path + "/dump_pubMeasurements.csv")
    pubProgress = pd.read_csv(folder_path + "/dump_pubProgress.csv")
    # Extracting sensor data
    rapl_sensor0 = rapl_sensor1 = rapl_sensor2 = rapl_sensor3 = downstream_sensor = pd.DataFrame(
        {'timestamp': [], 'value': []})
    for i, row in pubMeasurements.iterrows():
        if row['sensor.id'] == 'RaplKey (PackageID 0)':
            rapl_sensor0 = rapl_sensor0.append({'timestamp': row['sensor.timestamp'], 'value': row['sensor.value']},
                                               ignore_index=True)
        elif row['sensor.id'] == 'RaplKey (PackageID 1)':
            rapl_sensor1 = rapl_sensor1.append({'timestamp': row['sensor.timestamp'], 'value': row['sensor.value']},
                                               ignore_index=True)
        elif row['sensor.id'] == 'RaplKey (PackageID 2)':
            rapl_sensor2 = rapl_sensor1.append({'timestamp': row['sensor.timestamp'], 'value': row['sensor.value']},
                                               ignore_index=True)
        elif row['sensor.id'] == 'RaplKey (PackageID 3)':
            rapl_sensor3 = rapl_sensor1.append({'timestamp': row['sensor.timestamp'], 'value': row['sensor.value']},
                                               ignore_index=True)
    progress_sensor = pd.DataFrame(
        {'timestamp': pubProgress['msg.timestamp'], 'value': pubProgress['sensor.value']})
    # Writing in data dict
    data[cluster][trace]['rapl_sensors'] = pd.DataFrame(
        {'timestamp': rapl_sensor0['timestamp'], 'value0': rapl_sensor0['value'], 'value1': rapl_sensor1['value'],
         'value2': rapl_sensor2['value'], 'value3': rapl_sensor3['value']})
    data[cluster][trace]['performance_sensors'] = pd.DataFrame(
        {'timestamp': progress_sensor['timestamp'], 'progress': progress_sensor['value']})
    # data[cluster][trace]['nrm_downstream_sensors'] = pd.DataFrame({'timestamp':downstream_sensor['timestamp'],'downstream':downstream_sensor['value']})
    # Indexing on elasped time since the first data point
    data[cluster][trace]['first_sensor_point'] = min(data[cluster][trace]['rapl_sensors']['timestamp'][0],
                                                     data[cluster][trace]['performance_sensors']['timestamp'][
                                                         0])  # , data[cluster][trace]['nrm_downstream_sensors']['timestamp'][0])
    data[cluster][trace]['rapl_sensors']['elapsed_time'] = (
                data[cluster][trace]['rapl_sensors']['timestamp'] - data[cluster][trace]['first_sensor_point'])
    data[cluster][trace]['rapl_sensors'] = data[cluster][trace]['rapl_sensors'].set_index('elapsed_time')
    data[cluster][trace]['performance_sensors']['elapsed_time'] = (
                data[cluster][trace]['performance_sensors']['timestamp'] - data[cluster][trace][
            'first_sensor_point'])
    data[cluster][trace]['performance_sensors'] = data[cluster][trace]['performance_sensors'].set_index(
        'elapsed_time')


for trace in traces[cluster][0]:
    # Average sensors value
    avg0 = data[cluster][trace]['rapl_sensors']['value0'].mean()
    avg1 = data[cluster][trace]['rapl_sensors']['value1'].mean()
    avg2 = data[cluster][trace]['rapl_sensors']['value2'].mean()
    avg3 = data[cluster][trace]['rapl_sensors']['value3'].mean()
    data[cluster][trace]['aggregated_values'] = {'rapl0': avg0, 'rapl1': avg1, 'rapl2': avg2, 'rapl3': avg3,
                                                 'progress': data[cluster][trace]['performance_sensors'][
                                                     'progress']}  # 'rapl0_std':std0,'rapl1_std':std1,'rapl2_std':std2,'rapl3_std':std3,'downstream':data[cluster][trace]['nrm_downstream_sensors']['downstream'].mean(),'progress':data[cluster][trace]['performance_sensors']['progress']}
    avgs = pd.DataFrame({'averages': [avg0, avg1, avg2, avg3]})
    data[cluster][trace]['aggregated_values']['rapls'] = avgs.mean()[0]
    # Sensors periods and frequencies
    # RAPL
    rapl_elapsed_time = data[cluster][trace]['rapl_sensors'].index
    data[cluster][trace]['aggregated_values']['rapls_periods'] = pd.DataFrame(
        [rapl_elapsed_time[t] - rapl_elapsed_time[t - 1] for t in range(1, len(rapl_elapsed_time))],
        index=[rapl_elapsed_time[t] for t in range(1, len(rapl_elapsed_time))], columns=['periods'])
    # Progress
    performance_elapsed_time = data[cluster][trace]['performance_sensors'].index
    data[cluster][trace]['aggregated_values']['performance_frequency'] = pd.DataFrame(
        [1 / (performance_elapsed_time[t] - performance_elapsed_time[t - 1]) for t in
         range(1, len(performance_elapsed_time))],
        index=[performance_elapsed_time[t] for t in range(1, len(performance_elapsed_time))], columns=['frequency'])
    # Execution time:
    data[cluster][trace]['aggregated_values']['execution_time'] = performance_elapsed_time[-1]
    data[cluster][trace]['aggregated_values']['upsampled_timestamps'] = data[cluster][trace]['rapl_sensors'].index
    # Computing count and frequency at upsampled_frequency:
    data[cluster][trace]['aggregated_values']['progress_frequency_median'] = pd.DataFrame({'median': np.nanmedian(
        data[cluster][trace]['aggregated_values']['performance_frequency']['frequency'].where(
            data[cluster][trace]['aggregated_values']['performance_frequency'].index <=
            data[cluster][trace]['aggregated_values']['upsampled_timestamps'][0], 0)), 'timestamp':
                                                                                               data[cluster][trace][
                                                                                                   'aggregated_values'][
                                                                                                   'upsampled_timestamps'][
                                                                                                   0]}, index=[0])
    idx = 0  # index of powercap change in log
    data[cluster][trace]['aggregated_values']['pcap'] = pd.DataFrame(
        {'pcap': math.nan, 'timestamp': data[cluster][trace]['aggregated_values']['upsampled_timestamps'][0]},
        index=[0])
    for t in range(1, len(data[cluster][trace]['aggregated_values']['upsampled_timestamps'])):
        data[cluster][trace]['aggregated_values']['progress_frequency_median'] = \
        data[cluster][trace]['aggregated_values']['progress_frequency_median'].append({'median': np.nanmedian(
            data[cluster][trace]['aggregated_values']['performance_frequency']['frequency'].where((data[cluster][
                                                                                                       trace][
                                                                                                       'aggregated_values'][
                                                                                                       'performance_frequency'].index >=
                                                                                                   data[cluster][
                                                                                                       trace][
                                                                                                       'aggregated_values'][
                                                                                                       'upsampled_timestamps'][
                                                                                                       t - 1]) & (
                                                                                                              data[
                                                                                                                  cluster][
                                                                                                                  trace][
                                                                                                                  'aggregated_values'][
                                                                                                                  'performance_frequency'].index <=
                                                                                                              data[
                                                                                                                  cluster][
                                                                                                                  trace][
                                                                                                                  'aggregated_values'][
                                                                                                                  'upsampled_timestamps'][
                                                                                                                  t]))),
                                                                                       'timestamp':
                                                                                           data[cluster][trace][
                                                                                               'aggregated_values'][
                                                                                               'upsampled_timestamps'][
                                                                                               t]},
                                                                                      ignore_index=True)
        if (experiment_type == 'controller') or (experiment_type == 'identification'):
            if (data[cluster][trace]['enforce_powercap'].index[idx] - data[cluster][trace]['first_sensor_point']) < \
                    data[cluster][trace]['aggregated_values']['upsampled_timestamps'][t]:
                if idx < len(data[cluster][trace]['enforce_powercap']) - 1:
                    idx = idx + 1
            if (data[cluster][trace]['enforce_powercap'].index[0] - data[cluster][trace]['first_sensor_point']) > \
                    data[cluster][trace]['aggregated_values']['upsampled_timestamps'][t]:
                data[cluster][trace]['aggregated_values']['pcap'] = data[cluster][trace]['aggregated_values'][
                    'pcap'].append({'pcap': math.nan,
                                    'timestamp': data[cluster][trace]['aggregated_values']['upsampled_timestamps'][
                                        t]}, ignore_index=True)
            elif (data[cluster][trace]['enforce_powercap'].index[-1] - data[cluster][trace]['first_sensor_point']) < \
                    data[cluster][trace]['aggregated_values']['upsampled_timestamps'][t]:
                data[cluster][trace]['aggregated_values']['pcap'] = data[cluster][trace]['aggregated_values'][
                    'pcap'].append({'pcap': int(data[cluster][trace]['enforce_powercap']['powercap'].iloc[-1]),
                                    'timestamp': data[cluster][trace]['aggregated_values']['upsampled_timestamps'][
                                        t]}, ignore_index=True)
            else:
                data[cluster][trace]['aggregated_values']['pcap'] = data[cluster][trace]['aggregated_values'][
                    'pcap'].append({'pcap': int(data[cluster][trace]['enforce_powercap']['powercap'].iloc[idx - 1]),
                                    'timestamp': data[cluster][trace]['aggregated_values']['upsampled_timestamps'][
                                        t]}, ignore_index=True)
    data[cluster][trace]['aggregated_values']['pcap'] = data[cluster][trace]['aggregated_values']['pcap'].set_index(
        'timestamp')
    if (experiment_type == 'preliminaries') or (experiment_type == 'static_characteristic'):
        data[cluster][trace]['aggregated_values']['pcap'] = pd.DataFrame(
            {'pcap': int(data[cluster][trace]['parameters']['powercap']),
             'timestamp': data[cluster][trace]['aggregated_values']['upsampled_timestamps'][0]}, index=[0])
        for t in range(1, len(data[cluster][trace]['aggregated_values']['upsampled_timestamps'])):
            data[cluster][trace]['aggregated_values']['pcap'] = data[cluster][trace]['aggregated_values'][
                'pcap'].append({'pcap': int(data[cluster][trace]['parameters']['powercap']),
                                'timestamp': data[cluster][trace]['aggregated_values']['upsampled_timestamps'][t]},
                               ignore_index=True)
        data[cluster][trace]['aggregated_values']['pcap'] = data[cluster][trace]['aggregated_values'][
            'pcap'].set_index('timestamp')
    data[cluster][trace]['aggregated_values']['progress_frequency_median'] = \
    data[cluster][trace]['aggregated_values']['progress_frequency_median'].set_index('timestamp')


# for my_trace in traces[cluster][0]:
#     x_zoom = [0,
#               100]  # [0,len(data[cluster][my_trace]['aggregated_values']['progress_frequency_median']['median'])]
#     fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(5.7, 6.6))
#     data[cluster][my_trace]['aggregated_values']['progress_frequency_median']['median'].plot(color='k', ax=axes[0],
#                                                                                              marker='o',
#                                                                                              markersize=3,
#                                                                                              linestyle='')
#     axes[0].set_ylabel('Progress [Hz]')
#     axes[0].set_xlabel('')
#     axes[0].legend(['Measure', 'Objective value', 'Objective value ±5%'], fontsize='small')
#     axes[0].set_xlim(x_zoom)
#     axes[0].grid(True)
#     data[cluster][my_trace]['aggregated_values']['pcap'].plot(color='k', ax=axes[1],
#                                                               style=".")  # , style="+",  markersize=4)
#     data[cluster][my_trace]['rapl_sensors']['value0'].plot(color='lightcoral', ax=axes[1], marker="+",
#                                                            linestyle='')  # , style="+",  markersize=4)
#     data[cluster][my_trace]['rapl_sensors']['value1'].plot(color='lightcoral', ax=axes[1], marker="+", linestyle='')
#     data[cluster][my_trace]['rapl_sensors']['value2'].plot(color='lightcoral', ax=axes[1], marker="+",
#                                                            linestyle='')  # , style="+",  markersize=4)
#     data[cluster][my_trace]['rapl_sensors']['value3'].plot(color='lightcoral', ax=axes[1], marker="+",
#                                                            linestyle='')  # , style="+",  markersize=4)
#     axes[1].set_ylabel('Power [W]')
#     axes[1].set_xlabel('Time [s]')
#     axes[1].legend(['Powercap', 'Measure'], fontsize='small', ncol=1)  # ,'Measure - package1'
#     axes[1].grid(True)
#     axes[1].set_xlim(x_zoom)


pmin = 40
pmax = 120
power_parameters0 = [1, 0]

# Reshaping data:
prequestedvsmeasured = {}
prequestedvsmeasured[cluster] = pd.DataFrame()
# prequestedvsmeasured[cluster]['requested_pcap'] = [
#     data[cluster][trace]['parameters']['config-file']['actions'][0]['args'][0] for trace in traces[cluster][0]]
prequestedvsmeasured[cluster]['0'] = [data[cluster][trace]['aggregated_values']['rapl0'] for trace in
                                      traces[cluster][0]]
prequestedvsmeasured[cluster]['1'] = [data[cluster][trace]['aggregated_values']['rapl1'] for trace in
                                      traces[cluster][0]]
prequestedvsmeasured[cluster]['2'] = [data[cluster][trace]['aggregated_values']['rapl2'] for trace in
                                      traces[cluster][0]]
prequestedvsmeasured[cluster]['3'] = [data[cluster][trace]['aggregated_values']['rapl3'] for trace in
                                      traces[cluster][0]]
prequestedvsmeasured[cluster]['rapls'] = [data[cluster][trace]['aggregated_values']['rapls'] for trace in
                                          traces[cluster][0]]
# prequestedvsmeasured[cluster]['pcap_requested'] = prequestedvsmeasured[cluster]['requested_pcap']
# prequestedvsmeasured[cluster] = prequestedvsmeasured[cluster].set_index('requested_pcap')
prequestedvsmeasured[cluster].sort_index(inplace=True)


# Powercap to Power measure model:
def powermodel(power_requested, slope, offset):
    return slope * power_requested + offset


# Optimizing power model parameters
power_model_data = {}
power_model = {}
power_parameters = {}
r_squared_power_actuator = {}
# optimized params
# power_parameters[cluster], power_parameters_cov = opt.curve_fit(powermodel,
#                                                                 prequestedvsmeasured[cluster]['pcap_requested'],
#                                                                 prequestedvsmeasured[cluster]['rapls'],
#                                                                 p0=power_parameters0)  # /!\ model computed with package 0
# Model
# power_model[cluster] = powermodel(prequestedvsmeasured[cluster]['pcap_requested'].loc[pmin:pmax],
#                                   power_parameters[cluster][0],
#                                   power_parameters[cluster][1])  # model with fixed alpha

# Getting K_L, alpha, beta
sc = {}
sc_requested = {}
pcap2perf_model = {}
power2perf_params = {}

elected_performance_sensor = 'progress_frequency_median'  # choose between: 'average_performance_periods' 'average_progress_count' 'average_performance_frequency'
sc[cluster] = pd.DataFrame(
    [data[cluster][trace]['aggregated_values'][elected_performance_sensor]['median'].mean() for trace in
     traces[cluster][0]],
    index=[data[cluster][trace]['aggregated_values']['rapls'] for trace in traces[cluster][0]],
    columns=[elected_performance_sensor])
sc[cluster].sort_index(inplace=True)
# sc_requested[cluster] = pd.DataFrame(
#     [data[cluster][trace]['aggregated_values'][elected_performance_sensor]['median'].mean() for trace in
#      traces[cluster][0]],
#     index=[data[cluster][trace]['parameters']['config-file']['actions'][0]['args'][0] for trace in
#            traces[cluster][0]], columns=[elected_performance_sensor])
# sc_requested[cluster].sort_index(inplace=True)


def power2perf(power, alpha, perf_inf, power_0):  # general model formulation
    return perf_inf * (1 - np.exp(-alpha * (power - power_0)))


def pcap2perf(pcap, a, b, perf_inf, alpha, power_0):  # general model formulation
    return perf_inf * (1 - np.exp(-alpha * (a * pcap + b - power_0)))


# Model optimisation
# init param
# power2perf_param0 = [0.04, (sc[cluster].at[sc[cluster].index[-1], elected_performance_sensor] + sc[cluster].at[
#     sc[cluster].index[-2], elected_performance_sensor] + sc[cluster].at[
#                                 sc[cluster].index[-3], elected_performance_sensor]) / 3,
#                      min(sc[cluster].index)]  # guessed params
# # Optimization
# power2perf_param_opt, power2perf_param_cov = opt.curve_fit(power2perf, sc[cluster].index,
#                                                            sc[cluster][elected_performance_sensor],
#                                                            p0=power2perf_param0)
# power2perf_params[cluster] = power2perf_param_opt
# # Model
# pcap2perf_model[cluster] = pcap2perf(sc_requested[cluster].index, power_parameters[cluster][0],
#                                      power_parameters[cluster][1], power2perf_params[cluster][1],
#                                      power2perf_params[cluster][0],
#                                      power2perf_params[cluster][2])  # model with optimized perfinf









plotted_traces = {
    'gros': 'preliminaries_stream_c_2021-02-16T17:54:40+01:00',
    'dahu': 'preliminaries_stream_c_2021-02-17T11:45:24+01:00',
    'yeti': 'preliminaries_stream_c_2021-02-17T14:38:27+01:00',
}

# Parameters found using static Characteristic
a = {'gros': 0.83, 'dahu': 0.94, 'yeti': 0.89}
b = {'gros': 7.07, 'dahu': 0.17, 'yeti': 2.91}
alpha = {'gros': 0.047, 'dahu': 0.032, 'yeti': 0.023}
beta = {'gros': 28.5, 'dahu': 34.8, 'yeti': 33.7}
K_L = {'gros': 25.6, 'dahu': 42.4, 'yeti': 78.5}
# analytically found parameter
tau = 0.33

# Computing model predictions
for my_trace in traces[cluster][0]:
    data[cluster][my_trace]['aggregated_values']['progress_model'] = pd.DataFrame({'progress_model': K_L[
                                                                                                         cluster] * (
                                                                                                                 1 + -np.exp(
                                                                                                             -alpha[
                                                                                                                 cluster] * (
                                                                                                                         a[
                                                                                                                             cluster] *
                                                                                                                         data[
                                                                                                                             cluster][
                                                                                                                             my_trace][
                                                                                                                             'aggregated_values'][
                                                                                                                             'pcap'].iloc[
                                                                                                                             0] +
                                                                                                                         b[
                                                                                                                             cluster] -
                                                                                                                         beta[
                                                                                                                             cluster]))),
                                                                                   'timestamp':
                                                                                       data[cluster][my_trace][
                                                                                           'aggregated_values'][
                                                                                           'upsampled_timestamps'][
                                                                                           0]}, index=[0])
    data[cluster][my_trace]['aggregated_values']['progress_model'] = data[cluster][my_trace]['aggregated_values'][
        'progress_model'].append({'progress_model': K_L[cluster] * (1 + -np.exp(-alpha[cluster] * (
                a[cluster] * data[cluster][my_trace]['aggregated_values']['pcap'].iloc[1][0] + b[cluster] - beta[
            cluster]))), 'timestamp': data[cluster][my_trace]['aggregated_values']['upsampled_timestamps'][1]},
                                 ignore_index=True)
    for t in range(2, len(data[cluster][my_trace]['aggregated_values']['upsampled_timestamps'])):
        pcap_old_L = -np.exp(-alpha[cluster] * (
                    a[cluster] * data[cluster][my_trace]['aggregated_values']['pcap'].iloc[t - 1] + b[cluster] -
                    beta[cluster]))
        T_S = data[cluster][my_trace]['aggregated_values']['upsampled_timestamps'][t] - \
              data[cluster][my_trace]['aggregated_values']['upsampled_timestamps'][t - 1]
        data[cluster][my_trace]['aggregated_values']['progress_model'] = \
        data[cluster][my_trace]['aggregated_values']['progress_model'].append({'progress_model': K_L[
                                                                                                     cluster] * T_S / (
                                                                                                             T_S + tau) *
                                                                                                 pcap_old_L[
                                                                                                     0] + tau / (
                                                                                                             T_S + tau) * (
                                                                                                             data[
                                                                                                                 cluster][
                                                                                                                 my_trace][
                                                                                                                 'aggregated_values'][
                                                                                                                 'progress_model'][
                                                                                                                 'progress_model'].iloc[
                                                                                                                 -1] -
                                                                                                             K_L[
                                                                                                                 cluster]) +
                                                                                                 K_L[cluster],
                                                                               'timestamp': data[cluster][my_trace][
                                                                                   'aggregated_values'][
                                                                                   'upsampled_timestamps'][t]},
                                                                              ignore_index=True)
    data[cluster][my_trace]['aggregated_values']['progress_model'] = data[cluster][my_trace]['aggregated_values'][
        'progress_model'].set_index('timestamp')



# Computing modeling error
model_error = pd.DataFrame({'cluster': 'gros', 'Modeling error [Hz]': 0}, index=[0])
for trace in traces[cluster][0]:
    for idx in data[cluster][trace]['aggregated_values']['progress_frequency_median']['median'].index:
        model_error = model_error.append({'cluster': cluster, 'Modeling error [Hz]':
            data[cluster][trace]['aggregated_values']['progress_frequency_median']['median'][idx] -
            data[cluster][trace]['aggregated_values']['progress_model']['progress_model'][idx]}, ignore_index=True)

# # Extra plot
# plt.rcParams.update({'font.size': 14})
# fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(6.6, 4))
# sns.violinplot(y=model_error['cluster'], x=model_error['Modeling error [Hz]'], palette="Pastel1", scale="count")
# axes.axvline(x=0, color='tab:red', linestyle='-', linewidth=1)
# axes.grid(True)

# =============================================================================
# CONTROLLER
# =============================================================================

pmin = 40
pmax = 120

# FIGURE 6a
cluster = 'gros'
my_trace = 'preliminaries_stream_c_2021-02-16T17:54:40+01:00'
x_zoom = [0, len(data[cluster][my_trace]['aggregated_values']['progress_frequency_median']['median'])]
fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(5.7, 6.6))
data[cluster][my_trace]['aggregated_values']['progress_frequency_median']['median'].plot(color='k', ax=axes[0],
                                                                                         marker='o', markersize=3,
                                                                                         linestyle='')
setpoint = data[cluster][my_trace]['parameters']['config-file']['model']['gain'] * (1 - np.exp(
    - data[cluster][my_trace]['parameters']['config-file']['model']['alpha'] * (
                data[cluster][my_trace]['parameters']['config-file']['rapl']['slope'] * pmax +
                data[cluster][my_trace]['parameters']['config-file']['rapl']['offset'] -
                data[cluster][my_trace]['parameters']['config-file']['model']['beta']))) * \
           data[cluster][my_trace]['parameters']['config-file']['controller'][
               'setpoint']  # for index in data[cluster][trace]['aggregated_values']['progress_frequency_median']['median'].index]
axes[0].axhline(y=setpoint, color='skyblue', linestyle='-')
axes[0].set_ylabel('Progress [Hz]')
axes[0].set_xlabel('')
axes[0].legend(['Measure', 'Objective value', 'Objective value ±5%'], fontsize='small')
axes[0].set_xlim(x_zoom)
axes[0].grid(True)
data[cluster][my_trace]['aggregated_values']['pcap'].plot(color='k', ax=axes[1],
                                                          style=".")  # , style="+",  markersize=4)
data[cluster][my_trace]['rapl_sensors']['value0'].plot(color='lightcoral', ax=axes[1], marker="+",
                                                       linestyle='')  # , style="+",  markersize=4)
data[cluster][my_trace]['rapl_sensors']['value1'].plot(color='lightcoral', ax=axes[1], marker="+", linestyle='')
data[cluster][my_trace]['rapl_sensors']['value2'].plot(color='lightcoral', ax=axes[1], marker="+",
                                                       linestyle='')  # , style="+",  markersize=4)
data[cluster][my_trace]['rapl_sensors']['value3'].plot(color='lightcoral', ax=axes[1], marker="+",
                                                       linestyle='')  # , style="+",  markersize=4)
axes[1].set_ylabel('Power [W]')
axes[1].set_xlabel('Time [s]')
axes[1].legend(['Powercap', 'Measure'], fontsize='small', ncol=1)  # ,'Measure - package1'
axes[1].grid(True)
axes[1].set_xlim(x_zoom)

# # Computing error between measured progress and setpoint
# control_error = pd.DataFrame({'cluster': 'gros', 'Tracking error [Hz]': 0}, index=[0])
# for trace in traces[cluster][0]:
#     progress_objective = data[cluster][trace]['parameters']['config-file']['model']['gain'] * (1 - np.exp(
#         - data[cluster][trace]['parameters']['config-file']['model']['alpha'] * (
#                     data[cluster][trace]['parameters']['config-file']['rapl']['slope'] * pmax +
#                     data[cluster][trace]['parameters']['config-file']['rapl']['offset'] -
#                     data[cluster][trace]['parameters']['config-file']['model']['beta']))) * \
#                          data[cluster][trace]['parameters']['config-file']['controller']['setpoint']
#     for idx in data[cluster][trace]['aggregated_values']['progress_frequency_median']['median'].index:
#         control_error = control_error.append({'cluster': cluster, 'Tracking error [Hz]': progress_objective -
#                                                                                          data[cluster][trace][
#                                                                                              'aggregated_values'][
#                                                                                              'progress_frequency_median'][
#                                                                                              'median'][idx]},
#                                              ignore_index=True)

# # FIGURE 6b
# plt.rcParams.update({'font.size': 14})
# fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(6.6, 4))
# sns.violinplot(y=control_error['cluster'], x=control_error['Tracking error [Hz]'], palette="Pastel1", scale="count")
# axes.grid(True)
# axes.set_xlabel('Tacking Error [Hz]')
# axes.axvline(x=0, color='tab:red', linestyle='-', linewidth=1)
# # axes.set_xlim([-40,70])



plt.show()
