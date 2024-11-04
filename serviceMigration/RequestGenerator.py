import random
random.seed(20)

class RequestGenerator():

    @staticmethod
    def generate_requests(uavs: dict[str, dict[str, float]],
                          services: dict[str, dict[str, dict[str, float|int]]],
                          n_requests: int) -> dict[tuple[str, str], float]:
        """Given n_requests, the uavs and the services, generate
        n_requests random service requests asigned to random UAVs.

        Args:
            uavs (dict[str, dict[str, float]]): The uavs.
            services (dict[str, dict[str, float | int]]): The services.
            n_request (int): The number of requests to generate.

        Returns:
            dict[tuple[str, str], float]: The dict with the number of
            requests of each uav-service combination.
        """
        requests: dict[tuple[str, str], float] = {}
        for uav in uavs.keys():
            for serv in services.keys():
                requests[uav, serv] = 0

        for _ in range(n_requests):
            uav = random.choice(list(uavs.keys()))
            serv = random.choice(list(services.keys()))
            requests[uav, serv] += 1
        return requests