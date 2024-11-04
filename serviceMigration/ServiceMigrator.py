import json
from typing import Any
import gurobipy as gp
from PowerConsumptionModel import PowerConsumptionModel as PCM
from RequestGenerator import RequestGenerator as RG
from pathlib import Path
import pandas as pd


env = gp.Env(empty=True)
env.setParam("OutputFlag", 0)
env.start()

class ServiceMigrator():
    """ServiceMigrator is a class that takes UAVs and services as input
    and generates an MILP model that optimizes the service deployment
    over the UAVs to maximize the battery of the UAV with the least
    battery, or the mean battery.
    """


    def __init__(self, uavs: dict[str, dict[str, float]],
                       services: dict[str, dict[str, dict[str, float]]],
                       requests: dict[tuple[str, str], float],
                       time_slot_interval: float,
                       n_requests: int) -> None:


        self.uavs: dict[str, dict[str, float]] = uavs
        self.services: dict[str, dict[str, dict[str, float]]] = services
        self.requests: dict[tuple[str, str], float] = requests
        self.time_slot_interval: float = time_slot_interval
        self.n_requests = n_requests
        self.model: gp.Model = gp.Model(env=env)
        self.X_u_m: dict[tuple[str, str], gp.Var]
        self.z: gp.Var
        self.constraints_1: dict[str, gp.Constr]
        self.constraints_2: dict[str, gp.Constr]
        self.constraints_3: dict[str, gp.Constr]
        self.constraints_4: dict[str, gp.Constr]
        self.constraints_5: dict[str, gp.Constr]
        self.constraints_5: dict[str, gp.Constr]
        self.constraints_6: dict[str, gp.Constr]

        self.output: dict[str, list[dict[str, Any]]] = {}
        for uav in self.uavs.keys():
            self.output[uav] = []

    @staticmethod
    def read_input(file_path: Path, i) -> tuple[dict[str, dict[str, float]],
                                             dict[str, dict[str, dict[str, float]]],
                                             dict[tuple[str, str], float],
                                             float,
                                             int]:
        """Reads the input_file and returns the information needed to
        create a ServiceMigrator instance.

        Args:
            file_path (Path): The path of the input_file

        Returns:
            tuple[dict[str, dict[str, float]],
                  dict[str, dict[str, dict[str, float]]],
                  dict[tuple[str, str], float], float, int]: The
                information needed to create a ServiceMigrator
                instance.
        """
        input: dict[str, Any]
        with open(file_path) as file:
            input = json.loads(file.read())


        services: dict[str, dict[str, dict[str, float|int]]] = {}
        for serv in input["services"]:
            serv_id, serv_value = next(iter(serv.items()))
            services[serv_id] = {}
            for replica in range(serv_value["replicas"]):
                services[serv_id][f"{serv_id}_{replica}"] = {"cpu_cycles_per_deploy": serv_value["cpu_cycles_per_deploy"],
                                                            "cpu_cycles_per_request": serv_value["cpu_cycles_per_request"],
                                                            "ram_req": serv_value["ram_req"],
                                                            "input_size": serv_value["input_size"]}

        uavs: dict[str, dict[str, float]] = {}
        for iterr, uav in enumerate(range(i)):
            uavs[iterr] = {"batt_lvl": 46.62,
                            "ram_cap": 4.0,
                            "cpu_freq": 1.5}

        # requests: dict[tuple[str, str], float] = {}

        time_slot_interval: float = input["time_slot_interval"]
        n_requests: int = input["n_requests"]
        requests: dict[tuple[str, str], float] = RG.generate_requests(uavs=uavs,
                                                                    services=services,
                                                                    n_requests=n_requests)
        return uavs, services, requests, time_slot_interval, n_requests

    def _add_variables(self) -> None:
        """Add the variables to the model."""
        self.X_u_m = {}
        for uav in self.uavs.keys():
            for serv in self.services.keys():
                for instance in self.services[serv].keys():
                    self.X_u_m[(uav, instance)] = self.model.addVar(vtype=gp.GRB.BINARY,
                                                name=f"x {uav} {instance}")
        max_batt_lvl: float = max([uav["batt_lvl"] for uav in self.uavs.values()])

        self.z = self.model.addVar(vtype=gp.GRB.CONTINUOUS,
                                   lb=0.3,
                                   ub=max_batt_lvl,
                                   name="z")
        self.model.update()

    def _add_constraints_1(self) -> None:
        """Add a set of constraints to force the model to deploy all
        microservices.
        """
        self.constraints_1 = {}
        for serv in self.services.keys():
            for instance in self.services[serv].keys():
                variables_1: list[gp.Var] = [self.X_u_m[(uav, instance)] for uav in self.uavs.keys()]
                lin_expr: gp.LinExpr = gp.quicksum(variables_1)
                self.constraints_1[f"c1_{instance}"] = self.model.addConstr(lin_expr == 1)
        self.model.update()


    def _add_constraints_2(self) -> None:
        """Add a set of constraints to force the model to ensure that
        the sum of the ram_req of the services deployed in each UAV
        does not surpass the UAV's ram_cap.
        """
        self.constraints_2 = {}
        uav_ram_cap: float
        for uav, uav_value in self.uavs.items():
            variables_2: dict[gp.Var, float] = {}
            uav_ram_cap = uav_value["ram_cap"]
            for serv in self.services.keys():
                for instance_key, instance_value in self.services[serv].items():
                    variables_2[self.X_u_m[(uav, instance_key)]] = instance_value["ram_req"]
            lin_expr: gp.LinExpr = gp.quicksum(
                [var*coeff for var, coeff in variables_2.items()])
            self.constraints_2[f"c2_{uav}"] = self.model.addConstr(lin_expr <= uav_ram_cap)
        self.model.update()

    def _add_constraints_3(self) -> None:
        """Add a set of constraints to force the model to ensure that
        the sum of the cpu_cycles_per_deploy of the services deployed in each
        UAV plus the requests times cpu_cycles_per_request of those
        services does not surpass the UAV's cpu_freq.
        """
        self.constraints_3 = {}
        for uav, uav_value in self.uavs.items():
            lin_expr: gp.LinExpr = PCM.get_cpu_utilization(
                services=self.services,
                uav=(uav, uav_value),
                requests=self.requests,
                variables=self.X_u_m)
            self.constraints_3[f"c3_{uav}"] = self.model.addConstr(lin_expr <= 1.0)

        self.model.update()

    def _add_constraints_4_5(self) -> None:
        """Add two sets of constraints to force the model to ensure that
        the battery never underpass the minimum threshold and that z
        represents the UAV with the least battery.
        """
        self.constraints_4 = {}
        self.constraints_5 = {}
        for uav, uav_value in self.uavs.items():
            uav_batt_lvl = uav_value["batt_lvl"]
            cpu_utilization: gp.LinExpr = PCM.get_cpu_utilization(
                services=self.services,
                uav=(uav, uav_value),
                requests=self.requests,
                variables=self.X_u_m)
            uplink_data_rate: gp.LinExpr = PCM.get_uplink_data_rate(
                services=self.services,
                uav=(uav, uav_value),
                requests=self.requests,
                variables=self.X_u_m)
            downlink_data_rate: gp.LinExpr = PCM.get_downlink_data_rate(
                services=self.services,
                uav=(uav, uav_value),
                requests=self.requests,
                variables=self.X_u_m)
            energy_consumption: gp.LinExpr = PCM.get_energy_consumption(
                cpu_utilization=cpu_utilization,
                downlink_data_rate=downlink_data_rate,
                uplink_data_rate=uplink_data_rate,
                time_slot_interval=self.time_slot_interval)
            self.constraints_4[f"c4_{uav}"] = self.model.addConstr(uav_batt_lvl - energy_consumption >= 13.986)
            self.constraints_5[f"c4_{uav}"] = self.model.addConstr(uav_batt_lvl - energy_consumption >= self.z)
        self.model.update()

    def _add_obj_function(self) -> None:
        """Set the objective function to force the model to
        """
        self.model.setObjective(expr=self.z, sense=gp.GRB.MAXIMIZE)
        self.model.update()

    def setup_model(self) -> None:
        """Sequentially call all the methods to add variables,
        constraints and the objective function."""
        self._add_variables()
        self._add_constraints_1()
        self._add_constraints_2()
        self._add_constraints_3()
        self._add_constraints_4_5()
        self._add_obj_function()

    def solve(self) -> None:
        """_summary_
        """
        self.model.optimize()

    def print_solution(self) -> None:
        """_summary_
        """
        output = pd.DataFrame()
        vars = []
        uav_deployment: list[str]
        print_lambda = lambda x: f"{x[0]} {x[1]} {x[2]} {x[3]}"
        uav_data: dict[str, Any]
        uav_deployment_data: list[int]
        for uav, uav_value in self.uavs.items():
            ram_vars: dict[gp.Var, float] = {}
            uav_data = {}
            uav_deployment = ["×", "×", "×", "×"]
            uav_deployment_data = [0, 0, 0, 0]
            for i, serv in enumerate(self.services.keys()):
                for instance in self.services[serv].keys():
                    if (bool(self.X_u_m[uav, instance].X) == True):
                                uav_deployment[i] = "✓"
                                uav_deployment_data[i] = 1
            uav_data["services_deployed"] = uav_deployment_data
            cpu_utilization: gp.LinExpr = PCM.get_cpu_utilization(
                services=self.services,
                uav=(uav, uav_value),
                requests=self.requests,
                variables=self.X_u_m)
            uav_data["cpu_utilization"] = cpu_utilization.getValue()*100

            uplink_data_rate: gp.LinExpr = PCM.get_uplink_data_rate(
                services=self.services,
                uav=(uav, uav_value),
                requests=self.requests,
                variables=self.X_u_m)
            uav_data["uplink_data_rate"] = uplink_data_rate.getValue()
            downlink_data_rate: gp.LinExpr = PCM.get_downlink_data_rate(
                services=self.services,
                uav=(uav, uav_value),
                requests=self.requests,
                variables=self.X_u_m)
            uav_data["downlink_data_rate"] = downlink_data_rate.getValue()
            power_consumption: gp.LinExpr = PCM.get_energy_consumption(
                cpu_utilization=cpu_utilization,
                uplink_data_rate=uplink_data_rate,
                downlink_data_rate=downlink_data_rate,
                time_slot_interval=self.time_slot_interval)
            uav_data["battery"] = uav_value['batt_lvl'] - power_consumption.getValue()
            uav_data["step_consumption"] = power_consumption.getValue()
            for serv in self.services.keys():
                for instance_key, instance_value in self.services[serv].items():
                    ram_vars[self.X_u_m[(uav, instance_key)]] = instance_value["ram_req"]
            ram_usage: gp.LinExpr = gp.quicksum(
                [var*coeff for var, coeff in ram_vars.items()])
            uav_data["ram_usage"] = ram_usage.getValue()
            self.output[uav].append(uav_data)
            print(f"{str(uav).ljust(6)}: services -> {print_lambda(uav_deployment)}\tbattery -> {str(round(uav_value['batt_lvl'] - power_consumption.getValue(), 2)).ljust(5, '0')} Wh\tstep consumption -> {str(round(power_consumption.getValue(), 2)).ljust(4,'0')} Wh\tCPU -> {str(round(cpu_utilization.getValue()*100,2)).ljust(6)}%\tRAM -> {ram_usage.getValue()} Gb\tR down -> {str(round(downlink_data_rate.getValue(), 2)).ljust(5,'0')} Mbps\tR up -> {str(round(uplink_data_rate.getValue(), 2)).ljust(5,'0')} Mbps")


    def print_uavs_battery_lvls(self) -> None:
        """_summary_
        """

        for uav, uav_value in self.uavs.items():
            cpu_utilization: gp.LinExpr = PCM.get_cpu_utilization(
                services=self.services,
                uav=(uav, uav_value),
                requests=self.requests,
                variables=self.X_u_m)
            uplink_data_rate: gp.LinExpr = PCM.get_uplink_data_rate(
                services=self.services,
                uav=(uav, uav_value),
                requests=self.requests,
                variables=self.X_u_m)
            downlink_data_rate: gp.LinExpr = PCM.get_downlink_data_rate(
                services=self.services,
                uav=(uav, uav_value),
                requests=self.requests,
                variables=self.X_u_m)
            power_consumption: gp.LinExpr = PCM.get_energy_consumption(
                cpu_utilization=cpu_utilization,
                uplink_data_rate=uplink_data_rate,
                downlink_data_rate=downlink_data_rate,
                time_slot_interval=self.time_slot_interval)
            print(f"{uav}: {round(uav_value['batt_lvl'] - power_consumption.getValue(), 2)} Wh\t\t(step power consumption = {round(power_consumption.getValue(), 2)} Wh)")

    def step(self) -> None:
        """In every step new requests accumulate and UAV resources must
        be recalculated.
        """


        for uav, uav_value in self.uavs.items():
            cpu_utilization: gp.LinExpr = PCM.get_cpu_utilization(
                services=self.services,
                uav=(uav, uav_value),
                requests=self.requests,
                variables=self.X_u_m)
            uplink_data_rate: gp.LinExpr = PCM.get_uplink_data_rate(
                services=self.services,
                uav=(uav, uav_value),
                requests=self.requests,
                variables=self.X_u_m)
            downlink_data_rate: gp.LinExpr = PCM.get_downlink_data_rate(
                services=self.services,
                uav=(uav, uav_value),
                requests=self.requests,
                variables=self.X_u_m)
            power_consumption: gp.LinExpr = PCM.get_energy_consumption(
                cpu_utilization=cpu_utilization,
                uplink_data_rate=uplink_data_rate,
                downlink_data_rate=downlink_data_rate,
                time_slot_interval=self.time_slot_interval)

            self.uavs[uav]["batt_lvl"] -= power_consumption.getValue()

        new_requests: dict[tuple[str, str], float] = RG.generate_requests(
            uavs=self.uavs,
            services=self.services,
            n_requests=self.n_requests)

        for new_request_id, new_request_value in new_requests.items():
            self.requests[new_request_id] = new_request_value

        self.model = gp.Model(env=env)

    def output_to_csv(self, output_path: Path) -> None:
        """Save the results of the run to a file.

        Args:
            output_path (Path): The path of the output file.
        """

        columns: list[str] = ["uav", "step"]
        for i, _ in enumerate(self.services.keys()):
            columns.append(f"service_{i}")
        columns += ["battery", "step_consumption", "cpu_utilization", "ram_usage", "downlink_data_rate", "uplink_data_rate"]
        output_data: list = []

        row: dict[str, Any]
        for uav, data in self.output.items():
            row = {}
            for i,step in enumerate(data):
                row = {"uav": uav,
                       "step": i}
                for field_name, field_value in step.items():
                    if (type(field_value) == list):
                        for j, service in enumerate(field_value):
                            row[f"service_{j}"] = service
                    else:
                        row[field_name] = field_value
                output_data.append(row)

        df: pd.DataFrame = pd.DataFrame(data=output_data)
        df.to_csv(path_or_buf=output_path, index=False)