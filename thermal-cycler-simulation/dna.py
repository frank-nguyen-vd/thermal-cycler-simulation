import random

class DNA:
    def __init__(self, pid_specs, dnaLength=5):        
        self.dnaLength = dnaLength
        self.genes = self.init_DNA(dnaLength)
        self.specs = self.save_specs(pid_specs)
        self.score = 0

    def random_value(self, min_val, max_val, resolution):        
        return random.randint(int(min_val / resolution), int(max_val / resolution) + 1) * resolution

    def blend_in(self, tbc_controller):
        tbc_controller.pid.P  = self.genes[0]
        tbc_controller.pid.I  = self.genes[1]
        tbc_controller.pid.D  = self.genes[2]
        tbc_controller.pid.KI = self.genes[3]
        tbc_controller.pid.KD = self.genes[4]