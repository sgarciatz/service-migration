import gurobipy as gp

class PowerConsumptionModel(object):
    """Calulates the instataneous power consumption of a Raspberry Pi 4.

    It is supposed that only its WiFi network interface is being used.
    The Ethernet network interface is assumed to be idle.

    For the calulations, the model proposed in the 'PowerPi: Measuring and
    Modeling the Power Consumption of the Raspberry Pi' paper by Kaup et
    al..
    """

    @staticmethod
    def p_idle() -> float:
        """Returns the power of an idle Raspberry Pi 4.

        Returns:
            float: Returns the power of an idle Raspberry Pi 4.
        """
        return 1.5778

    @staticmethod
    def p_eth_idle() -> float:
        """Returns the power of an idle Ethernet network interface of a
        Raspberry Pi 4.

        Returns:
            float: Returns the power of an idle Ethernet network
            interface Raspberry Pi 4.
        """
        return 0.294

    @staticmethod
    def p_wifi_idle() -> float:
        """Returns the power of an idle WiFi network interface of a
        Raspberry Pi 4.

        Returns:
            float: Returns the power of an idle WiFi network interface
            Raspberry Pi 4.
        """
        return 0.942

    @staticmethod
    def p_cpu(cpu_utilization: gp.LinExpr) -> gp.LinExpr:
        """Returns the cpu_utilization dependent power consumption of a
        Raspberry Pi 4.

        Args:
            cpu_utilization (gp.LinExpr):The cpu_utilization rate.

        Returns:
            gp.LinExpr: The cpu_utilization dependent power consumption of a
            Raspberry Pi 4.
        """
        return 0.181 * cpu_utilization

    @staticmethod
    def p_wifi_down(downlink_data_rate: gp.LinExpr) -> gp.LinExpr:
        """Returns the downlink data-rate dependent power consumption of
        a Raspberry Pi 4.

        Args:
            down_link_data_rate (float): The downlink data_rate in Mbps.

        Returns:
            float: the downlink data-rate dependent power consumption of
        a Raspberry Pi 4.
        """
        return 0.057 + 4.813e-3 * downlink_data_rate

    @staticmethod
    def p_wifi_up(uplink_data_rate: gp.LinExpr) -> gp.LinExpr:
        """Returns the downlink data-rate dependent power consumption of
        a Raspberry Pi 4.

        Args:
            uplink_data_rate (float): The downlink data_rate in Mbps.

        Returns:
            float: the downlink data-rate dependent power consumption of
        a Raspberry Pi 4.
        """
        return 0.064 + 4.813e-3 * uplink_data_rate

    @staticmethod
    def get_cpu_utilization(services: dict[str, dict[str, dict[str, float]]],
                            uav: tuple[str, dict[str, float]],
                            requests: dict[tuple[str, str], float],
                            variables: dict[tuple[str, str], gp.Var]
                            ) -> gp.LinExpr:
        """Calculates the cpu utilization given the services deployed in
        the uav and the requests.

        Args:
            services (dict[str, dict[str, float]]): A dictionary with
            the information about the microservices.
            uavs (dict[str, dict[str, float]]): A dictionary with a
            single entry with the info about the uav.
            variables (dict[tuple[str, str], gp.Var]): A dictionary with
            all the binary variables that indicate wheter a microservice
            is deployed in uav.

        Returns:
            gp.LinExpr: the cpu utilization given the services deployed
            in the uav.
        """
        cpu_utilization: gp.LinExpr
        aux_vars: dict[gp.Var, tuple[float, float, float]] = {}
        uav_cpu_freq: float = uav[1]["cpu_freq"]
        for serv in services.keys():
            for instance_key, instance_value in services[serv].items():
                aux_vars[variables[uav[0], instance_key]] = (instance_value["cpu_cycles_per_deploy"],
                                                             instance_value["cpu_cycles_per_request"],
                                                             requests[uav[0], serv])

        cpu_utilization = gp.quicksum(
            [var * (v1 + v2 * v3) for var, (v1, v2, v3) in aux_vars.items()]
        )
        cpu_utilization = cpu_utilization / uav_cpu_freq
        return cpu_utilization

    @staticmethod
    def get_downlink_data_rate(services: dict[str, dict[str, dict[str, float]]],
                               uav: tuple[str, dict[str, float]],
                               requests: dict[tuple[str, str], float],
                               variables: dict[tuple[str, str], gp.Var]
                              ) -> gp.LinExpr:
        """Calculates the downlink data rate given the services deployed
        in the uav and the requests.

        Args:
            services (dict[str, dict[str, float]]): A dictionary with
            the information about the microservices.
            uavs (dict[str, dict[str, float]]): A dictionary with a
            single entry with the info about the uav.
            variables (dict[tuple[str, str], gp.Var]): A dictionary with
            all the binary variables that indicate wheter a microservice
            is deployed in uav.

        Returns:
            gp.LinExpr: The downlink data rate given the services
            deployed in the uav.
        """
        data_rate: gp.LinExpr
        aux_vars: list[tuple[float, float]] = []
        for serv in services.keys():
            aux_vars.append((services[serv][f"{serv}_0"]["input_size"],
                            requests[uav[0], serv]))
        data_rate = gp.quicksum(
            [v1 * v2  for (v1, v2) in aux_vars]
        )

        return data_rate

    @staticmethod
    def get_uplink_data_rate(services: dict[str, dict[str, dict[str, float]]],
                             uav: tuple[str, dict[str, float]],
                             requests: dict[tuple[str, str], float],
                             variables: dict[tuple[str, str], gp.Var]
                            ) -> gp.LinExpr:
        """Calculates the uplink data rate given the services deployed
        in the uav and the requests.

        Args:
            services (dict[str, dict[str, float]]): A dictionary with
            the information about the microservices.
            uavs (dict[str, dict[str, float]]): A dictionary with a
            single entry with the info about the uav.
            variables (dict[tuple[str, str], gp.Var]): A dictionary with
            all the binary variables that indicate wheter a microservice
            is deployed in uav.

        Returns:
            gp.LinExpr: The uplink data rate given the services deployed
            in the uav.
        """
        data_rate: gp.LinExpr
        aux_vars: dict[gp.Var, tuple[float, float]] = {}
        services_instances: dict[str, dict[str, gp.Var]] = {}
        is_deployed: gp.LinExpr
        serv_data_rates: list[gp.LinExpr] = []
        for serv in services.keys():
            is_deployed = gp.quicksum(
                [variables[uav[0], k] for k in services[serv].keys()])
            serv_data_rates.append(
                (1.0 - is_deployed) * services[serv][f"{serv}_0"]["input_size"] * requests[uav[0], serv])
        return gp.quicksum(serv_data_rates)


    @staticmethod
    def get_energy_consumption(cpu_utilization: gp.LinExpr,
                               uplink_data_rate: gp.LinExpr,
                               downlink_data_rate: gp.LinExpr,
                               time_slot_interval: float
                              ) -> gp.LinExpr:
        """Calculates the energy consumption given the cpu utilization
        rate and the downlink and uplink data rates.

        Args:
            cpu_utilization (gp.LinExpr): The CPU utilization of a UAV.
            uplink_data_rate (gp.LinExpr): The uplink data rate of a
                UAV.
            downlink_data_rate (gp.LinExpr]): The downlink data rate of
                a UAV.
            time_slot_interval (float): The duration of a time slot
                expressed in hours.

        Returns:
            gp.LinExpr: The energy consumption of the uav.
        """

        return time_slot_interval * (PowerConsumptionModel.p_idle() +\
                                     PowerConsumptionModel.p_cpu(cpu_utilization=cpu_utilization) +\
                                     PowerConsumptionModel.p_eth_idle() +\
                                     PowerConsumptionModel.p_wifi_idle() +\
                                     PowerConsumptionModel.p_wifi_down(downlink_data_rate=downlink_data_rate) +\
                                     PowerConsumptionModel.p_wifi_up(uplink_data_rate=uplink_data_rate))