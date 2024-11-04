from matplotlib import pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import pandas as pd
from pathlib import Path
import os

base_dir = Path("../output")
output_file = Path("Scenario_36.csv")
data = pd.read_csv(os.path.join(base_dir, output_file))

data = data[["step", "battery"]]
data["battery"] = data["battery"] / 46.62 *100
data_mean = data.groupby(["step"]).mean()
data_max = data.groupby(["step"]).max()
data_min = data.groupby(["step"]).min()
data_std = data.groupby(["step"]).std()

print(data_std)
data = data_mean["battery"].to_list()
data.insert(0, 100)


plt.plot(range(55), data)
# plt.errorbar(range(54), data_mean.head(54)["battery"], data_std.head(54)["battery"], fmt='.', color="black")
plt.xlabel("Elapsed time (minutes)", fontsize=12)
plt.ylabel("Remaining battery (%)", fontsize=12)
plt.axhline(y = 30, color = 'red', linestyle=":")
plt.legend(["Average UAV remaining battery", "Minimum UAV battery threshold, b"])
plt.ylim((0, 101))
plt.xlim((0, 55))
plt.xticks(range(0, 60, 5), [str(i*10) for i in range(0, 60, 5)])

plt.show()




colors = ["#FFFFFF", "#E6F0FF", "#CCE0FF", "#99C2FF", "#66A3FF", "#3385FF", "#0066FF", "#004C99", "#003366"]
custom_cmap = LinearSegmentedColormap.from_list("custom_cmap", colors)

