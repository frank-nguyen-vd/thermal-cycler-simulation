import random

class DNA:
    def __init__(self):        
        self.generate_DNA_Specs()
        self.dnaLength = len(self.specs)
        self.dna = [0] * self.dnaLength
        self.alive = True   
        self.score = 0
        self.measured_up_rate = 0
        self.target_up_rate = 0
        self.measured_down_rate = 0
        self.target_down_rate = 0
        self.heat_overshoot = 0
        self.cool_overshoot = 0
        self.max_up_deviation = 0
        self.max_down_deviation = 0
    
    def copy(self):
        clone                    = DNA()
        clone.dna                = self.dna.copy()
        clone.score              = self.score
        clone.measured_up_rate   = self.measured_up_rate
        clone.target_up_rate     = self.target_up_rate
        clone.measured_down_rate = self.measured_down_rate
        clone.target_down_rate   = self.target_down_rate
        clone.heat_overshoot     = self.heat_overshoot
        clone.cool_overshoot     = self.cool_overshoot
        clone.max_up_deviation   = self.max_up_deviation
        clone.max_down_deviation = self.max_down_deviation
        return clone
    
    def generate_PID_Specs(self):
        Pmin = 0.01 # P must be positive
        Pmax = 10
        Pres = 0.01

        Imin = 0
        Imax = 10
        Ires = 0.001

        Dmin = 0
        Dmax = 10
        Dres = 0.0001

        KImin = 0
        KImax = 10
        KIres = 0.1

        KDmin = 1 # KD must be positive
        KDmax = 10
        KDres = 0.1

        specs = []
        for stage in ["Ramp Up", "Overshoot Over", "Hold Over", "Land Over", 
                      "Hold", "Ramp Down", "Overshoot Under", "Hold Under", 
                      "Land Under"]:
            specs.append([Pmin,  Pmax,  Pres, f"P ({stage})"])
            specs.append([Imin,  Imax,  Ires, f"I ({stage})"])
            specs.append([Dmin,  Dmax,  Dres, f"D ({stage})"])
            specs.append([KImin, KImax, KIres, f"KI ({stage})"])
            specs.append([KDmin, KDmax, KDres, f"KD ({stage})"])
        return specs

    def generate_SmpVol_Specs(self):
        specs = []

        min_val = 0
        max_val = 10
        resolution = 0.1
        specs.append([min_val, max_val, resolution, "Max Heat Overshoot"])


        min_val = 0
        max_val = 10
        resolution = 0.1
        specs.append([min_val, max_val, resolution, "Max Cool Overshoot"])

        min_val = 0
        max_val = 5
        resolution = 0.1
        specs.append([min_val, max_val, resolution, "Max Heat Sample Window"])
        
        min_val = 0
        max_val = 5
        resolution = 0.1
        specs.append([min_val, max_val, resolution, "Max Cool Sample Window"])

        min_val = 10 # Max Hold Power cannot be 0
        max_val = 100
        resolution = 10
        specs.append([min_val, max_val, resolution, "Max Hold Power"])

        min_val = 10 # Max Ramp Power cannot be 0
        max_val = 500
        resolution = 10
        specs.append([min_val, max_val, resolution, "Max Ramp Power"])

        min_val = 0
        max_val = 5
        resolution = 0.1
        specs.append([min_val, max_val, resolution, "Max Heat Block Window"])

        min_val = 0
        max_val = 5
        resolution = 0.1
        specs.append([min_val, max_val, resolution, "Max Cool Block Window"])

        min_val = 0
        max_val = 5
        resolution = 0.1
        specs.append([min_val, max_val, resolution, "Heat Overshoot Attenuation"])

        min_val = 0
        max_val = 1
        resolution = 0.01
        specs.append([min_val, max_val, resolution, "Heat Overshoot Activation Ramp Rate Factor"])

        min_val = 0
        max_val = 1
        resolution = 0.01
        specs.append([min_val, max_val, resolution, "Heat Overshoot Activation PID Set Point"])

        min_val = 0
        max_val = 5
        resolution = 0.1
        specs.append([min_val, max_val, resolution, "Cool Overshoot Attenuation"])

        min_val = 0
        max_val = 1
        resolution = 0.01
        specs.append([min_val, max_val, resolution, "Cool Overshoot Activation Ramp Rate Factor"])

        min_val = 0
        max_val = -1
        resolution = -0.01
        specs.append([min_val, max_val, resolution, "Cool Overshoot Activation PID Set Point"])

        return specs

    def generate_DNA_Specs(self):
        specs = self.generate_PID_Specs() + self.generate_SmpVol_Specs()

        min_val = 1
        max_val = 6
        resolution = 0.1
        specs.append([min_val, max_val, resolution, "Temp Control Over Ramp Rate Limit"])

        min_val = 1
        max_val = 6
        resolution = 0.1
        specs.append([min_val, max_val, resolution, "Temp Control Under Ramp Rate Limit"])

        min_val = 0
        max_val = 3
        resolution = 0.1
        specs.append([min_val, max_val, resolution, "Temp Control Over Block Window"])

        min_val = 0
        max_val = 3
        resolution = 0.1
        specs.append([min_val, max_val, resolution, "Temp Control Under Block Window"])

        self.specs = specs

    def mutate_gene(self, loc):
        resolution = self.specs[loc][2]
        min_val    = int(self.specs[loc][0] / resolution)
        max_val    = int(self.specs[loc][1] / resolution)
        self.dna[loc] = random.randint(min_val, max_val) * resolution

    def generate_DNA(self):        
        for i in range(0, self.dnaLength):
            self.mutate_gene(i)

    def blend_in(self, tbc_controller):
        tbc_controller.pid_const["Ramp Up"]["P"]  = self.dna[0]
        tbc_controller.pid_const["Ramp Up"]["I"]  = self.dna[1]
        tbc_controller.pid_const["Ramp Up"]["D"]  = self.dna[2]
        tbc_controller.pid_const["Ramp Up"]["KI"] = self.dna[3]
        tbc_controller.pid_const["Ramp Up"]["KD"] = self.dna[4]
        
        tbc_controller.pid_const["Overshoot Over"]["P"]  = self.dna[5]
        tbc_controller.pid_const["Overshoot Over"]["I"]  = self.dna[6]
        tbc_controller.pid_const["Overshoot Over"]["D"]  = self.dna[7]
        tbc_controller.pid_const["Overshoot Over"]["KI"] = self.dna[8]
        tbc_controller.pid_const["Overshoot Over"]["KD"] = self.dna[9]

        tbc_controller.pid_const["Hold Over"]["P"]  = self.dna[10]
        tbc_controller.pid_const["Hold Over"]["I"]  = self.dna[11]
        tbc_controller.pid_const["Hold Over"]["D"]  = self.dna[12]
        tbc_controller.pid_const["Hold Over"]["KI"] = self.dna[13]
        tbc_controller.pid_const["Hold Over"]["KD"] = self.dna[14]

        tbc_controller.pid_const["Land Over"]["P"]  = self.dna[15]
        tbc_controller.pid_const["Land Over"]["I"]  = self.dna[16]
        tbc_controller.pid_const["Land Over"]["D"]  = self.dna[17]
        tbc_controller.pid_const["Land Over"]["KI"] = self.dna[18]
        tbc_controller.pid_const["Land Over"]["KD"] = self.dna[19]

        tbc_controller.pid_const["Hold"]["P"]  = self.dna[20]
        tbc_controller.pid_const["Hold"]["I"]  = self.dna[21]
        tbc_controller.pid_const["Hold"]["D"]  = self.dna[22]
        tbc_controller.pid_const["Hold"]["KI"] = self.dna[23]
        tbc_controller.pid_const["Hold"]["KD"] = self.dna[24]

        tbc_controller.pid_const["Ramp Down"]["P"]  = self.dna[25]
        tbc_controller.pid_const["Ramp Down"]["I"]  = self.dna[26]
        tbc_controller.pid_const["Ramp Down"]["D"]  = self.dna[27]
        tbc_controller.pid_const["Ramp Down"]["KI"] = self.dna[28]
        tbc_controller.pid_const["Ramp Down"]["KD"] = self.dna[29]

        tbc_controller.pid_const["Overshoot Under"]["P"]  = self.dna[30]
        tbc_controller.pid_const["Overshoot Under"]["I"]  = self.dna[31]
        tbc_controller.pid_const["Overshoot Under"]["D"]  = self.dna[32]
        tbc_controller.pid_const["Overshoot Under"]["KI"] = self.dna[33]
        tbc_controller.pid_const["Overshoot Under"]["KD"] = self.dna[34]

        tbc_controller.pid_const["Hold Under"]["P"]  = self.dna[35]
        tbc_controller.pid_const["Hold Under"]["I"]  = self.dna[36]
        tbc_controller.pid_const["Hold Under"]["D"]  = self.dna[37]
        tbc_controller.pid_const["Hold Under"]["KI"] = self.dna[38]
        tbc_controller.pid_const["Hold Under"]["KD"] = self.dna[39]                

        tbc_controller.pid_const["Land Under"]["P"]  = self.dna[40]
        tbc_controller.pid_const["Land Under"]["I"]  = self.dna[41]
        tbc_controller.pid_const["Land Under"]["D"]  = self.dna[42]
        tbc_controller.pid_const["Land Under"]["KI"] = self.dna[43]
        tbc_controller.pid_const["Land Under"]["KD"] = self.dna[44]

        tbc_controller.maxHeatBlkOS      = self.dna[45]
        tbc_controller.maxCoolBlkOS      = self.dna[46]
        tbc_controller.maxHeatBlkWin     = self.dna[47]
        tbc_controller.maxCoolBlkWin     = self.dna[48]
        tbc_controller.qMaxHoldPid       = self.dna[49]
        tbc_controller.qMaxRampPid       = self.dna[50]
        tbc_controller.maxHeatBlkWin     = self.dna[51]
        tbc_controller.maxCoolBlkWin     = self.dna[52]
        tbc_controller.heat_brake_const  = self.dna[53]
        tbc_controller.heatSpCtrlActivRR = self.dna[54]
        tbc_controller.heatSpCtrlActivSP = self.dna[55]
        tbc_controller.cool_brake_const  = self.dna[56]
        tbc_controller.coolSpCtrlActivRR = self.dna[57]
        tbc_controller.coolSpCtrlActivSP = self.dna[58]

        tbc_controller.smoothRegionOverRR   = self.dna[59]
        tbc_controller.smoothRegionUnderRR  = self.dna[60]
        tbc_controller.smoothRegionOverWin  = self.dna[61]
        tbc_controller.smoothRegionUnderWin = self.dna[62]