#!/usr/bin/env python
# coding: utf-8

# In[8]:


# pip install simpy


# In[14]:


import simpy
import random
import pandas as pd
import numpy as np
import time
pd.set_option('display.max_columns',10)

start = time.time()

num_runs = 25 # Repeat simulation 25 times with the same parameters to get average
# num_runs = 1 
num_checkers = 35 # Number of document check queue servers
num_scanners = 35 # Number of personal check queue servers

arrival_rate = 50 # Passenger arrival rate
boarding_pass_mean = 0.75 # Document check queue service time
minScan = 0.5 # Personal check queue minimum service time 
maxScan = 1.0 # Personal check queue maximum service time 
sim_time = 360 # Each run will be 6 hours long
passenger_list = {}
res = {}

# Creating the Airport environment
class Airport(object):

    def __init__(self, env):
        self.env = env
        self.boarding_checker = simpy.Resource(env, num_checkers)
        self.personal_scanner = []  # Set of scanners
        for i in range(num_scanners):
            self.personal_scanner.append(simpy.Resource(env, 1))

    def boarding_check(self, passenger):
        rand_arrival = random.expovariate(1.0/boarding_pass_mean)
        yield self.env.timeout(rand_arrival)

    def scan_time(self, passenger):
        rand_scan_time = random.uniform(minScan, maxScan)
        yield self.env.timeout(rand_scan_time)


def passenger(env, name, s, passenger_list):

    # Time passenger arrives at airport
    passenger_list[name][0] = env.now

    with s.boarding_checker.request() as id_check:
        yield id_check

        # Time passenger enters boarding check
        passenger_check_start = env.now

        yield(env.process(s.boarding_check(name)))

        # Time passenger leaves boarding check
        passenger_check_end = env.now

        # Time passenger spends in boarding check
        passenger_list[name][1] = passenger_check_end - passenger_check_start

    # Checking for the shortest line
    shortest_line = 0
    for i in range(1, num_scanners):
        if (len(s.personal_scanner[i].queue) < len(s.personal_scanner[shortest_line].queue)):
            shortest_line = i

    with s.personal_scanner[shortest_line].request() as scan_request:
        yield scan_request

        # Time passenger enters personal scanner
        passenger_scan_start = env.now
        yield env.process(s.scan_time(name))

        # Time passenger leaves personal scanner
        passenger_scan_end = env.now

        # Time passenger spends in personal scanner
        passenger_list[name][2] = passenger_scan_end - passenger_scan_start

    # Time passenger leaves the checks
    passenger_list[name][3] = env.now

def setup(env):
    i = 0
    s = Airport(env)

    while True:
        yield env.timeout(random.expovariate(arrival_rate))
        i+=1
        passenger_list['Passenger ' + str(i)] = [0, 0, 0, 0]
        env.process(passenger(env, 'Passenger %d' % i,
                                  s, passenger_list))


print("Starting Airport Simulation")

# Run  multiple simulations and calculate wait time
for i in range(num_runs):
    random.seed(i)

    env = simpy.Environment()
    env.process(setup(env))

    env.run(until = sim_time)

    data_time = pd.DataFrame.from_dict(passenger_list, orient = 'index',
                                                       columns = [  'arrival_time',
                                                                    'time_in_boarding_check',
                                                                    'time_in_personal_scanner',
                                                                    'exit_time'])
    # Calculate total time in system
    data_time['total_time'] = data_time['exit_time'] - data_time['arrival_time']

    # Calculate wait time 
    data_time['total_wait_time'] =  data_time['total_time'] - data_time['time_in_boarding_check'] -                                     data_time['time_in_personal_scanner']
    data_time2 = data_time[data_time['total_time'] > 0]

    # Append avg of this run's passengers wait times to results
    res[i+1] = data_time2['total_wait_time'].mean()

    print("Run " + str(i+1) + " complete")

sim_res = pd.DataFrame.from_dict(res, orient = 'index', columns = ['Avg Wait Time'])
print(sim_res)

# Calculate % of runs where wait time is below 15 mins
success = sim_res[sim_res['Avg Wait Time'] <= 15]
success_rate = success.count()/ sim_res.count()
print("% of runs where wait time is below 15 mins with " + str(num_checkers) +" boarding pass checkers and "       + str(num_scanners) + " personal scanners is " + str(round(success_rate[0]*100, 1)) + "%")
print(str(sim_res.mean()))

end = time.time()
print('Total Simulation Run Time: ' + str(end - start))


# In[ ]:




