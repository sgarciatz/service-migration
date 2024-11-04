from matplotlib import pyplot as plt
from pathlib import Path
import pandas as pd
import os


base_dir = Path("../output")
output_file = Path("epochs.csv")
data = pd.read_csv(os.path.join(base_dir, output_file))

plt.plot(data["No of UAVs"], data["Time slots"]*10)
plt.xlabel("No. of UAVs", fontsize=12)
plt.yticks(ticks = [i for i in range(0, 601, 60)])
plt.xticks(ticks = [i for i in range(10, 61, 5)])
plt.ylabel("Elapsed time (minutes)", fontsize=12)

plt.show()