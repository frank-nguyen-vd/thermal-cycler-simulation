import random

class DNA:
    def __init__(self, pid_specs):
        self.genes = []
        self.genes.append(self.random_value(pid_specs.Pmin,  pid_specs.Pmax,  pid_specs.Pres))
        self.genes.append(self.random_value(pid_specs.IPmin, pid_specs.Imax,  pid_specs.Ires))
        self.genes.append(self.random_value(pid_specs.Dmin,  pid_specs.Dmax,  pid_specs.Dres))
        self.genes.append(self.random_value(pid_specs.KImin, pid_specs.KImax, pid_specs.KIres))
        self.genes.append(self.random_value(pid_specs.KDmin, pid_specs.KDmax, pid_specs.KDres))
        self.score = 0

    def random_value(self, min_val, max_val, resolution):        
        return random.randint(int(min_val / resolution), int(max_val / resolution) + 1) * resolution