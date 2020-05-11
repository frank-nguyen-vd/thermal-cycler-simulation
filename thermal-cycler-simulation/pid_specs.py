class PID_Specs:

    def __init__(self):
        self.Pmin = 0.01 # P must be positive
        self.Pmax = 10
        self.Pres = 0.01

        self.Imin = 0
        self.Imax = 10
        self.Ires = 0.001

        self.Dmin = 0
        self.Dmax = 10
        self.Dres = 0.0001

        self.KImin = 0
        self.KImax = 10
        self.KIres = 0.1

        self.KDmin = 1 # KD must be positive
        self.KDmax = 10
        self.KDres = 0.1