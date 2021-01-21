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
#import control as ctl
import yaml
import pickle
import math


# Getting the right paths
experiment_date = '2020-11-20' # ex: '2020-11-20' TO UPDATE
experiment_dir = os.getcwd()+'/Documents/working-documents/data/hnrm-experiments-master-g5k-data-'+experiment_date+'_preliminaries/g5k/data/'+experiment_date+'_preliminaries/'
clusters = next(os.walk(experiment_dir))[1]
traces = pd.DataFrame()
for cluster in clusters:
    traces[cluster] = next(os.walk(experiment_dir+cluster))[1] 

# Extracting experitments data 
data = {}
for cluster in clusters:
    data[cluster] = {}
    for trace in traces[cluster]:
        data[cluster][trace] = {}
        # Initial trace parameters
        folder_path = experiment_dir+cluster+'/'+trace
        with open(folder_path+"/parameters.yaml") as file:
            data[cluster][trace]['parameters'] = yaml.load(file, Loader=yaml.FullLoader)
        # Loading sensors data files
        pubMeasurements = pd.read_csv(folder_path+"/dump_pubMeasurements.csv")
        pubProgress = pd.read_csv(folder_path+"/dump_pubProgress.csv")
        # Checking if msg.timestamp == sensor.timestamps
        data[cluster][trace]['timestamp_check'] = True
        for i, row in pubMeasurements.iterrows():
            if pubMeasurements['msg.timestamp'][i] != pubMeasurements['sensor.timestamp'][i]:
                print('Message and sensor timestamps are different! Cluster '+cluster+', trace '+trace+', at index '+str(i))
                data[cluster][trace]['timestamp_check'] = False
        # Extracting sensor data
        rapl_sensor0 = rapl_sensor1 = rapl_sensor2 = rapl_sensor3 = downstream_sensor = pd.DataFrame({'timestamp':[],'value':[]})
        for i, row in pubMeasurements.iterrows():
            #if 'RaplKey (PackageID ' in row['sensor.id']:
             #   if len(rapl_sensors['timestamp']) != 0 and rapl_sensors['timestamp'][-1] ==  row['sensor.timestamp']:
                #    rapl_sensors['value'+row['sensor.id'][-2]][-1] = row['sensor.value']
              #  else:
                #    rapl_sensors = rapl_sensors.append({'timestamp':row['sensor.timestamp'],'value'+row['sensor.id'][-2]:row['sensor.value']}, ignore_index=True)
                    #rapl_sensors['value'+row['sensor.id'][-2]] = row['sensor.value'] 
            if row['sensor.id'] == 'RaplKey (PackageID 0)':
                rapl_sensor0 = rapl_sensor0.append({'timestamp':row['sensor.timestamp'],'value':row['sensor.value']}, ignore_index=True)
            elif row['sensor.id'] == 'RaplKey (PackageID 1)':
                rapl_sensor1 = rapl_sensor1.append({'timestamp':row['sensor.timestamp'],'value':row['sensor.value']}, ignore_index=True)
            elif row['sensor.id'] == 'RaplKey (PackageID 2)':
                rapl_sensor2 = rapl_sensor1.append({'timestamp':row['sensor.timestamp'],'value':row['sensor.value']}, ignore_index=True)
            elif row['sensor.id'] == 'RaplKey (PackageID 3)':
                rapl_sensor3 = rapl_sensor1.append({'timestamp':row['sensor.timestamp'],'value':row['sensor.value']}, ignore_index=True)
            else:
                downstream_sensor = downstream_sensor.append({'timestamp':row['sensor.timestamp'],'value':row['sensor.value']}, ignore_index=True)
        progress_sensor = pd.DataFrame({'timestamp':pubProgress['msg.timestamp'],'value':pubProgress['sensor.value']})
        # Checking if pubMeasurements downstream timestamp == process timestamps
        data[cluster][trace]['timestamp_check_measvspro'] = True
        for i, row in progress_sensor.iterrows():
            if progress_sensor['timestamp'][i] != downstream_sensor['timestamp'][i]:
                print('Progress and downstream timestamps are different! at index Cluster '+cluster+', trace '+trace+', at index '+str(i))
                data[cluster][trace]['timestamp_check_measvspro'] = False
        # Checking if pubMeasurements downstream timestamp is longer than process timestamps
        data[cluster][trace]['is_measurementstimestamp_longer_than_progresstimestamp'] = False
        if len(progress_sensor['timestamp']) < len(downstream_sensor['timestamp']):
            #print('More downstream measures than progress!')
            data[cluster][trace]['is_measurementstimestamp_longer_than_progresstimestamp'] = True
            downstream_sensor = downstream_sensor[0:len(progress_sensor)] ####### /!\ one data sample is removed !!!
        # Writing in data dict
        data[cluster][trace]['rapl_sensors'] = pd.DataFrame({'timestamp':rapl_sensor0['timestamp'],'value0':rapl_sensor0['value'],'value1':rapl_sensor1['value'],'value2':rapl_sensor2['value'],'value3':rapl_sensor3['value']})
        data[cluster][trace]['performance_sensors'] = pd.DataFrame({'timestamp':progress_sensor['timestamp'],'downstream':downstream_sensor['value'],'progress':progress_sensor['value']})
        # Indexing on elasped time since the first data point
        data[cluster][trace]['first_sensor_point'] = min(data[cluster][trace]['rapl_sensors']['timestamp'][0], data[cluster][trace]['performance_sensors']['timestamp'][0])
        data[cluster][trace]['rapl_sensors']['elapsed_time'] = (data[cluster][trace]['rapl_sensors']['timestamp'] - data[cluster][trace]['first_sensor_point'])/10**6
        data[cluster][trace]['rapl_sensors'] = data[cluster][trace]['rapl_sensors'].set_index('elapsed_time')
        data[cluster][trace]['performance_sensors']['elapsed_time'] = (data[cluster][trace]['performance_sensors']['timestamp'] - data[cluster][trace]['first_sensor_point'])/10**6
        data[cluster][trace]['performance_sensors'] = data[cluster][trace]['performance_sensors'].set_index('elapsed_time')

