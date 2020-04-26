class PID_Controller:
    def __init__(self):
        self.SP = 0
        self.PV = 0
        self.P = 0
        self.I = 0
        self.D = 0
        self.KI = 0
        self.KD = 0
        self.dt = 0
        self.ffwd = 0
        self.m = 0
        self.y = 0
        self.b = 0
        
    def reset(self):
        self.ffwd = 0
        self.m = 0
        self.y = 0
        self.b = 0

    def update_derivative(self):        
        self.y = self.y + self.dt * (self.PV - self.y) / (self.dt + self.D / self.KD)

    def update_proportional(self):        
        self.m = self.b + self.ffwd + (100 / self.P) * (self.SP - self.PV - self.KD * (self.PV - self.y))
        if self.m > 100:
            self.m = 100
        if self.m < -100:
            self.m = -100

    def update_integral(self):  
        if abs(self.SP - self.PV) * 2 > self.KI:
            i = 100000
        else:
            i = self.I

        self.b = self.b + self.dt * (self.m - self.ffwd - self.b) / (self.dt + i)


    def update(self):        
        self.update_derivative()
        self.update_proportional()
        self.update_integral()

        return self.m
