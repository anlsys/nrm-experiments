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


def progress_model(prog_now, prev_p_cap,T_S):
    pcap_old_L = -np.exp(-alpha[cluster] * (a[cluster] * prev_p_cap + b[cluster] - beta[cluster]))
    progress_value = K_L[cluster] * T_S / (T_S + tau) * pcap_old_L + tau / (T_S + tau) * (prog_now - K_L[cluster]) + K_L[cluster]
    return progress_value
    
    

time = pcap_data['upsampled_timestamps']
progress = [0]
pcap = pcap_data['pcap'].values.tolist()
first_progress = K_L[cluster] * (1 + -np.exp(-alpha[cluster] * (a[cluster] * pcap[1][0] + b[cluster] - beta[cluster])))
progress.append(first_progress)
for t in range(2,len(time)):
    pre_p_cap = pcap[t-1][0]
    pre_prog = progress[t-1]
    T_S = time[t] - time[t - 1]
    progress.append(progress_model(pre_prog,pre_p_cap,T_S))



fig, axs = plt.subplots(2)
fig.suptitle('power and performance against time')
axs[0].plot(pcap_data['upsampled_timestamps'], pcap, 'go')
axs[0].set(xlabel='time', ylabel='power cap')
axs[1].plot(pcap_data['upsampled_timestamps'], np.reshape(progress,(len(progress),1)), 'ro')
axs[1].set(xlabel='time', ylabel='performance')

plt.show()
