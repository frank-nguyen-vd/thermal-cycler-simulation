class PID_Specs:

    def __init__(self):
        self.Pmin = 0.5
        self.Pmax = 10
        self.Pres = 0.1

        self.Imin = 0
        self.Imax = 5
        self.Ires = 0.001

        self.Dmin = 0
        self.Dmax = 1
        self.Dres = 0.001

        self.KImin = 1
        self.KImax = 10
        self.KIres = 1

        self.KDmin = 1
        self.KDmax = 10
        self.KDres = 1