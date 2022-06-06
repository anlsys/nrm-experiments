

from gym import Env
from gym.spaces import Discrete, Box
import numpy as np
import random
import matplotlib.pyplot as plt
from stable_baselines3 import DDPG
from datetime import datetime


dt = 0.01
cluster = 'gros'

def env_def(in_data):

    a = {'gros':0.83,'dahu':0.94,'yeti':0.89}
    b = {'gros':7.07,'dahu':0.17,'yeti':2.91}
    alpha = {'gros':0.047,'dahu':0.032,'yeti':0.023}
    beta = {'gros':28.5,'dahu':34.8,'yeti':33.7}
    K_L = {'gros':25.6,'dahu':42.4,'yeti':78.5}
    # analytically found parameter
    tau = 0.33

    IN_MIN = in_data['pcap'].pcap.min()
    IN_MAX = in_data['pcap'].pcap.max()

    OBS_MIN = in_data['progress_model'].progress_model.min()
    OBS_MAX = in_data['progress_model'].progress_model.max()

    print(OBS_MIN)
    print(OBS_MAX)

    # def progress_funct(p_now,p_cap):
    #     p_next = K_L['gros']*dt/(dt+tau)*p_cap+tau/(dt+tau)*p_now
    #     return p_next

    def progress_model(p_now,p_cap):
        pcap_old_L = -np.exp(-alpha[cluster] * (a[cluster] * in_data['pcap'].iloc[t - 1] + b[cluster] - beta[cluster]))
        T_S = in_data['upsampled_timestamps'][t] - in_data['upsampled_timestamps'][t - 1]
        in_data['progress_model'] = in_data['progress_model'].append({'progress_model': K_L[cluster] * T_S / (T_S + tau) * pcap_old_L[0] + tau / (
                    T_S + tau) * (in_data['progress_model']['progress_model'].iloc[-1] - K_L[cluster]) + K_L[cluster],'timestamp':in_data['upsampled_timestamps'][
                                          t]}, ignore_index=True)

    fig, axs = plt.subplots(2)
    fig.suptitle('power and performance against time')
    # In[62]:


    class Custom_env(Env):
        def __init__(self):
            # Actions we can are set of pcaps between 0 - 1
    #         self.action_space = Discrete(3)
    #         self.action_space = Box(low=np.array([0,0]),high = np.array([1,1]))
            self.action_space = Box(low=np.float32(np.array([IN_MIN])), high=np.float32(np.array([IN_MAX])))
            # Observation of the current performance (state space)
            self.observation_space = Box(low=np.float32(np.array([OBS_MIN])), high=np.float32(np.array([OBS_MAX])))
            # Set starting space
            # self.state = np.random.rand(1,1)
            self.state = random.uniform(OBS_MIN,OBS_MAX).reshape(1,1)
            # Set execution length
            self.execution_time = 350
            self.current_step = 0
            self.action = None

        def step(self, action, testing=False):

            new_state = progress_funct(self.state,action)
            self.state = new_state
            self.action = action
    #         print(x_res_train,"++",self.state)

            # Calculate reward
            reward = np.linalg.norm(self.state) - np.linalg.norm(action**2)
            self.R = reward
            # Check if the sim is done
    #         print(T,self.execution_time)
            if not testing:
                if self.current_step >= self.execution_time:
                    done = True
                else:
                    done = False

                info = {}
                # self.render(self.current_step)
                self.current_step+=1

            else:
                self.render()

            return self.state, reward, done, info

        def render(self):
            print(self.current_step, self.state,self.action)
            axs[0].plot(self.current_step,self.state,'go')
            axs[0].set(xlabel = 'time',ylabel = 'performance')
            axs[1].plot(self.current_step,self.action,'ro')
            axs[1].set(xlabel = 'time',ylabel = 'power cap')

            self.total += self.R
            self.cost += self.action

        def reset(self):

            self.state = random.uniform(OBS_MIN,OBS_MAX).reshape(1,1)
            self.execution_time = 100
            self.current_step = 0
            self.total = 0
            self.cost = 0
            return self.state



    # In[63]:


    env = Custom_env()




    env.action_space.sample()




    test_obs = env.observation_space.sample()




    model = DDPG("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=1000)





    obs = env.reset()
    count = 0
    # while count < 100:
    for t in range(1, len(in_data['upsampled_timestamps'])):
        obs = in_data['progress_model']['progress_model'].iloc[t].reshape(1,1)
        act = in_data['pcap']['pcap'].iloc[t].reshape(1,1)
        # print(obs)
        action, _states = model.predict(obs)
        true_out = progress_funct(obs,act)
        obs, rewards, dones, info = env.step(action, testing=True)

        # print(obs)
        count += 1
        # env.render(count)


    print(env.cost,env.total)


if __name__ == "__main__":
    env_def()
    now = datetime.now()
    plt.savefig("./Figures/Figure_"+str(now)+".png")
    plt.show()