# Averaging
for cluster in clusters:
    for trace in traces[cluster]:
        # Average sensors value
        avg0 = data[cluster][trace]['rapl_sensors']['value0'].mean()
        avg1 = data[cluster][trace]['rapl_sensors']['value1'].mean()
        avg2 = data[cluster][trace]['rapl_sensors']['value2'].mean()
        avg3 = data[cluster][trace]['rapl_sensors']['value3'].mean()
        data[cluster][trace]['aggregated_values'] = {'rapl0':avg0,'rapl1':avg1,'rapl2':avg2,'rapl3':avg3,'downstream':data[cluster][trace]['performance_sensors']['downstream'].mean(),'progress':data[cluster][trace]['performance_sensors']['progress']}
        avgs = pd.DataFrame({'averages':[avg0, avg1, avg2, avg3]})
        data[cluster][trace]['aggregated_values']['rapls'] = avgs.mean()[0]
        # Sensors periods
            # Raplcluster = 'gros'
        rapl_elapsed_time = data[cluster][trace]['rapl_sensors'].index
        data[cluster][trace]['aggregated_values']['rapls_periods'] = pd.DataFrame([rapl_elapsed_time[t]-rapl_elapsed_time[t-1] for t in range(1,len(rapl_elapsed_time))], index=[rapl_elapsed_time[t] for t in range(1,len(rapl_elapsed_time))], columns=['periods'])
        data[cluster][trace]['aggregated_values']['average_rapls_periods'] = data[cluster][trace]['aggregated_values']['rapls_periods'].mean()[0]
            # Progress
        performance_elapsed_time = data[cluster][trace]['performance_sensors'].index
        data[cluster][trace]['aggregated_values']['performance_periods'] = pd.DataFrame([performance_elapsed_time[t]-performance_elapsed_time[t-1] for t in range(1,len(performance_elapsed_time))], index=[performance_elapsed_time[t] for t in range(1,len(performance_elapsed_time))], columns=['periods'])
        data[cluster][trace]['aggregated_values']['average_performance_periods'] = data[cluster][trace]['aggregated_values']['performance_periods'].mean()[0]
        # Execution time:
        data[cluster][trace]['aggregated_values']['execution_time'] = performance_elapsed_time[-1]
        # Sensor value count (at rapl sensor frequency) :
        data[cluster][trace]['aggregated_values']['progress_count'] = pd.DataFrame({'count':sum(data[cluster][trace]['performance_sensors']['progress'].where(data[cluster][trace]['performance_sensors'].index<= data[cluster][trace]['rapl_sensors'].index[0],0)),'timestamp':data[cluster][trace]['rapl_sensors'].index[0]}, index=[0])
        for t in range(1,len(data[cluster][trace]['rapl_sensors'].index)):
             data[cluster][trace]['aggregated_values']['progress_count'] = data[cluster][trace]['aggregated_values']['progress_count'].append({'count':sum(data[cluster][trace]['performance_sensors']['progress'].where((data[cluster][trace]['performance_sensors'].index>= data[cluster][trace]['rapl_sensors'].index[t-1]) & (data[cluster][trace]['performance_sensors'].index <=data[cluster][trace]['rapl_sensors'].index[t]),0)),'timestamp':t}, ignore_index=True)
        data[cluster][trace]['aggregated_values']['progress_count'] = data[cluster][trace]['aggregated_values']['progress_count'].set_index('timestamp')
        data[cluster][trace]['aggregated_values']['average_progress_count'] = data[cluster][trace]['aggregated_values']['progress_count'].mean()[0]

