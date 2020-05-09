import random

class DNA:
    def __init__(self, pid_specs):        
        self.init_DNA()
        self.create_specs(pid_specs)
        self.alive = True   
        self.score = 0
    
    def create_specs(self, pid_specs):
        self.specs = []
        for i in range(0, 9):
            self.specs.append([pid_specs.Pmin,  pid_specs.Pmax,  pid_specs.Pres])
            self.specs.append([pid_specs.Imin,  pid_specs.Imax,  pid_specs.Ires])
            self.specs.append([pid_specs.Dmin,  pid_specs.Dmax,  pid_specs.Dres])
            self.specs.append([pid_specs.KImin, pid_specs.KImax, pid_specs.KIres])
            self.specs.append([pid_specs.KDmin, pid_specs.KDmax, pid_specs.KDres])        

    def rand_gene(self, loc):
        min_val    = self.specs[loc][0]
        max_val    = self.specs[loc][1]
        resolution = self.specs[loc][2]
        self.genes[loc] = random.randint(int(min_val / resolution), int(max_val / resolution)) * resolution

    def init_DNA(self):
        self.genes = []
        for i in range(0, 9):
            for j in range(0, 5):
                self.genes.append(0)        
        self.dnaLength = len(self.genes)

    def rand_DNA(self):
        for i in range(0, self.dnaLength):
            self.rand_gene(i)

    def blend_in(self, tbc_controller):
        tbc_controller.pid_const["Ramp Up"]["P"]  = self.genes[0]
        tbc_controller.pid_const["Ramp Up"]["I"]  = self.genes[1]
        tbc_controller.pid_const["Ramp Up"]["D"]  = self.genes[2]
        tbc_controller.pid_const["Ramp Up"]["KI"] = self.genes[3]
        tbc_controller.pid_const["Ramp Up"]["KD"] = self.genes[4]
        
        tbc_controller.pid_const["Overshoot Over"]["P"]  = self.genes[5]
        tbc_controller.pid_const["Overshoot Over"]["I"]  = self.genes[6]
        tbc_controller.pid_const["Overshoot Over"]["D"]  = self.genes[7]
        tbc_controller.pid_const["Overshoot Over"]["KI"] = self.genes[8]
        tbc_controller.pid_const["Overshoot Over"]["KD"] = self.genes[9]

        tbc_controller.pid_const["Hold Over"]["P"]  = self.genes[10]
        tbc_controller.pid_const["Hold Over"]["I"]  = self.genes[11]
        tbc_controller.pid_const["Hold Over"]["D"]  = self.genes[12]
        tbc_controller.pid_const["Hold Over"]["KI"] = self.genes[13]
        tbc_controller.pid_const["Hold Over"]["KD"] = self.genes[14]

        tbc_controller.pid_const["Land Over"]["P"]  = self.genes[15]
        tbc_controller.pid_const["Land Over"]["I"]  = self.genes[16]
        tbc_controller.pid_const["Land Over"]["D"]  = self.genes[17]
        tbc_controller.pid_const["Land Over"]["KI"] = self.genes[18]
        tbc_controller.pid_const["Land Over"]["KD"] = self.genes[19]

        tbc_controller.pid_const["Hold"]["P"]  = self.genes[20]
        tbc_controller.pid_const["Hold"]["I"]  = self.genes[21]
        tbc_controller.pid_const["Hold"]["D"]  = self.genes[22]
        tbc_controller.pid_const["Hold"]["KI"] = self.genes[23]
        tbc_controller.pid_const["Hold"]["KD"] = self.genes[24]

        tbc_controller.pid_const["Ramp Down"]["P"]  = self.genes[25]
        tbc_controller.pid_const["Ramp Down"]["I"]  = self.genes[26]
        tbc_controller.pid_const["Ramp Down"]["D"]  = self.genes[27]
        tbc_controller.pid_const["Ramp Down"]["KI"] = self.genes[28]
        tbc_controller.pid_const["Ramp Down"]["KD"] = self.genes[29]

        tbc_controller.pid_const["Overshoot Under"]["P"]  = self.genes[30]
        tbc_controller.pid_const["Overshoot Under"]["I"]  = self.genes[31]
        tbc_controller.pid_const["Overshoot Under"]["D"]  = self.genes[32]
        tbc_controller.pid_const["Overshoot Under"]["KI"] = self.genes[33]
        tbc_controller.pid_const["Overshoot Under"]["KD"] = self.genes[34]

        tbc_controller.pid_const["Hold Under"]["P"]  = self.genes[35]
        tbc_controller.pid_const["Hold Under"]["I"]  = self.genes[36]
        tbc_controller.pid_const["Hold Under"]["D"]  = self.genes[37]
        tbc_controller.pid_const["Hold Under"]["KI"] = self.genes[38]
        tbc_controller.pid_const["Hold Under"]["KD"] = self.genes[39]                

        tbc_controller.pid_const["Land Under"]["P"]  = self.genes[40]
        tbc_controller.pid_const["Land Under"]["I"]  = self.genes[41]
        tbc_controller.pid_const["Land Under"]["D"]  = self.genes[42]
        tbc_controller.pid_const["Land Under"]["KI"] = self.genes[43]
        tbc_controller.pid_const["Land Under"]["KD"] = self.genes[44]           