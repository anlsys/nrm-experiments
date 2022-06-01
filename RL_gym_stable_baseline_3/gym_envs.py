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


# In[3]:



omega_1 = 1.2
omega_2 = 0.5
zeta_1 = 0.9
zeta_2 = 0.6
A = np.array([[0, 1], [-omega_1**2, -2*omega_1*zeta_1]])
B = np.array([[0],[omega_1**2]]).reshape(2, 1)
dt = 0.01

def pm(x, t, mag_1, omega_1):
    u = mag_1*np.sin(omega_1*t)
    return np.dot(A, x) + np.dot(B, u)

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


# In[62]:


class Custom_env(Env):
    def __init__(self):
        # Actions we can are set of pcaps between 0 - 1
#         self.action_space = Discrete(3)
        self.action_space = Box(low=np.array([0,0]),high = np.array([1,1]))
        # Observation of the current performance (state space)
        self.observation_space = Box(low=np.array([[0],[0]]), high=np.array([[10],[10]]))
        # Set starting space
        self.state = np.random.rand(2,1)
        # Set execution length
        self.execution_time = 10
        self.current_step = 0
        
    def step(self, action):
        dt = 0.01
#         if action == 0:
#             mag = 1
#             omega = 1
#         elif action == 1:
#             mag = 1
#             omega = 1
#         else:
#             mag = -1
#             omega = -1
        mag = action[0]
        omega = action[1]
        x_res_train, infodict = odeintw(pm, self.state, np.array([0,dt]), args=( mag, omega),
                              full_output=True)
        # Apply action
        self.state = x_res_train[-1,:] 
#         print(x_res_train,"++",self.state)
        
        # Calculate reward
        reward = np.linalg.norm(self.state ** 2 - action ** 2)
        
        # Check if the sim is done
#         print(T,self.execution_time)
        if self.current_step >= self.execution_time:
            done = True
        else:
            done = False
        
        info = {}
        self.current_step+=1
        return self.state, reward, done, info

    def render(self):
        plt.figure(1)
        plt.plot(self.state[0], self.state[1],'ro')
        plt.xlabel('x_1')
        plt.ylabel("x_2")
        # plt.legend(loc='best')
        plt.draw()
    
    def reset(self):
        # Reset shower temperature
        self.state = np.random.rand(2,1)
        # print(self.state)
        # Reset shower time
        self.execution_time = 10
        self.current_step = 0
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
model.learn(total_timesteps=50000)
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
    env.render()

plt.show()