# Save
def save_obj(obj, name ):
    with open(os.getcwd()+'/Documents/working-documents/data/'+ name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL) 
#save_obj(data,experiment_date)

# Load 
def load_obj(name ):
    with open(os.getcwd()+'/Documents/working-documents/data/' + name + '.pkl', 'rb') as f:
        return pickle.load(f)
#data = load_obj(experiment_date)


# PLOTS SECTION
clusters_styles = {clusters[0]:'peru',clusters[1]:'forestgreen',clusters[2]:'cornflowerblue'}
TDP = {'yeti':125,'dahu':125,'gros':125} # thermal dissipation power, in W

# PLOT: Signals over time, visualization 
    # Choose a cluster and a trance
cluster = 'dahu'
asked_pcap = 80
for trace in traces[cluster]:
    if asked_pcap == data[cluster][trace]['parameters']['powercap']:
        my_trace = trace
#my_traces = [traces[cluster][3], traces[cluster][7], traces[cluster][8]]

    # plot
fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(6.6,6.6))
fig.suptitle(data[cluster][my_trace]['parameters']['benchmark']+', Pcap='+str(data[cluster][my_trace]['parameters']['powercap'])+'W')
#for my_trace in my_traces:
#data[cluster][my_trace]['performance_sensors']['downstream'].plot(color='cornflowerblue',ax=axes[0], style=".", markersize=2)
data[cluster][trace]['aggregated_values']['performance_periods'].plot(color='cornflowerblue',ax=axes[0], style=".", markersize=2)
axes[0].set_ylabel('pubprogress periods (s)')
axes[0].grid(True)
#for my_trace in my_traces:
axes[1].axhline(y=data[cluster][my_trace]['parameters']['powercap'], color='lightcoral', linestyle='-')
data[cluster][my_trace]['rapl_sensors']['value0'].plot(color='forestgreen',ax=axes[1], style=".")#, style="+",  markersize=4)
data[cluster][my_trace]['rapl_sensors']['value1'].plot(color='limegreen',ax=axes[1], style=".")#, style="+",  markersize=4)
data[cluster][my_trace]['rapl_sensors']['value2'].plot(color='darkolivegreen',ax=axes[1], style="-")#, style="+",  markersize=4)
data[cluster][my_trace]['rapl_sensors']['value3'].plot(color='lightgreen',ax=axes[1], style="-")#, style="+",  markersize=4)
axes[1].set_ylabel('Power (in W)')
axes[1].legend(['asked_powercap','rapl_sensors per package'],fontsize='small',ncol=1)
axes[1].grid(True)
axes[1].set_ylim([0,155])
#for my_trace in my_traces:
#data[cluster][my_trace]['performance_sensors']['progress'].plot(color='goldenrod',ax=axes[2], style=".", markersize=2)
#data[cluster][trace]['aggregated_values']['performance_periods'].plot(color='goldenrod',ax=axes[2], style=".", markersize=2)
data[cluster][my_trace]['aggregated_values']['progress_count'].plot(color='goldenrod',ax=axes[2], style=".", markersize=3)
axes[2].set_ylabel('pubProgress count')
axes[2].grid(True)

plt.savefig(os.getcwd()+'/Documents/working-documents/figures/'+experiment_date+'/periods_rapls_count_vs_time_'+cluster+'-'+str(data[cluster][my_trace]['parameters']['powercap'])+'W.pdf')

