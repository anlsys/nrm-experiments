import os
import pandas as pd
import matplotlib.pyplot as plt
import yaml
import math
import scipy.optimize as opt
import numpy as np
import tarfile
from matplotlib import cm
import seaborn as sns

def data_gen(pcap_data = False, progress_data = False):
    exp_type = 'identification'
    experiment_type = exp_type
    experiment_dir = '/home/akhilesh.raj/Desktop/ANL_repo/europar-96-artifacts/dataset/'+exp_type+'/experiments-data/'
    #experiment_dir = '/Users/akhilesh/Desktop/europar-96-artifacts/dataset/'+exp_type+'/experiments-data/'
    clusters = next(os.walk(experiment_dir))[1]


    traces = {}
    traces_tmp = {}

    cluster = 'gros'
    traces[cluster] = pd.DataFrame()
    traces[cluster][0] = next(os.walk(experiment_dir+cluster))[1]
    data = {}

    data[cluster] = {}
    for trace in traces[cluster][0]:
        data[cluster][trace] = {}
        folder_path = experiment_dir + cluster + '/' + trace
        if os.path.isfile(folder_path + '/parameters.yaml'):
            with open(folder_path + "/parameters.yaml") as file:
                data[cluster][trace]['parameters'] = yaml.load(file, Loader=yaml.FullLoader)
                with open(folder_path + '/' + data[cluster][trace]['parameters']['config-file']) as file:
                    data[cluster][trace]['parameters']['config-file'] = yaml.load(file, Loader=yaml.FullLoader)
        data[cluster][trace]['identification-runner-log'] = pd.read_csv(folder_path + "/" + experiment_type + "-runner.log",
                                                                        sep='\0', names=['created', 'levelname', 'process',
                                                                                         'funcName', 'message'])
        data[cluster][trace]['enforce_powercap'] = data[cluster][trace]['identification-runner-log'][
            data[cluster][trace]['identification-runner-log']['funcName'] == 'enforce_powercap']
        data[cluster][trace]['enforce_powercap'] = data[cluster][trace]['enforce_powercap'].set_index('created')
        data[cluster][trace]['enforce_powercap']['powercap'] = [
            ''.join(c for c in data[cluster][trace]['enforce_powercap']['message'][i] if c.isdigit()) for i in
            data[cluster][trace]['enforce_powercap'].index]
        pubMeasurements = pd.read_csv(folder_path + "/dump_pubMeasurements.csv")
        pubProgress = pd.read_csv(folder_path + "/dump_pubProgress.csv")
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
        progress_sensor = pd.DataFrame({'timestamp': pubProgress['msg.timestamp'], 'value': pubProgress['sensor.value']})
        # Writing in data dict
        data[cluster][trace]['rapl_sensors'] = pd.DataFrame(
            {'timestamp': rapl_sensor0['timestamp'], 'value0': rapl_sensor0['value'], 'value1': rapl_sensor1['value'],
             'value2': rapl_sensor2['value'], 'value3': rapl_sensor3['value']})
        data[cluster][trace]['performance_sensors'] = pd.DataFrame(
            {'timestamp': progress_sensor['timestamp'], 'progress': progress_sensor['value']})

        data[cluster][trace]['first_sensor_point'] = min(data[cluster][trace]['rapl_sensors']['timestamp'][0],
                                                         data[cluster][trace]['performance_sensors']['timestamp'][
                                                             0])
        data[cluster][trace]['rapl_sensors']['elapsed_time'] = (
                    data[cluster][trace]['rapl_sensors']['timestamp'] - data[cluster][trace]['first_sensor_point'])
        data[cluster][trace]['rapl_sensors'] = data[cluster][trace]['rapl_sensors'].set_index('elapsed_time')
        data[cluster][trace]['performance_sensors']['elapsed_time'] = (
                    data[cluster][trace]['performance_sensors']['timestamp'] - data[cluster][trace]['first_sensor_point'])
        data[cluster][trace]['performance_sensors'] = data[cluster][trace]['performance_sensors'].set_index('elapsed_time')



    for trace in traces[cluster][0]:
        data[cluster][trace]['aggregated_values'] = {'progress':data[cluster][trace]['performance_sensors']['progress']}

        rapl_elapsed_time = data[cluster][trace]['rapl_sensors'].index
        data[cluster][trace]['aggregated_values']['rapls_periods'] = pd.DataFrame([rapl_elapsed_time[t]-rapl_elapsed_time[t-1] for t in range(1,len(rapl_elapsed_time))], index=[rapl_elapsed_time[t] for t in range(1,len(rapl_elapsed_time))], columns=['periods'])
        performance_elapsed_time = data[cluster][trace]['performance_sensors'].index
        data[cluster][trace]['aggregated_values']['performance_frequency'] = pd.DataFrame([1/(performance_elapsed_time[t]-performance_elapsed_time[t-1]) for t in range(1,len(performance_elapsed_time))], index=[performance_elapsed_time[t] for t in range(1,len(performance_elapsed_time))], columns=['frequency'])
        data[cluster][trace]['aggregated_values']['execution_time'] = performance_elapsed_time[-1]
        data[cluster][trace]['aggregated_values']['upsampled_timestamps'] = data[cluster][trace]['rapl_sensors'].index
        data[cluster][trace]['aggregated_values']['progress_frequency_median'] = pd.DataFrame({'median':np.nanmedian(data[cluster][trace]['aggregated_values']['performance_frequency']['frequency'].where(data[cluster][trace]['aggregated_values']['performance_frequency'].index<= data[cluster][trace]['aggregated_values']['upsampled_timestamps'][0],0)),'timestamp':data[cluster][trace]['aggregated_values']['upsampled_timestamps'][0]}, index=[0])
        idx = 0
        data[cluster][trace]['aggregated_values']['pcap'] = pd.DataFrame({'pcap':math.nan,'timestamp':data[cluster][trace]['aggregated_values']['upsampled_timestamps'][0]}, index=[0])
        for t in range(1,len(data[cluster][trace]['aggregated_values']['upsampled_timestamps'])):
             data[cluster][trace]['aggregated_values']['progress_frequency_median'] = data[cluster][trace]['aggregated_values']['progress_frequency_median'].append({'median':np.nanmedian(data[cluster][trace]['aggregated_values']['performance_frequency']['frequency'].where((data[cluster][trace]['aggregated_values']['performance_frequency'].index>= data[cluster][trace]['aggregated_values']['upsampled_timestamps'][t-1]) & (data[cluster][trace]['aggregated_values']['performance_frequency'].index <=data[cluster][trace]['aggregated_values']['upsampled_timestamps'][t]))),'timestamp':data[cluster][trace]['aggregated_values']['upsampled_timestamps'][t]}, ignore_index=True)
             if (experiment_type == 'controller') or (experiment_type == 'identification'):
                 if (data[cluster][trace]['enforce_powercap'].index[idx]-data[cluster][trace]['first_sensor_point'])<data[cluster][trace]['aggregated_values']['upsampled_timestamps'][t]:
                     if idx < len(data[cluster][trace]['enforce_powercap'])-1:
                         idx = idx +1
                 if (data[cluster][trace]['enforce_powercap'].index[0]-data[cluster][trace]['first_sensor_point'])>data[cluster][trace]['aggregated_values']['upsampled_timestamps'][t]:
                    data[cluster][trace]['aggregated_values']['pcap'] = data[cluster][trace]['aggregated_values']['pcap'].append({'pcap':math.nan,'timestamp':data[cluster][trace]['aggregated_values']['upsampled_timestamps'][t]}, ignore_index=True)
                 elif (data[cluster][trace]['enforce_powercap'].index[-1]-data[cluster][trace]['first_sensor_point'])<data[cluster][trace]['aggregated_values']['upsampled_timestamps'][t]:
                     data[cluster][trace]['aggregated_values']['pcap'] = data[cluster][trace]['aggregated_values']['pcap'].append({'pcap':int(data[cluster][trace]['enforce_powercap']['powercap'].iloc[-1]),'timestamp':data[cluster][trace]['aggregated_values']['upsampled_timestamps'][t]}, ignore_index=True)
                 else:
                     data[cluster][trace]['aggregated_values']['pcap'] = data[cluster][trace]['aggregated_values']['pcap'].append({'pcap':int(data[cluster][trace]['enforce_powercap']['powercap'].iloc[idx-1]),'timestamp':data[cluster][trace]['aggregated_values']['upsampled_timestamps'][t]}, ignore_index=True)
        data[cluster][trace]['aggregated_values']['pcap'] = data[cluster][trace]['aggregated_values']['pcap'].set_index('timestamp')




    # clusters_styles = {'yeti':'black','gros':'orange','dahu':'skyblue'}
    # clusters_markers = {'yeti':'o','gros':'x','dahu':'v'}
    plt.rcParams.update({'font.size': 14})



    plotted_traces = {
        #'gros':'preliminaries_stream_c_2021-02-17T11:04:41+01:00'
    'gros':'preliminaries_stream_c_2021-02-17T17:08:58+01:00'
        }



    a = {'gros':0.83,'dahu':0.94,'yeti':0.89}
    b = {'gros':7.07,'dahu':0.17,'yeti':2.91}
    alpha = {'gros':0.047,'dahu':0.032,'yeti':0.023}
    beta = {'gros':28.5,'dahu':34.8,'yeti':33.7}
    K_L = {'gros':25.6,'dahu':42.4,'yeti':78.5}
    tau = 0.33

    for my_trace in traces[cluster][0]:
        data[cluster][my_trace]['aggregated_values']['progress_model'] = pd.DataFrame({'progress_model':K_L[cluster]*(1 + -np.exp( -alpha[cluster]*( a[cluster]*data[cluster][my_trace]['aggregated_values']['pcap'].iloc[0] + b[cluster] - beta[cluster] ) )),'timestamp':data[cluster][my_trace]['aggregated_values']['upsampled_timestamps'][0]}, index=[0])
        data[cluster][my_trace]['aggregated_values']['progress_model'] = data[cluster][my_trace]['aggregated_values']['progress_model'].append({'progress_model':K_L[cluster]*(1 + -np.exp( -alpha[cluster]*( a[cluster]*data[cluster][my_trace]['aggregated_values']['pcap'].iloc[1][0] + b[cluster] - beta[cluster] ) )),'timestamp':data[cluster][my_trace]['aggregated_values']['upsampled_timestamps'][1]}, ignore_index=True)
        for t in range(2,len(data[cluster][my_trace]['aggregated_values']['upsampled_timestamps'])):
            pcap_old_L = -np.exp( -alpha[cluster]*( a[cluster]*data[cluster][my_trace]['aggregated_values']['pcap'].iloc[t-1] + b[cluster] - beta[cluster] ) )
            T_S= data[cluster][my_trace]['aggregated_values']['upsampled_timestamps'][t] - data[cluster][my_trace]['aggregated_values']['upsampled_timestamps'][t-1]
            data[cluster][my_trace]['aggregated_values']['progress_model'] = data[cluster][my_trace]['aggregated_values']['progress_model'].append({'progress_model':K_L[cluster]*T_S/(T_S+tau)*pcap_old_L[0] + tau/(T_S+tau)*(data[cluster][my_trace]['aggregated_values']['progress_model']['progress_model'].iloc[-1] - K_L[cluster]) + K_L[cluster],'timestamp':data[cluster][my_trace]['aggregated_values']['upsampled_timestamps'][t]}, ignore_index=True)
        data[cluster][my_trace]['aggregated_values']['progress_model'] = data[cluster][my_trace]['aggregated_values']['progress_model'].set_index('timestamp')



    my_trace = plotted_traces[cluster]
    # x_zoom = [0,len(data[cluster][my_trace]['aggregated_values']['pcap'])]
    # fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(5.7,6.6))
    # data[cluster][my_trace]['aggregated_values']['progress_frequency_median']['median'].plot(color='k',ax=axes[0], marker='o', markersize=3, linestyle='')
    # data[cluster][my_trace]['aggregated_values']['progress_model'].plot(color='skyblue',ax=axes[0], linewidth=2)#, marker="d", markersize=3)
    # axes[0].set_ylabel('Progress [Hz]')
    # axes[0].set_xlabel('')
    # axes[0].legend(['cluster: '+cluster])
    # axes[0].legend(['Measure','Model'],fontsize='small')
    # axes[0].set_ylim([0,75])
    # axes[0].set_xlim(x_zoom)
    # axes[0].grid(True)
    # data[cluster][my_trace]['aggregated_values']['pcap'].plot(color='k',ax=axes[1], style=".")#, style="+",  markersize=4)
    # data[cluster][my_trace]['rapl_sensors']['value0'].plot(color='palevioletred',ax=axes[1], style="+")#, style="+",  markersize=4)
    # axes[1].set_ylabel('Power [W]')
    # axes[1].set_xlabel('Time [s]')
    # axes[1].set_ylim([30,130])
    # axes[1].legend(['Powercap','Measure'],fontsize='small',ncol=1)
    # axes[1].grid(True)
    # axes[1].set_xlim(x_zoom)

    if pcap_data:
        return data[cluster][my_trace]['aggregated_values']

if __name__ == "__main__":
    p_test = data_gen(pcap_data = True)
    print(p_test['pcap'], p_test['progress_model'])
    plt.show()
