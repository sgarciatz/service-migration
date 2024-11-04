import json
from typing import Any
from RequestGenerator import RequestGenerator as RG
from ServiceMigrator import ServiceMigrator
import time
from pathlib import Path

jotas = []
for i in range(10, 60):

    uavs, services, requests, time_slot_interval, n_requests = ServiceMigrator.read_input(Path("../input/Scenario_36.json"), i)

    service_migrator: ServiceMigrator = ServiceMigrator(uavs=uavs,
                                                        services=services,
                                                        requests=requests,
                                                        time_slot_interval=time_slot_interval,
                                                        n_requests=n_requests)
    j: int = 0
    times = []
    while(True):
        j += 1
        start = time.time()
        service_migrator.setup_model()
        service_migrator.solve()
        if (service_migrator.model.Status != 2):
            print(f"From Iter {j} and on it is unfeasable.")
            break
        #print(f"------------------Iter {str(i).rjust(2, ' ')}------------------")
        #service_migrator.print_solution()
        service_migrator.step()
        times.append(time.time()-start)
        #print(f"-------------------------------------------")
        #print()
    jotas.append(j-1)
for iter,j in enumerate(jotas):
    print(iter+10, " -> ", j)

#service_migrator.output_to_csv(Path("Scenario_36.csv"))