# PLOT: Actuator: In average: Power asked vs. power measured
paskedvsmeasured = {}
for cluster in clusters:
    paskedvsmeasured[cluster] = pd.DataFrame()
    paskedvsmeasured[cluster]['asked_pcap'] = [data[cluster][trace]['parameters']['powercap'] for trace in traces[cluster]]
    paskedvsmeasured[cluster]['0'] = [data[cluster][trace]['aggregated_values']['rapl0'] for trace in traces[cluster]]
    paskedvsmeasured[cluster]['1'] = [data[cluster][trace]['aggregated_values']['rapl1'] for trace in traces[cluster]]
    paskedvsmeasured[cluster]['2'] = [data[cluster][trace]['aggregated_values']['rapl2'] for trace in traces[cluster]]
    paskedvsmeasured[cluster]['3'] = [data[cluster][trace]['aggregated_values']['rapl3'] for trace in traces[cluster]]
    paskedvsmeasured[cluster]['pcap_asked'] = paskedvsmeasured[cluster]['asked_pcap']
    paskedvsmeasured[cluster] = paskedvsmeasured[cluster].set_index('asked_pcap')
    
for cluster in clusters:
    fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(6.6,6.6))
    fig.suptitle('Power asked vs. measured - Cluster: '+cluster)
    paskedvsmeasured[cluster]['0'].plot(color=clusters_styles[cluster],style="P")
    paskedvsmeasured[cluster]['1'].plot(color=clusters_styles[cluster],marker="X",linestyle='')
    paskedvsmeasured[cluster]['2'].plot(color=clusters_styles[cluster],marker="o",linestyle='')
    paskedvsmeasured[cluster]['3'].plot(color=clusters_styles[cluster],marker="d",linestyle='')
    axes.axhline(y=TDP[cluster], color='lightcoral', linestyle='-')
    paskedvsmeasured[cluster]['pcap_asked'].plot(color='grey', linewidth=0.5)
    axes.grid(True)
    axes.set_ylabel('Measured Power (in W)')
    axes.set_xlabel('Asked Power (in W)')
    axes.legend(['Package 0','Package 1','Package 2','Package 3','TDP'],fontsize='small',loc='upper left',ncol=1)
    fig.gca().set_aspect('equal', adjustable='box')
    
    plt.savefig(os.getcwd()+'/Documents/working-documents/figures/'+experiment_date+'/asked_pcap_vs_rapls_'+cluster+'.pdf')

# PLOT: Actuator: Through time
asked_pcaps = [30, 90, 140]
selected_traces = {}
for cluster in clusters:
    selected_traces[cluster] = {}
    for asked_pcap in asked_pcaps:
        for trace in traces[cluster]:
            if asked_pcap == data[cluster][trace]['parameters']['powercap']:
                selected_traces[cluster][asked_pcap] = trace
    # plot
colors_pcaps={asked_pcaps[0]:'crimson',asked_pcaps[1]:'orange',asked_pcaps[2]:'dodgerblue'}
for cluster in clusters:
    fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(6.6,6.6))
    fig.suptitle('Cluster: '+cluster)
    for asked_pcap in asked_pcaps:
        axes.axhline(y=data[cluster][selected_traces[cluster][asked_pcap]]['parameters']['powercap'], color=colors_pcaps[asked_pcap], linestyle='-')
        data[cluster][selected_traces[cluster][asked_pcap]]['rapl_sensors']['value0'].plot(color=colors_pcaps[asked_pcap],ax=axes, marker="+", linestyle='')
        data[cluster][selected_traces[cluster][asked_pcap]]['rapl_sensors']['value1'].plot(color=colors_pcaps[asked_pcap],ax=axes, marker="x", linestyle='')
        data[cluster][selected_traces[cluster][asked_pcap]]['rapl_sensors']['value2'].plot(color=colors_pcaps[asked_pcap],ax=axes, marker="1", linestyle='')
        data[cluster][selected_traces[cluster][asked_pcap]]['rapl_sensors']['value3'].plot(color=colors_pcaps[asked_pcap],ax=axes, marker="2", linestyle='')
    axes.set_ylabel('Power (in W)')
    axes.legend(['asked_powercap','rapl_sensors per package'],fontsize='small',loc='upper center',ncol=1)
    axes.grid(True)
    axes.set_ylim([0,155])
    
    plt.savefig(os.getcwd()+'/Documents/working-documents/figures/'+experiment_date+'/rapls_actuator_through_time'+cluster+'-'+str(asked_pcaps)+'W.pdf')
    
