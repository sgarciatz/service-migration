import matplotlib
from matplotlib import pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.colors
import pandas as pd
from pathlib import Path
import os
import numpy as np




base_dir = Path("../output")
output_file = Path("Scenario_36.csv")
data = pd.read_csv(os.path.join(base_dir, output_file))

data = data[["uav", "step", "cpu_utilization"]]

data_rates = {}
for key, value in data.iterrows():
    if (value[0] not in data_rates): data_rates[value[0]] = {}
    data_rates[value[0]][value[1]] = value[2]

data_rates_m = []
max_value = 0
for value in data_rates.values():
    data_rates_uav = []
    for item in value.values():
        data_rates_uav.append(item)
        if item > max_value:
            max_value = item
    data_rates_m.append(data_rates_uav)

fig, ax = plt.subplots(1, 1, figsize=(10, 6), )
ax.yaxis.set_ticks([i for i in range(0, 36)], [f"uav_{i}" for i in range(1, 37)])
plt.xticks(ticks=[i for i in range(0, 54)], labels=["" for i in range(0, 54)])
plt.xlabel("Time slots", fontsize=24)
plt.yticks(ticks=[i for i in range(0, 36)], labels=["" for i in range(1, 37)])
plt.ylabel("UAVs", fontsize=24)

plt.imshow(data_rates_m, cmap="Blues", vmin=0, vmax=max_value)
cbar = plt.colorbar(fraction=0.032, pad=0.02)
cbar.set_label("CPU Utilization (%)", fontsize=24)
cbar.ax.tick_params(labelsize=16)

# cbar = plt.colorbar(ticks=[0.65, 0, -0.65], fraction=0.032, pad=0.02)
# cbar.set_ticklabels(["1 microservice added", "Stays the same", "1 microservice removed"], fontsize = 12)
plt.show()