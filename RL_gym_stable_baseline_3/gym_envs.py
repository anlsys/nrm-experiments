

from gym import Env
from gym.spaces import Discrete, Box
import numpy as np
import random
import matplotlib.pyplot as plt
from stable_baselines3 import PPO
from stable_baselines3.common.noise import NormalActionNoise, OrnsteinUhlenbeckActionNoise
from datetime import datetime


dt = 0.01
cluster = 'gros'

def env_def(in_data):

    a = {'gros':0.83,'dahu':0.94,'yeti':0.89}
    b = {'gros':7.07,'dahu':0.17,'yeti':2.91}
    alpha = {'gros':0.047,'dahu':0.032,'yeti':0.023}
    beta = {'gros':28.5,'dahu':34.8,'yeti':33.7}
    K_L = {'gros':25.6,'dahu':42.4,'yeti':78.5}
    tau = 0.33

    IN_MIN = in_data['pcap'].pcap.min()
    IN_MAX = in_data['pcap'].pcap.max()

    OBS_MIN = in_data['progress_model'].progress_model.min()
    OBS_MAX = in_data['progress_model'].progress_model.max()

    print(OBS_MIN)
    print(OBS_MAX)


    def progress_model(prog_now, prev_p_cap, T_S):
        pcap_old_L = -np.exp(-alpha[cluster] * (a[cluster] * prev_p_cap + b[cluster] - beta[cluster]))
        progress_value = K_L[cluster] * T_S / (T_S + tau) * pcap_old_L + tau / (T_S + tau) * (prog_now - K_L[cluster]) + \
                         K_L[cluster]
        return progress_value



    class Custom_env(Env):
        def __init__(self):
            self.action_space = Box(low=np.float32(np.array([IN_MIN])), high=np.float32(np.array([IN_MAX])))
            print(IN_MIN,IN_MAX,OBS_MIN,OBS_MAX)
            self.observation_space = Box(low=np.float32(np.array([OBS_MIN])), high=np.float32(np.array([OBS_MAX])))
            self.state = random.uniform(OBS_MIN,OBS_MAX).reshape(1,1)
            self.execution_time = 350
            self.current_step = 0
            self.action = None

        def step(self, action, testing=False):
            T_S = 1
            new_state = progress_model(self.state,action,T_S)
            self.state = new_state
            self.action = action

            reward = np.linalg.norm(self.action**2)+np.linalg.norm(self.state)
            self.R = reward

            if not testing:
                if self.current_step >= self.execution_time:
                    done = True
                else:
                    done = False

                info = {}
                self.current_step+=1

            else:
                self.render()

            return self.state, reward, done, info

        def reset(self):

            self.state = random.uniform(OBS_MIN,OBS_MAX).reshape(1,1)
            self.execution_time = 100
            self.current_step = 0
            self.total = 0
            self.cost = 0
            return self.state

    action_noise = NormalActionNoise(mean=0.1, sigma=0.2)

    env = Custom_env()
    env.action_space.sample()
    test_obs = env.observation_space.sample()
    print(test_obs)
    model = PPO("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=10000)
    time = in_data['upsampled_timestamps']
    progress_M = [0]
    progress_actual = [0]
    pcap = in_data['pcap'].values.tolist()
    first_progress = K_L[cluster] * (
                1 + -np.exp(-alpha[cluster] * (a[cluster] * pcap[1][0] + b[cluster] - beta[cluster])))
    progress_M.append(first_progress)
    progress_actual.append(first_progress)

    fig1, axs1 = plt.subplots(2)
    fig1.suptitle('power and performance against time with RL')

    for t in range(2, len(time)):

        pre_prog_model = progress_M[t - 1]
        T_S = time[t] - time[t - 1]
        action, _states = model.predict(pre_prog_model.reshape(1,))
        next_model_observation = progress_model(pre_prog_model,action,T_S)
        progress_M.append(next_model_observation)
        axs1[0].plot(t,action, 'go')
        axs1[0].set(xlabel='time', ylabel='power cap')
        axs1[1].plot(t,next_model_observation, 'ro')
        axs1[1].set(xlabel='time', ylabel='performance')



if __name__ == "__main__":
    env_def()
    plt.show()