# PLOT: Static Characteristic
sc = {}
sc_asked = {}
powermodel = {}
alpha = 0.04 # to find automatically
elected_performance_sensor = 'average_progress_count' # choose between: 'average_performance_periods' 'average_progress_count'
for cluster in clusters:
    sc[cluster] = pd.DataFrame([data[cluster][trace]['aggregated_values'][elected_performance_sensor] for trace in traces[cluster]], index=[data[cluster][trace]['aggregated_values']['rapls'] for trace in traces[cluster]], columns=[elected_performance_sensor])
    sc[cluster].sort_index(inplace=True)
    sc_asked[cluster] = pd.DataFrame([data[cluster][trace]['aggregated_values'][elected_performance_sensor] for trace in traces[cluster]], index=[data[cluster][trace]['parameters']['powercap'] for trace in traces[cluster]], columns=[elected_performance_sensor])
    sc_asked[cluster].sort_index(inplace=True)
    #powermodel[cluster] = [sc[cluster].at[max(sc[cluster].index),elected_performance_sensor]*(1-math.exp(-alpha*(i-min(sc[cluster].index)))) for i in sc[cluster].index] # final value:supposed to be known ?
    powermodel[cluster] = [(sc[cluster].at[sc[cluster].index[-1],elected_performance_sensor]+sc[cluster].at[sc[cluster].index[-2],elected_performance_sensor]+sc[cluster].at[sc[cluster].index[-3],elected_performance_sensor])/3*(1-math.exp(-alpha*(i-min(sc[cluster].index)))) for i in sc[cluster].index] # mean over last 3 values:  supposed to be known ?

fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(6.6,6.6))
fig.suptitle('Static Characteristic - Performance vs Measured and Asked Power')
for cluster in clusters:
    sc[cluster][elected_performance_sensor].plot(color=clusters_styles[cluster],marker="x")
    sc_asked[cluster][elected_performance_sensor].plot(color=clusters_styles[cluster],marker="o",linestyle=':')
    plt.plot(sc[cluster].index,powermodel[cluster],color=clusters_styles[cluster])
axes.grid(True)
axes.set_ylabel('Performance ('+elected_performance_sensor+')')
axes.set_xlabel('Power (in W)')
#axes.set_yscale('log')
#axes.set_xscale('log')
legend = []
for cluster in clusters:
    legend += [cluster+' - measured']
    legend += [cluster+' - asked']
axes.legend(legend,fontsize='small',loc='upper center',ncol=1)

#plt.savefig(os.getcwd()+'/Documents/working-documents/figures/'+experiment_date+'/SC_'+elected_performance_sensor+'vs_rapls_asked_pcap_with_model_alpha'+str(alpha)+'.pdf')

# PLOT: Execution time vs. power
exec_time_power = {}
exec_time_power_asked = {}
for cluster in clusters:
    exec_time_power[cluster] = pd.DataFrame([data[cluster][trace]['aggregated_values']['execution_time'] for trace in traces[cluster]], index=[data[cluster][trace]['aggregated_values']['rapls'] for trace in traces[cluster]], columns=['execution_time'])
    exec_time_power[cluster].sort_index(inplace=True)
    exec_time_power_asked[cluster] = pd.DataFrame([data[cluster][trace]['aggregated_values']['execution_time'] for trace in traces[cluster]], index=[data[cluster][trace]['parameters']['powercap'] for trace in traces[cluster]], columns=['execution_time'])
    exec_time_power_asked[cluster].sort_index(inplace=True)

fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(6.6,6.6))
fig.suptitle('Execution time vs Measured and Asked Power')
for cluster in clusters:
    exec_time_power[cluster]['execution_time'].plot(color=clusters_styles[cluster],marker="x")
    exec_time_power_asked[cluster]['execution_time'].plot(color=clusters_styles[cluster],marker="o",linestyle=':')
axes.grid(True)
axes.set_ylabel('Execution Time (in s)')
#axes.set_yscale('log')
axes.set_xlabel('Power (in W)')
legend = []
for cluster in clusters:
    legend += [cluster+' - measured']
    legend += [cluster+' - asked']
axes.legend(legend,fontsize='small',loc='upper right',ncol=1)

plt.savefig(os.getcwd()+'/Documents/working-documents/figures/'+experiment_date+'/execution time_vs_rapls_asked_pcap.pdf')

# Identification
# https://python-control.readthedocs.io/en/0.8.3/index.html
#rsys = ctl.era(YY, m, n, nin, nout, r)
#ctl.frd(d, w)
# https://control-toolbox.readthedocs.io/en/latest/index.html#
#ctl.SystemIdentification(path_x, path_x_dot, path_y)
#ctl.fit(num_epochs=500)
#ctl.model()
# https://web.math.princeton.edu/~cwrowley/python-control/index.html
# git clone https://github.com/python-control/python-control.git
