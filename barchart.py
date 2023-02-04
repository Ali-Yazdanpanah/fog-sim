import matplotlib.pyplot as plt
import random


# Starting value and step size
start_value = 70
step = 10

# Lists to hold the values and labels
values = []
labels = []


seventyNode = random.uniform(0.84, 0.86)
eightyNode = 1 - (70 - (seventyNode * 70) + 10)/80
ninghtyNode = 1 - (80 - (eightyNode * 80) + 10)/90
hundredNode = 1 - (90 - (ninghtyNode * 90) + 10)/100

values = [seventyNode,eightyNode,ninghtyNode,hundredNode]
# print(hundredNode)

# Generate the values and labels
for i in range(start_value, 101, step):
    # values.append(i)
    labels.append('Nodes: ' + str(i))

# Plot the bar chart
plt.bar(labels, values)

# Add a title and show the plot
plt.title('Number of Nodes in Computer Network')
plt.xlabel('Nodes')
plt.ylabel('Count')
plt.show()
