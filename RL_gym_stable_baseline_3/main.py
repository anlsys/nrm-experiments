import data_get_1od as DE
import gym_envs as GE
from matplotlib import pyplot as plt

pcap_data = DE.data_gen(pcap_data = True)
GE.env_def(pcap_data)
plt.show()