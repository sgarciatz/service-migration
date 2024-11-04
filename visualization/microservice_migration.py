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

data = data[["uav", "step", "service_0", "service_1", "service_2", "service_3"]]

deployments = []
migrations = []
for i in range(36):
    rows = data[data["uav"].str.contains(f"uav_{i}", na = False)][["service_0", "service_1", "service_2", "service_3"]]
    deployments_uav = []
    for row in rows.iterrows():
        deployments_uav.append(int(row[1]["service_0"] + row[1]["service_1"] + row[1]["service_2"] + row[1]["service_3"]))
    deployments.append(deployments_uav)

print(deployments[0])

for i in range(36):
    migrations_uav = [deployments[i][0]]
    for j in range (1, 54):
        migrations_uav.append(deployments[i][j] - deployments[i][j-1])
    migrations.append(migrations_uav)

print(migrations[0])

cmap = matplotlib.colors.ListedColormap(["blue", "white", "red"])
fig, ax = plt.subplots(1, 1, figsize=(10, 6), )
plt.xticks(ticks=[i for i in range(0, 54)], labels=["" for i in range(0, 54)])
plt.xlabel("Time slots", fontsize=24)
plt.yticks(ticks=[i for i in range(0, 36)], labels=["" for i in range(1, 37)])
plt.ylabel("UAVs", fontsize=24)

img = plt.imshow(np.array(migrations), cmap=cmap)
cbar = plt.colorbar(ticks=[0.65, 0, -0.65], fraction=0.032, pad=0.02)
cbar.set_ticklabels(["+1", "0", "-1"], fontsize = 24)
plt.show()