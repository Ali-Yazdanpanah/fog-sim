import matplotlib.pyplot as plt
import numpy as np
import random

# Generating values
memory_utilization = np.random.uniform(low=0.67, high=0.85, size=1000)
cpu_utilization = memory_utilization*1.05
execution_time = np.random.randint(low=191, high=214, size=1000)

# Plotting
fig = plt.figure()
ax = plt.axes(projection='3d')
ax.scatter(memory_utilization, cpu_utilization, execution_time, c=execution_time, cmap='Reds')
ax.set_xlabel('Memory Utilization')
ax.set_ylabel('CPU Utilization')
ax.set_zlabel('Execution Time')
plt.show()
