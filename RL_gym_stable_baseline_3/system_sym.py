import data_get_1od as DE
import gym_envs as GE
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np



cluster = 'gros'

a = {'gros': 0.83, 'dahu': 0.94, 'yeti': 0.89}
b = {'gros': 7.07, 'dahu': 0.17, 'yeti': 2.91}
alpha = {'gros': 0.047, 'dahu': 0.032, 'yeti': 0.023}
beta = {'gros': 28.5, 'dahu': 34.8, 'yeti': 33.7}
K_L = {'gros': 25.6, 'dahu': 42.4, 'yeti': 78.5}
tau = 0.33


pcap_data = DE.data_gen(pcap_data = True)


def progress_model(p_now, p_cap,T_S):
    pcap_old_L = -np.exp(-alpha[cluster] * (a[cluster] * p_now + b[cluster] - beta[cluster]))
    return K_L[cluster] * T_S / (T_S + tau) * pcap_old_L + tau / (T_S + tau) * (p_cap - K_L[cluster]) + K_L[cluster]
    
    

pcap_data['progress_model'] = pd.DataFrame({'progress_model':K_L[cluster]*(1 + -np.exp( -alpha[cluster]*( a[cluster]*pcap_data['pcap'].iloc[0] + b[cluster] - beta[cluster] ) )),'timestamp':pcap_data['upsampled_timestamps'][0]}, index=[0])
pcap_data['progress_model'] = pcap_data['progress_model'].append({'progress_model':K_L[cluster]*(1 + -np.exp( -alpha[cluster]*( a[cluster]*pcap_data['pcap'].iloc[1][0] + b[cluster] - beta[cluster] ) )),'timestamp':pcap_data['upsampled_timestamps'][1]}, ignore_index=True)
progress = []
powercap = []
for t in range(2,len(pcap_data['upsampled_timestamps'])):
    p_c = pcap_data['pcap']['pcap'].iloc[t-1]
    p_n = pcap_data['progress_model']['progress_model'].iloc[-1]
    T_S= pcap_data['upsampled_timestamps'][t] - pcap_data['upsampled_timestamps'][t-1]
    ret_pn = progress_model(p_n,p_c,T_S)
    RESULT.append(ret_pn)
    ACTION.append(p_c)
    pcap_data['progress_model'] = pcap_data['progress_model'].append({'progress_model':ret_pn,'timestamp':pcap_data['upsampled_timestamps'][t]}, ignore_index=True)
# pcap_data['progress_model'] = pcap_data['progress_model'].set_index('timestamp')


fig, axs = plt.subplots(2)
fig.suptitle('power and performance against time')
axs[0].plot(pcap_data['upsampled_timestamps'][:-2], ACTION, 'go')
axs[0].set(xlabel='time', ylabel='power cap')
axs[1].plot(pcap_data['upsampled_timestamps'][:-2], np.reshape(RESULT,(len(RESULT),1)), 'ro')
axs[1].set(xlabel='time', ylabel='performance')

plt.show()
