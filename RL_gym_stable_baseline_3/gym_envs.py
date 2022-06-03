#!/usr/bin/env python
# coding: utf-8

# In[2]:


from gym import Env
from gym.spaces import Discrete, Box
import numpy as np
import random
from odeintw import odeintw
import matplotlib.pyplot as plt
from odeintw import odeintw
from stable_baselines3 import PPO
from datetime import datetime

# In[3]:



omega_1 = 1.2
omega_2 = 0.5
zeta_1 = 0.9
zeta_2 = 0.6
A = np.array([[0, 1], [-omega_1**2, -2*omega_1*zeta_1]])
B = np.array([[0],[omega_1**2]]).reshape(2, 1)
dt = 0.01


a = {'gros':0.83,'dahu':0.94,'yeti':0.89}
b = {'gros':7.07,'dahu':0.17,'yeti':2.91}
alpha = {'gros':0.047,'dahu':0.032,'yeti':0.023}
beta = {'gros':28.5,'dahu':34.8,'yeti':33.7}
K_L = {'gros':25.6,'dahu':42.4,'yeti':78.5}
# analytically found parameter
tau = 0.33



def pm(x, t, mag_1, omega_1):
    u = mag_1*np.sin(omega_1*t)
    return np.dot(A, x) + np.dot(B, u)

def progress_funct(p_now,p_cap):
    p_next = K_L['gros']*dt/(dt+tau)*p_cap+tau/(dt+tau)*p_now
    return p_next

# def main():
#     dt = 0.01
#     train_t = 10
#     num_p = int(train_t/dt)
#     x0_train = 10*np.random.rand(2,1)
#     t = np.linspace(0, train_t, num_p)
#
#     mag = 1
#     omega = 1
#     x_res_train, infodict = odeintw(pm, x0_train, t, args=( mag, omega),
#                               full_output=True)

#     plt.figure(1)

#     plt.plot(t, x_res_train.reshape(num_p,2), label='z1', linewidth=1.5)
#     plt.xlabel('t')
#     plt.legend(loc='best')
#     plt.draw()

#     plt.show()

# if __name__ == "__main__":
#     main()

fig, axs = plt.subplots(2)
fig.suptitle('power and performance against time')
# In[62]:


class Custom_env(Env):
    def __init__(self):
        # Actions we can are set of pcaps between 0 - 1
#         self.action_space = Discrete(3)
#         self.action_space = Box(low=np.array([0,0]),high = np.array([1,1]))
        self.action_space = Box(low=np.float32(np.array([0.40])), high=np.float32(np.array([1.20])))
        # Observation of the current performance (state space)
        self.observation_space = Box(low=np.float32(np.array([0])), high=np.float32(np.array([0.60])))
        # Set starting space
        self.state = np.random.rand(1,1)
        # Set execution length
        self.execution_time = 100
        self.current_step = 0
        self.action = None
        
    def step(self, action):
        # dt = 0.01
#         if action == 0:
#             mag = 1
#             omega = 1
#         elif action == 1:
#             mag = 1
#             omega = 1
#         else:
#             mag = -1
#             omega = -1

        # x_res_train, infodict = odeintw(pm, self.state, np.array([0,dt]), args=( mag, omega),
        #                       full_output=True)
        # Apply action
        new_state = progress_funct(self.state,action)
        self.state = new_state
        self.action = action
#         print(x_res_train,"++",self.state)
        
        # Calculate reward
        reward = np.linalg.norm(self.state) - np.linalg.norm(action**2)
        self.R = reward
        # Check if the sim is done
#         print(T,self.execution_time)
        if self.current_step >= self.execution_time:
            done = True
        else:
            done = False
        
        info = {}
        # self.render(self.current_step)
        self.current_step+=1

        return self.state, reward, done, info

    def render(self,time):
        # plt.figure(1)
        # plt.plot(time,self.action,'ro')
        # plt.plot(time,self.state,'go')
        # plt.xlabel('time step')
        # plt.ylabel('power, performance')
        # # plt.legend(loc='best')
        # plt.draw()
        axs[0].plot(time,self.state,'go')
        axs[0].set(xlabel = 'time',ylabel = 'performance')
        axs[1].plot(time,self.action,'ro')
        axs[1].set(xlabel = 'time',ylabel = 'power cap')

        self.total += self.R
        self.cost += self.action
        # plt.draw()
    
    def reset(self):
        # fig, axs = plt.subplots(2)
        # fig.suptitle('power and performance against time')
        # Reset shower temperature
        self.state = np.random.rand(1,1)
        # print(self.state)
        # Reset shower time
        self.execution_time = 10
        self.current_step = 0
        self.total = 0
        self.cost = 0
        return self.state
    


# In[63]:


env = Custom_env()


# In[64]:


env.action_space.sample()


# In[65]:


test_obs = env.observation_space.sample()
print(test_obs.shape)

# In[66]:


# episodes = 100
# for episode in range(1,episodes+1):
# #     env.render()
#     state = env.reset()
#     done = False
#     score = 0
#     train_t = 11
#     num_p = int(train_t/dt)
#     t_dur = np.linspace(0, train_t, num_p)
#     while not done:
#         action = env.action_space.sample()
#         n_state, reward, done, info = env.step(action)
#         score += reward
#     print('Epsiode:{} Score:{}'.format(episode,score))


# In[67]:


model = PPO("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=10000)
# print("execution completed")
# model.save("dynamics")

# del model # remove to demonstrate saving and loading

# model = PPO.load("dynamics")


# In[ ]:


obs = env.reset()
count = 0
while count < 100:
    action, _states = model.predict(obs)
    obs, rewards, dones, info = env.step(action)
    # print(obs)
    count += 1
    env.render(count)

now = datetime.now()

print(env.cost,env.total)

plt.savefig("./Figures/Figure_"+str(now)+".png")
plt.show()
