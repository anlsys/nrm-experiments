#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 19 09:27:26 2020

@author: sophiecerf
"""

# =============================================================================
# Libraries
# ============================================================================= 
import os
import pandas as pd
import matplotlib.pyplot as plt
#import control as ctl
import yaml
import pickle
import math
# For data modeling
import scipy.optimize as opt
import numpy as np
import tarfile

# =============================================================================
# Experiment selection and load data
# =============================================================================
# Getting the right paths
experiment_date = '2021-01-26' # ex: '2020-11-20' '2021-01-22'
experiment_type = 'identification' # ex: 'preliminaries' 'identification'
experiment_dir = os.getcwd()+'/Documents/working-documents/data/hnrm-experiments-master-g5k-data-'+experiment_date+'_'+experiment_type+'/g5k/data/'+experiment_date+'_'+experiment_type+'/'
clusters = next(os.walk(experiment_dir))[1] # clusters are name of folders
# Remove input configuration files from cluster list (in identification experiments) 
if experiment_type == 'identification':
    clusters.remove('inputs')
traces = pd.DataFrame()
for cluster in clusters:
    # Extracting tar folders, if not already done
    if next(os.walk(experiment_dir+cluster))[1] == []:
        files = os.listdir(experiment_dir+cluster)
        for fname in files:
            if fname.endswith("tar.xz"):
                tar = tarfile.open(experiment_dir+cluster+'/'+fname, "r:xz")
                tar.extractall(path=experiment_dir+cluster+'/'+fname[:-7])
                tar.close()
    traces[cluster] = next(os.walk(experiment_dir+cluster))[1] 

# =============================================================================
# Processing data format to dataframe
# ============================================================================= 
data = {}
for cluster in clusters:
    data[cluster] = {}
    for trace in traces[cluster]:
        data[cluster][trace] = {}
        folder_path = experiment_dir+cluster+'/'+trace
        # Trace experimental plan: parameters or log
        with open(folder_path+"/parameters.yaml") as file:
            data[cluster][trace]['parameters'] = yaml.load(file, Loader=yaml.FullLoader)
        if experiment_type == 'identification':
            data[cluster][trace]['identification-runner-log'] = pd.read_csv(folder_path+"/identification-runner.log", sep = '\0', names = ['created','levelname','process','funcName','message'])
            data[cluster][trace]['enforce_powercap'] = data[cluster][trace]['identification-runner-log'][data[cluster][trace]['identification-runner-log']['funcName'] == 'enforce_powercap']
            data[cluster][trace]['enforce_powercap'] = data[cluster][trace]['enforce_powercap'].set_index('created')
            levels = [''.join(c for c in data[cluster][trace]['enforce_powercap']['message'][i] if c.isdigit()) for i in data[cluster][trace]['enforce_powercap'].index]
            data[cluster][trace]['enforce_powercap']['powercap'] = levels
        # Loading sensors data files
        pubMeasurements = pd.read_csv(folder_path+"/dump_pubMeasurements.csv")
        pubProgress = pd.read_csv(folder_path+"/dump_pubProgress.csv")
        # Checking if msg.timestamp == sensor.timestamps
        data[cluster][trace]['timestamp_check'] = True
        for i, row in pubMeasurements.iterrows():
            if pubMeasurements['msg.timestamp'][i] != pubMeasurements['sensor.timestamp'][i]:
                #print('Message and sensor timestamps are different! Cluster '+cluster+', trace '+trace+', at index '+str(i))
                data[cluster][trace]['timestamp_check'] = False
        # Extracting sensor data
        rapl_sensor0 = rapl_sensor1 = rapl_sensor2 = rapl_sensor3 = downstream_sensor = pd.DataFrame({'timestamp':[],'value':[]})
        for i, row in pubMeasurements.iterrows():
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
        #data[cluster][trace]['timestamp_check_measvspro'] = True
        #for i, row in progress_sensor.iterrows():
            #if progress_sensor['timestamp'][i] != downstream_sensor['timestamp'][i]:
                #print('Progress and downstream timestamps are different! at index Cluster '+cluster+', trace '+trace+', at index '+str(i))
                #data[cluster][trace]['timestamp_check_measvspro'] = False
        # Checking if pubMeasurements downstream timestamp is longer than process timestamps
        data[cluster][trace]['is_measurementstimestamp_longer_than_progresstimestamp'] = False
        if len(progress_sensor['timestamp']) < len(downstream_sensor['timestamp']):
            #print('More downstream measures than progress!')
            data[cluster][trace]['is_measurementstimestamp_longer_than_progresstimestamp'] = True
            #downstream_sensor = downstream_sensor[0:len(progress_sensor)] ####### /!\ one data sample is removed !!!
        # Writing in data dict
        data[cluster][trace]['rapl_sensors'] = pd.DataFrame({'timestamp':rapl_sensor0['timestamp'],'value0':rapl_sensor0['value'],'value1':rapl_sensor1['value'],'value2':rapl_sensor2['value'],'value3':rapl_sensor3['value']})
        data[cluster][trace]['performance_sensors'] = pd.DataFrame({'timestamp':progress_sensor['timestamp'],'progress':progress_sensor['value']})
        data[cluster][trace]['nrm_downstream_sensors'] = pd.DataFrame({'timestamp':downstream_sensor['timestamp'],'downstream':downstream_sensor['value']})
        # Indexing on elasped time since the first data point
        data[cluster][trace]['first_sensor_point'] = min(data[cluster][trace]['rapl_sensors']['timestamp'][0], data[cluster][trace]['performance_sensors']['timestamp'][0], data[cluster][trace]['nrm_downstream_sensors']['timestamp'][0])
        if experiment_type == 'preliminaries':
            timestampformat = 10**6
        else:
            timestampformat = 1
        data[cluster][trace]['rapl_sensors']['elapsed_time'] = (data[cluster][trace]['rapl_sensors']['timestamp'] - data[cluster][trace]['first_sensor_point'])/timestampformat
        data[cluster][trace]['rapl_sensors'] = data[cluster][trace]['rapl_sensors'].set_index('elapsed_time')
        data[cluster][trace]['performance_sensors']['elapsed_time'] = (data[cluster][trace]['performance_sensors']['timestamp'] - data[cluster][trace]['first_sensor_point'])/timestampformat
        data[cluster][trace]['performance_sensors'] = data[cluster][trace]['performance_sensors'].set_index('elapsed_time')

# =============================================================================
# Compute extra metrics: averages, frequencies, upsampling
# =============================================================================
for cluster in clusters:
    for trace in traces[cluster]:
        # Average and std sensors value
        avg0 = data[cluster][trace]['rapl_sensors']['value0'].mean()
        avg1 = data[cluster][trace]['rapl_sensors']['value1'].mean()
        avg2 = data[cluster][trace]['rapl_sensors']['value2'].mean()
        avg3 = data[cluster][trace]['rapl_sensors']['value3'].mean()
        std0 = data[cluster][trace]['rapl_sensors']['value0'].std()
        std1 = data[cluster][trace]['rapl_sensors']['value1'].std()
        std2 = data[cluster][trace]['rapl_sensors']['value2'].std()
        std3 = data[cluster][trace]['rapl_sensors']['value3'].std()
        data[cluster][trace]['aggregated_values'] = {'rapl0':avg0,'rapl1':avg1,'rapl2':avg2,'rapl3':avg3,'rapl0_std':std0,'rapl1_std':std1,'rapl2_std':std2,'rapl3_std':std3,'downstream':data[cluster][trace]['nrm_downstream_sensors']['downstream'].mean(),'progress':data[cluster][trace]['performance_sensors']['progress']}
        avgs = pd.DataFrame({'averages':[avg0, avg1, avg2, avg3]})
        data[cluster][trace]['aggregated_values']['rapls'] = avgs.mean()[0]
        #data[cluster][trace]['aggregated_values']['rapls_std'] = avgs.std()[0]
        # Sensors periods and frequencies
            # RAPL
        rapl_elapsed_time = data[cluster][trace]['rapl_sensors'].index
        data[cluster][trace]['aggregated_values']['rapls_periods'] = pd.DataFrame([rapl_elapsed_time[t]-rapl_elapsed_time[t-1] for t in range(1,len(rapl_elapsed_time))], index=[rapl_elapsed_time[t] for t in range(1,len(rapl_elapsed_time))], columns=['periods'])
        data[cluster][trace]['aggregated_values']['rapls_frequency'] = pd.DataFrame([1/(rapl_elapsed_time[t]-rapl_elapsed_time[t-1]) for t in range(1,len(rapl_elapsed_time))], index=[rapl_elapsed_time[t] for t in range(1,len(rapl_elapsed_time))], columns=['rapl frequency'])
        data[cluster][trace]['aggregated_values']['average_rapls_periods'] = data[cluster][trace]['aggregated_values']['rapls_periods'].mean()[0]
            # Progress
        performance_elapsed_time = data[cluster][trace]['performance_sensors'].index
        data[cluster][trace]['aggregated_values']['performance_periods'] = pd.DataFrame([performance_elapsed_time[t]-performance_elapsed_time[t-1] for t in range(1,len(performance_elapsed_time))], index=[performance_elapsed_time[t] for t in range(1,len(performance_elapsed_time))], columns=['periods'])
        data[cluster][trace]['aggregated_values']['average_performance_periods'] = data[cluster][trace]['aggregated_values']['performance_periods'].mean()[0]
        data[cluster][trace]['aggregated_values']['performance_frequency'] = pd.DataFrame([1/(performance_elapsed_time[t]-performance_elapsed_time[t-1]) for t in range(1,len(performance_elapsed_time))], index=[performance_elapsed_time[t] for t in range(1,len(performance_elapsed_time))], columns=['frequency'])
        data[cluster][trace]['aggregated_values']['average_performance_frequency'] = data[cluster][trace]['aggregated_values']['performance_frequency'].mean()[0]
        # Execution time:
        data[cluster][trace]['aggregated_values']['execution_time'] = performance_elapsed_time[-1]
        # Upsampling RAPL frequency:
        upsampling_factor = 1
        data[cluster][trace]['aggregated_values']['upsampled_timestamps'] = pd.DataFrame([max(data[cluster][trace]['rapl_sensors'].index[0]-i/upsampling_factor,0) for i in range(1,upsampling_factor)])
        for t in range(1,len(data[cluster][trace]['rapl_sensors'].index)):
            data[cluster][trace]['aggregated_values']['upsampled_timestamps'] = data[cluster][trace]['aggregated_values']['upsampled_timestamps'].append([i/upsampling_factor*data[cluster][trace]['rapl_sensors'].index[t]+(upsampling_factor-i)/upsampling_factor*data[cluster][trace]['rapl_sensors'].index[t-1] for i in range(0,upsampling_factor)])
        data[cluster][trace]['aggregated_values']['upsampled_timestamps'] = data[cluster][trace]['aggregated_values']['upsampled_timestamps'].append([data[cluster][trace]['rapl_sensors'].index[-1]])
        data[cluster][trace]['aggregated_values']['upsampled_timestamps']  = data[cluster][trace]['aggregated_values']['upsampled_timestamps'].sort_values(by=0)
        data[cluster][trace]['aggregated_values']['upsampled_timestamps'] = data[cluster][trace]['aggregated_values']['upsampled_timestamps'].set_index(0)
        # Computing count and frequency at upsampled_frequency:
        data[cluster][trace]['aggregated_values']['progress_frequency_at_rapl_rate'] = pd.DataFrame({'frequency':np.mean(data[cluster][trace]['aggregated_values']['performance_frequency']['frequency'].where(data[cluster][trace]['aggregated_values']['performance_frequency'].index<= data[cluster][trace]['aggregated_values']['upsampled_timestamps'].index[0],0)),'timestamp':data[cluster][trace]['aggregated_values']['upsampled_timestamps'].index[0]}, index=[0])
        data[cluster][trace]['aggregated_values']['progress_count'] = pd.DataFrame({'count':sum(data[cluster][trace]['performance_sensors']['progress'].where(data[cluster][trace]['performance_sensors'].index<= data[cluster][trace]['aggregated_values']['upsampled_timestamps'].index[0],0)),'timestamp':data[cluster][trace]['aggregated_values']['upsampled_timestamps'].index[0]}, index=[0])
        idx = 0  # index of powercap change in log
        data[cluster][trace]['aggregated_values']['pcap'] = pd.DataFrame({'pcap':math.nan,'timestamp':data[cluster][trace]['aggregated_values']['upsampled_timestamps'].index[0]}, index=[0])
        for t in range(1,len(data[cluster][trace]['aggregated_values']['upsampled_timestamps'].index)):
             data[cluster][trace]['aggregated_values']['progress_count'] = data[cluster][trace]['aggregated_values']['progress_count'].append({'count':sum(data[cluster][trace]['performance_sensors']['progress'].where((data[cluster][trace]['performance_sensors'].index>= data[cluster][trace]['aggregated_values']['upsampled_timestamps'].index[t-1]) & (data[cluster][trace]['performance_sensors'].index <=data[cluster][trace]['aggregated_values']['upsampled_timestamps'].index[t]),0)),'timestamp':data[cluster][trace]['aggregated_values']['upsampled_timestamps'].index[t]}, ignore_index=True)
             data[cluster][trace]['aggregated_values']['progress_frequency_at_rapl_rate'] = data[cluster][trace]['aggregated_values']['progress_frequency_at_rapl_rate'].append({'frequency':np.mean(data[cluster][trace]['aggregated_values']['performance_frequency']['frequency'].where((data[cluster][trace]['aggregated_values']['performance_frequency'].index>= data[cluster][trace]['aggregated_values']['upsampled_timestamps'].index[t-1]) & (data[cluster][trace]['aggregated_values']['performance_frequency'].index <=data[cluster][trace]['aggregated_values']['upsampled_timestamps'].index[t]))),'timestamp':data[cluster][trace]['aggregated_values']['upsampled_timestamps'].index[t]}, ignore_index=True)
             if experiment_type == 'identification':
                 if (data[cluster][trace]['enforce_powercap'].index[idx]-data[cluster][trace]['first_sensor_point'])<data[cluster][trace]['aggregated_values']['upsampled_timestamps'].index[t]:
                     if idx < len(data[cluster][trace]['enforce_powercap'])-1:           
                         idx = idx +1
                 if (data[cluster][trace]['enforce_powercap'].index[0]-data[cluster][trace]['first_sensor_point'])>data[cluster][trace]['aggregated_values']['upsampled_timestamps'].index[t]:
                    data[cluster][trace]['aggregated_values']['pcap'] = data[cluster][trace]['aggregated_values']['pcap'].append({'pcap':math.nan,'timestamp':data[cluster][trace]['aggregated_values']['upsampled_timestamps'].index[t]}, ignore_index=True)
                 elif (data[cluster][trace]['enforce_powercap'].index[-1]-data[cluster][trace]['first_sensor_point'])<data[cluster][trace]['aggregated_values']['upsampled_timestamps'].index[t]:
                     data[cluster][trace]['aggregated_values']['pcap'] = data[cluster][trace]['aggregated_values']['pcap'].append({'pcap':int(data[cluster][trace]['enforce_powercap']['powercap'].iloc[-1]),'timestamp':data[cluster][trace]['aggregated_values']['upsampled_timestamps'].index[t]}, ignore_index=True)
                 else:
                     data[cluster][trace]['aggregated_values']['pcap'] = data[cluster][trace]['aggregated_values']['pcap'].append({'pcap':int(data[cluster][trace]['enforce_powercap']['powercap'].iloc[idx-1]),'timestamp':data[cluster][trace]['aggregated_values']['upsampled_timestamps'].index[t]}, ignore_index=True)
        data[cluster][trace]['aggregated_values']['progress_count'] = data[cluster][trace]['aggregated_values']['progress_count'].set_index('timestamp')
        data[cluster][trace]['aggregated_values']['pcap'] = data[cluster][trace]['aggregated_values']['pcap'].set_index('timestamp')
        data[cluster][trace]['aggregated_values']['progress_frequency_at_rapl_rate'] = data[cluster][trace]['aggregated_values']['progress_frequency_at_rapl_rate'].set_index('timestamp')
        data[cluster][trace]['aggregated_values']['average_progress_count'] = data[cluster][trace]['aggregated_values']['progress_count'].mean()[0]

# =============================================================================
# Save and load processed data
# =============================================================================
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

# =============================================================================
# ================================== PLOTS ====================================
# =============================================================================
# Global configuration
clusters_styles = {clusters[0]:'peru',clusters[1]:'forestgreen',clusters[2]:'cornflowerblue'}
TDP = {'yeti':125,'dahu':125,'gros':125} # thermal dissipation power, in W
pmin = 40
pmax = 120

# =============================================================================
# Progress and Power over Time
# =============================================================================
# Choose a cluster and a trace
cluster = 'yeti'
requested_pcap = 50
experiment_plan = 'step_50-70.yaml' # 'step_110-130.yaml' 
for trace in traces[cluster]:
    if experiment_type == 'preliminaries':
        if requested_pcap == data[cluster][trace]['parameters']['powercap']:
            my_trace = trace
    if experiment_type == 'identification':
        if experiment_plan == data[cluster][trace]['parameters']['experiment-plan']:
            my_trace = trace
            
#my_traces = [traces[cluster][3], traces[cluster][7], traces[cluster][8]]

    # PLOT
x_zoom = [0,90]
fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(6.6,6.6))
#fig.suptitle(data[cluster][my_trace]['parameters']['benchmark']+', Pcap='+str(data[cluster][my_trace]['parameters']['powercap'])+'W')
#for my_trace in my_traces:
#data[cluster][my_trace]['nrm_downstream_sensors']['downstream'].plot(color='peru',ax=axes[0], style=".", markersize=2)
data[cluster][my_trace]['aggregated_values']['performance_frequency'].plot(color='darkblue',ax=axes[0], style=".", markersize=2)
data[cluster][my_trace]['aggregated_values']['progress_frequency_at_rapl_rate'].plot(color='cornflowerblue',ax=axes[0], marker="d", markersize=3)
axes[0].set_ylabel('Progress (heartbeat frequency in Hz)')
#axes[0].legend(['Heartrate','Averaged Heartrate ('+str(my_trace)+')'],fontsize='small',ncol=1)#
axes[0].set_ylim([0,100])
axes[0].set_xlim(x_zoom)
axes[0].grid(True)
#for my_trace in my_traces:
if experiment_type == 'preliminaries':
    axes[1].axhline(y=data[cluster][my_trace]['parameters']['powercap'], color='lightcoral', linestyle='-')
else:
    data[cluster][my_trace]['aggregated_values']['pcap'].plot(color='k',ax=axes[1], style=".")#, style="+",  markersize=4)
data[cluster][my_trace]['rapl_sensors']['value0'].plot(color='forestgreen',ax=axes[1], style="+")#, style="+",  markersize=4)
data[cluster][my_trace]['rapl_sensors']['value1'].plot(color='limegreen',ax=axes[1], style="+",  markersize=2)
data[cluster][my_trace]['rapl_sensors']['value2'].plot(color='darkolivegreen',ax=axes[1], style="-")#, style="+",  markersize=4)
data[cluster][my_trace]['rapl_sensors']['value3'].plot(color='lightgreen',ax=axes[1], style="-")#, style="+",  markersize=4)
#axes[1].axhline(y=TDP[cluster], color='black', linestyle=':')
axes[1].set_ylabel('Power (in W)')
axes[1].set_xlabel('Time (in s)')
#axes[1].set_ylim([60,100])
axes[1].legend(['powercap','measure package0','measure package1'],fontsize='small',ncol=1)
axes[1].grid(True)
axes[1].set_xlim(x_zoom)
#for my_trace in my_traces:
#data[cluster][my_trace]['performance_sensors']['progress'].plot(color='goldenrod',ax=axes[2], style=".", markersize=2)
#data[cluster][trace]['aggregated_values']['performance_periods'].plot(color='goldenrod',ax=axes[2], style=".", markersize=2)
#data[cluster][my_trace]['aggregated_values']['progress_count'].plot(color='goldenrod',ax=axes[2], style=".", markersize=3)
#plt.plot(data[cluster][my_trace]['rapl_sensors'].index,37*(-np.exp(-0.04*(data[cluster][my_trace]['rapl_sensors']['value0']-30))+1),color='r', marker="+",linestyle='') # data (lin with fixed alpha = 0.04) /!\ only package 0 !!
#axes[2].set_ylabel('pubProgress count')
#axes[2].grid(True)
#axes[2].set_xlim(x_zoom)
#axes[2].set_ylim([20,40])

    # Save
#plt.savefig(os.getcwd()+'/Documents/working-documents/figures/'+experiment_date+'/frequency_rapls_count_vs_time_'+cluster+'-'+str(data[cluster][my_trace]['parameters']['powercap'])+'W.pdf')
#plt.savefig(os.getcwd()+'/Documents/working-documents/figures/'+experiment_date+'/frequency_rapls_count_vs_time_'+cluster+'-identification-'+str(my_trace)+'W.pdf')


# =============================================================================
# RAPL actuator - Frequencies
# =============================================================================
my_trace = '100Hz' # ex: '1000Hz' '100Hz' '50Hz'
fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(6.6,6.6))
fig.suptitle('Required frequency: '+str(my_trace))
# plotting through time
#data[cluster][my_trace]['aggregated_values']['rapls_periods'].plot(color='darkblue',ax=axes, style=".", markersize=2)
# plotting distribution
data[cluster][my_trace]['aggregated_values']['rapls_periods'].hist(bins=100,ax=axes,density=True) 
axes.set_xlabel('RAPL measured arrival periods (in s)')
#axes.set_xlabel('Time (in s)')
axes.grid(True)

    # Save
#plt.savefig(os.getcwd()+'/working-documents/figures/'+experiment_date+'/histogram_rapl-periods-normed_'+cluster+'_'+str(my_trace)+'.pdf')

# =============================================================================
# RAPL actuator - In average: Power requested vs. power measured - Model
# =============================================================================
# Selecting relevant data: 
prequestedvsmeasured = {}
for cluster in clusters:
    prequestedvsmeasured[cluster] = pd.DataFrame()
    prequestedvsmeasured[cluster]['requested_pcap'] = [data[cluster][trace]['parameters']['powercap'] for trace in traces[cluster]]
    prequestedvsmeasured[cluster]['0'] = [data[cluster][trace]['aggregated_values']['rapl0'] for trace in traces[cluster]]
    # Standard deviation
    #prequestedvsmeasured[cluster]['0+'] = [data[cluster][trace]['aggregated_values']['rapl0']+data[cluster][trace]['aggregated_values']['rapl0_std'] for trace in traces[cluster]]
    #prequestedvsmeasured[cluster]['0-'] = [data[cluster][trace]['aggregated_values']['rapl0']-data[cluster][trace]['aggregated_values']['rapl0_std'] for trace in traces[cluster]]
    prequestedvsmeasured[cluster]['1'] = [data[cluster][trace]['aggregated_values']['rapl1'] for trace in traces[cluster]]
    prequestedvsmeasured[cluster]['2'] = [data[cluster][trace]['aggregated_values']['rapl2'] for trace in traces[cluster]]
    prequestedvsmeasured[cluster]['3'] = [data[cluster][trace]['aggregated_values']['rapl3'] for trace in traces[cluster]]
    prequestedvsmeasured[cluster]['rapls'] = [data[cluster][trace]['aggregated_values']['rapls'] for trace in traces[cluster]]
    prequestedvsmeasured[cluster]['pcap_requested'] = prequestedvsmeasured[cluster]['requested_pcap']
    prequestedvsmeasured[cluster] = prequestedvsmeasured[cluster].set_index('requested_pcap')
    prequestedvsmeasured[cluster].sort_index(inplace=True)
  
# Powercap to Power measure model:
def powermodel(power_requested, slope, offset):
    return slope*power_requested+offset

# Optimizing power model parameters
power_model_data = {}
power_model = {}
power_parameters = {}
r_squared_power_actuator = {}
for cluster in clusters:
    # guessed params
    power_parameters0 = [1, 0]                                        
    power_parameters[cluster], power_parameters_cov = opt.curve_fit(powermodel, prequestedvsmeasured[cluster]['pcap_requested'].loc[pmin:pmax], prequestedvsmeasured[cluster]['rapls'].loc[pmin:pmax], p0=power_parameters0)     # /!\ model computed with package 0
    # Model
    power_model[cluster] = powermodel(prequestedvsmeasured[cluster]['pcap_requested'].loc[pmin:pmax], power_parameters[cluster][0], power_parameters[cluster][1]) # model with fixed alpha
    # Equations taken from https://en.wikipedia.org/wiki/Coefficient_of_determination : "proportion of the variance in the dependent variable that is predictable from the independent variable"
    residuals_pcap = prequestedvsmeasured[cluster]['rapls'].loc[pmin:pmax] - power_model[cluster] 
    ss_res_pcap = np.sum(residuals_pcap**2)
    ss_tot_pcap = np.sum((prequestedvsmeasured[cluster]['rapls'].loc[pmin:pmax]-np.mean(prequestedvsmeasured[cluster]['rapls'].loc[pmin:pmax]))**2)
    r_squared_power_actuator[cluster] = 1 - (ss_res_pcap / ss_tot_pcap)
    print(cluster)
    print(r_squared_power_actuator[cluster])

# PLOT   
for cluster in clusters:
    fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(6.6,6.6))
    fig.suptitle('Power requested vs. measured - Cluster: '+cluster)
    prequestedvsmeasured[cluster]['0'].plot(color=clusters_styles[cluster],style="P")
    # Standard deviation
    #prequestedvsmeasured[cluster]['0+'].plot(color=clusters_styles[cluster],style=".")
    #prequestedvsmeasured[cluster]['0-'].plot(color=clusters_styles[cluster],style=".")
    prequestedvsmeasured[cluster]['1'].plot(color=clusters_styles[cluster],marker="X",linestyle='')
    prequestedvsmeasured[cluster]['2'].plot(color=clusters_styles[cluster],marker="o",linestyle='')
    prequestedvsmeasured[cluster]['3'].plot(color=clusters_styles[cluster],marker="d",linestyle='')
    plt.plot(prequestedvsmeasured[cluster]['pcap_requested'].loc[pmin:pmax],power_model[cluster],color=clusters_styles[cluster]) # model 0.04
    axes.axhline(y=TDP[cluster], color='lightcoral', linestyle='-')
    prequestedvsmeasured[cluster]['pcap_requested'].plot(color='grey', linewidth=0.5)
    axes.grid(True)
    axes.set_ylabel('Measured Power (in W)')
    axes.set_xlabel('requested Power (in W)')
    axes.legend(['Package 0','Package 1','Package 2','Package 3','TDP'],fontsize='small',loc='upper left',ncol=1)
    fig.gca().set_aspect('equal', adjustable='box')
    
        # Save
    #plt.savefig(os.getcwd()+'/Documents/working-documents/figures/'+experiment_date+'/requested_pcap_vs_rapls_'+cluster+'.pdf')

# =============================================================================
# RAPL actuator - through time
# =============================================================================
# Selecting some traces
requested_pcaps = [40, 70, 100, 120]
selected_traces = {}
for cluster in clusters:
    selected_traces[cluster] = {}
    for requested_pcap in requested_pcaps:
        for trace in traces[cluster]:
        #selected_traces[cluster][requested_pcap] = trace
            if requested_pcap == data[cluster][trace]['parameters']['powercap']:
                selected_traces[cluster][requested_pcap] = trace
# PLOT
colors_pcaps={requested_pcaps[0]:'crimson',requested_pcaps[1]:'yellowgreen',requested_pcaps[2]:'gold',requested_pcaps[3]:'dodgerblue'}
for cluster in clusters:
    fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(6.6,6.6))
    fig.suptitle('Cluster: '+cluster)
    for requested_pcap in requested_pcaps:
        #axes.axhline(y=data[cluster][selected_traces[cluster][requested_pcap]]['parameters']['powercap'], color=colors_pcaps[requested_pcap], linestyle='-')
        data[cluster][selected_traces[cluster][requested_pcap]]['rapl_sensors']['value0'].plot(color=colors_pcaps[requested_pcap],ax=axes, marker="+", linestyle='')
        data[cluster][selected_traces[cluster][requested_pcap]]['rapl_sensors']['value1'].plot(color=colors_pcaps[requested_pcap],ax=axes, marker="x", linestyle='')
        data[cluster][selected_traces[cluster][requested_pcap]]['rapl_sensors']['value2'].plot(color=colors_pcaps[requested_pcap],ax=axes, marker="1", linestyle='')
        data[cluster][selected_traces[cluster][requested_pcap]]['rapl_sensors']['value3'].plot(color=colors_pcaps[requested_pcap],ax=axes, marker="2", linestyle='')
    axes.axhline(y=TDP[cluster], color='black', linestyle=':')
    axes.set_ylabel('Power (in W)')
    axes.legend(['requested_powercap','rapl_sensors per package'],fontsize='small',loc='upper center',ncol=1)
    axes.grid(True)
    axes.set_ylim([0,155])
        
        # Save
    plt.savefig(os.getcwd()+'/Documents/working-documents/figures/'+experiment_date+'/rapls_actuator_through_time'+cluster+'-'+str(requested_pcaps)+'W.pdf')
    
# =============================================================================
# Static Characteristic: Progress vs Power 
# =============================================================================
# Selecting relevant data, modeling
sc = {}
sc_requested = {}
power2perf_model = {}
power2perf_params = {}
power2perf_parameters = {}
r_squared = {}
alpha = 0.04 # to find automatically
elected_performance_sensor = 'average_performance_frequency' # choose between: 'average_performance_periods' 'average_progress_count' 'average_performance_frequency'
for cluster in clusters:
    sc[cluster] = pd.DataFrame([data[cluster][trace]['aggregated_values'][elected_performance_sensor] for trace in traces[cluster]], index=[data[cluster][trace]['aggregated_values']['rapls'] for trace in traces[cluster]], columns=[elected_performance_sensor])
    sc[cluster].sort_index(inplace=True)
    if experiment_type == 'preliminaries':
        sc_requested[cluster] = pd.DataFrame([data[cluster][trace]['aggregated_values'][elected_performance_sensor] for trace in traces[cluster]], index=[data[cluster][trace]['parameters']['powercap'] for trace in traces[cluster]], columns=[elected_performance_sensor])
    else:
        sc_requested[cluster] = pd.DataFrame([data[cluster][trace]['aggregated_values'][elected_performance_sensor] for trace in traces[cluster]], index=[data[cluster][trace]['aggregated_values']['pcap'] for trace in traces[cluster]], columns=[elected_performance_sensor])
    sc_requested[cluster].sort_index(inplace=True)
    #power2perf_model[cluster] = [sc[cluster].at[max(sc[cluster].index),elected_performance_sensor]*(1-math.exp(-alpha*(i-min(sc[cluster].index)))) for i in sc[cluster].index] # final value:supposed to be known ?
    power2perf_model[cluster] = [(sc[cluster].at[sc[cluster].index[-1],elected_performance_sensor]+sc[cluster].at[sc[cluster].index[-2],elected_performance_sensor]+sc[cluster].at[sc[cluster].index[-3],elected_performance_sensor])/3*(1-math.exp(-alpha*(i-min(sc[cluster].index)))) for i in sc[cluster].index] # mean over last 3 values:  supposed to be known ?
    def power2perf_onlyalpha(power, alpha): # Cluster specific model (only alpha is optimally found)
        perf_inf = (sc[cluster].at[sc[cluster].index[-1],elected_performance_sensor]+sc[cluster].at[sc[cluster].index[-2],elected_performance_sensor]+sc[cluster].at[sc[cluster].index[-3],elected_performance_sensor])/3
        power_0 =  min(sc[cluster].index)
        return perf_inf*(1-np.exp(-alpha*(power-power_0)))

def power2perf(power, alpha, perf_inf, power_0): # general model formulation
    return perf_inf*(1-np.exp(-alpha*(power-power_0)))

# Model optimisation 
for cluster in clusters:
    power2perf_param0 = [0.04, (sc[cluster].at[sc[cluster].index[-1],elected_performance_sensor]+sc[cluster].at[sc[cluster].index[-2],elected_performance_sensor]+sc[cluster].at[sc[cluster].index[-3],elected_performance_sensor])/3, min(sc[cluster].index)]                                        # guessed params
    power2perf_param_opt, power2perf_param_cov = opt.curve_fit(power2perf, sc[cluster].index, sc[cluster][elected_performance_sensor], p0=power2perf_param0)     
    power2perf_onlyalpha_param_opt, power2perf_onlyalpha_param_cov = opt.curve_fit(power2perf_onlyalpha, sc[cluster].index, sc[cluster][elected_performance_sensor], p0=alpha)
    power2perf_params[cluster] = power2perf_onlyalpha_param_opt[0]
    # Model
    #power2perf_model[cluster] = power2perf(sc[cluster].index, *power2perf_param_opt) # model with optimization of all parameters
    #power2perf_model[cluster] = power2perf_onlyalpha(sc[cluster].index, *power2perf_onlyalpha_param_opt) # model with optimizd alpha
    power2perf_model[cluster] = power2perf_onlyalpha(sc[cluster].index, 0.04) # model with fixed alpha
    # Equations taken from https://en.wikipedia.org/wiki/Coefficient_of_determination : "proportion of the variance in the dependent variable that is predictable from the independent variable"
    residuals = sc[cluster][elected_performance_sensor] - power2perf_model[cluster]
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((sc[cluster][elected_performance_sensor]-np.mean(sc[cluster][elected_performance_sensor]))**2)
    r_squared[cluster] = 1 - (ss_res / ss_tot)
    print(cluster)
    print(r_squared[cluster])

# PLOT
fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(6.6,6.6))
#fig.suptitle('Static Characteristic - Performance vs Measured and requested Power')
for cluster in clusters:
    #sc[cluster][elected_performance_sensor].plot(color=clusters_styles[cluster],marker="x") # power vs. measured progress
    #sc_requested[cluster][elected_performance_sensor].plot(color=clusters_styles[cluster],marker="o",linestyle=':') # requested power vs measured progress
    plt.plot(sc[cluster].index,power2perf_model[cluster])#,color=clusters_styles[cluster]) # power vs. modelled progress
    # Plot linearized static characteristic:
    #plt.plot(-np.exp(-0.04*(sc[cluster].index-min(sc[cluster].index))),sc[cluster][elected_performance_sensor],color=clusters_styles[cluster], marker="+",linestyle='') # data (lin with fixed alpha = 0.04)
    #plt.plot(-np.exp(-0.04*(sc[cluster].index-min(sc[cluster].index))),power2perf_model[cluster],color=clusters_styles[cluster]) # model 0.04
axes.grid(True)
axes.set_ylabel('Performance ('+elected_performance_sensor+')')
axes.set_xlabel('Power (in W)')
axes.set_xlabel('Linearized Power: $-exp^{-0.04(power-30)}$')
#axes.set_yscale('log')
#axes.set_xscale('log')
legend = []
for cluster in clusters:
    #legend += [cluster+' - measured']
    #legend += [cluster+' - requested']
    #legend += [cluster+' - model, alpha='+str(power2perf_params[cluster])]
    legend += [cluster+' - measurements, $R^2$='+str(r_squared[cluster])]
    legend += [cluster+' - model, alpha=0.04']
axes.legend(legend,fontsize='small',loc='upper left',ncol=1)

    # Save
#plt.savefig(os.getcwd()+'/Documents/working-documents/figures/'+experiment_date+'/SC_'+elected_performance_sensor+'vs_rapls_requested_pcap_with_model_alpha'+str(alpha)+'.pdf')
#plt.savefig(os.getcwd()+'/Documents/working-documents/figures/'+experiment_date+'/SC_'+elected_performance_sensor+'vs_rapls_requested_pcap.pdf')
#plt.savefig(os.getcwd()+'/Documents/working-documents/figures/'+experiment_date+'/SC_'+elected_performance_sensor+'_vs_linearized_pcap_004.pdf')


# =============================================================================
# Execution time vs. power
# =============================================================================
# Selecting data
exec_time_power = {}
exec_time_power_requested = {}
for cluster in clusters:
    exec_time_power[cluster] = pd.DataFrame([data[cluster][trace]['aggregated_values']['execution_time'] for trace in traces[cluster]], index=[data[cluster][trace]['aggregated_values']['rapls'] for trace in traces[cluster]], columns=['execution_time'])
    exec_time_power[cluster].sort_index(inplace=True)
    exec_time_power_requested[cluster] = pd.DataFrame([data[cluster][trace]['aggregated_values']['execution_time'] for trace in traces[cluster]], index=[data[cluster][trace]['parameters']['powercap'] for trace in traces[cluster]], columns=['execution_time'])
    exec_time_power_requested[cluster].sort_index(inplace=True)

# PLOT
fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(6.6,6.6))
fig.suptitle('Execution time vs Measured and requested Power')
for cluster in clusters:
    exec_time_power[cluster]['execution_time'].plot(color=clusters_styles[cluster],marker="x")
    #exec_time_power_requested[cluster]['execution_time'].plot(color=clusters_styles[cluster],marker="o",linestyle=':')
axes.grid(True)
axes.set_ylabel('Execution Time (in s)')
#axes.set_yscale('log')
axes.set_xlabel('Power (in W)')
#axes.set_ylim([0,500])
legend = []
for cluster in clusters:
    legend += [cluster+' - measured']
    #legend += [cluster+' - requested']
axes.legend(legend,fontsize='small',loc='upper right',ncol=1)

    # Save
#plt.savefig(os.getcwd()+'/Documents/working-documents/figures/'+experiment_date+'/execution_time_vs_rapls_pcap.pdf')

# =============================================================================
#                               CORRELATION ANAYSIS
# =============================================================================
    # Using Pearson correlation coefficient 
for elected_performance_sensor in ['average_performance_periods','average_progress_count','average_performance_frequency']:
    print(elected_performance_sensor)
    for cluster in clusters:
        print(cluster)
        print(np.corrcoef([data[cluster][trace]['aggregated_values']['execution_time'] for trace in traces[cluster]], [data[cluster][trace]['aggregated_values'][elected_performance_sensor] for trace in traces[cluster]]))
    print('yeti without experiment 30W')
    traces_yeti_without30=traces[cluster].drop(2)
    print(np.corrcoef([data[cluster][trace]['aggregated_values']['execution_time'] for trace in traces_yeti_without30], [data[cluster][trace]['aggregated_values'][elected_performance_sensor] for trace in traces_yeti_without30]))

# =============================================================================
#                               Identification
# =============================================================================
# https://python-control.readthedocs.io/en/0.8.3/index.html
#rsys = ctl.era(YY, m, n, nin, nout, r)
#ctl.frd(d, w)
# https://control-toolbox.readthedocs.io/en/latest/index.html#
#ctl.SystemIdentification(path_x, path_x_dot, path_y)
#ctl.fit(num_epochs=500)
#ctl.model()
# https://web.math.princeton.edu/~cwrowley/python-control/index.html
# git clone https://github.com/python-control/python-control.git
