class PID_Controller:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self._SP = 0
        self._PV = 0
        self._P = 0
        self._I = 0
        self._D = 0
        self._KI = 0
        self._KD = 0
        self._dt = 0
        self._ffwd = 0
        self._m = 0
        self._y = 0
        self._b = 0

    def update_derivative(self):        
        self._y = self._y + self._dt * (self._PV - self._y) / (self._dt + self._D / self._KD)

    def update_proportional(self):        
        self._m = self._b + self._ffwd + (100 / self._P) * (self._SP - self._PV - self._KD * (self._PV - self._y))
        if self._m > 100:
            self._m = 100
        if self._m < -100:
            self._m = -100

    def update_integral(self):  
        if abs(self._SP - self._PV) * 2 > self._KI:
            i = 100000
        else:
            i = self._I

        self._b = self._b + self._dt * (self._m - self._ffwd - self._b) / (self._dt + i)


    def update(self):        
        self.update_derivative()
        self.update_proportional()
        self.update_integral()


