import random

class DNA:
    def __init__(self, pid_specs, dnaLength=5):
        self.dnaLength = dnaLength
        self.genes = self.init_DNA(dnaLength)
        self.specs = self.save_specs(pid_specs)        
        self.score = 0
    
    def save_specs(self, pid_specs):
        specs = []
        specs.append([pid_specs.Pmin,  pid_specs.Pmax,  pid_specs.Pres])
        specs.append([pid_specs.Imin,  pid_specs.Imax,  pid_specs.Ires])
        specs.append([pid_specs.Dmin,  pid_specs.Dmax,  pid_specs.Dres])
        specs.append([pid_specs.KImin, pid_specs.KImax, pid_specs.KIres])
        specs.append([pid_specs.KDmin, pid_specs.KDmax, pid_specs.KDres])
        return specs

    def rand_gene(self, loc):
        min_val    = self.specs[loc][0]
        max_val    = self.specs[loc][1]
        resolution = self.specs[loc][2]
        self.genes[loc] = random.randint(int(min_val / resolution), int(max_val / resolution)) * resolution

    def init_DNA(self, dnaLength):
        genes = []
        for i in range(0, dnaLength):
            genes.append(0)
        return genes

    def rand_DNA(self):
        for i in range(0, self.dnaLength):
            self.rand_gene(i)

    def blend_in(self, tbc_controller):
        tbc_controller.pid.P  = self.genes[0]
        tbc_controller.pid.I  = self.genes[1]
        tbc_controller.pid.D  = self.genes[2]
        tbc_controller.pid.KI = self.genes[3]
        tbc_controller.pid.KD = self.genes[4]