from math import sqrt
import joblib

class Peltier:
    def __init__(self):
        self.QC = [
            -8.0217,
             1.1891E-01,
             1.9009E+01,
            -1.2212,
            -6.8303E-01,
             2.1962E-03,
            -1.0342E-05,
             1.7197E-02,
            -3.9014E-03,
            -3.7383E-02
        ]
        self.QH = [
             1.0741,
            -0.013303,
             0.066409,
            -1.64E-04,
             2.99E-07,
             0.09032,
             9.17E-05,
            -1.21E-06,
            -1.57E-04,
            -5.29E-04
        ]
        self.V = [
            -0.14174,
             0.0023421,
             1.9298,
            -7.85E-07,
             0.061427,
            -1.47E-05,
            -2.72E-07,
             0.010453,
             4.90E-05,
            -0.0051499
        ]
        self.stage = "heat"
        self.model = self.load_model("peltier_trained_model.ml")

    def load_model(self, path):
        return joblib.load(path)

    def output(self, qpid, heat_sink_temp, block_temp, max_heat_current, max_cool_current):
        if self.stage == "heat":
            dT = block_temp - heat_sink_temp
            Iset =  self.QH[0] \
                    + self.QH[1] * block_temp \
                    + self.QH[2] * qpid \
                    + self.QH[3] * qpid**2 \
                    + self.QH[4] * qpid**3 \
                    + self.QH[5] * dT \
                    + self.QH[6] * dT**2 \
                    + self.QH[7] * dT**3 \
                    + self.QH[8] * block_temp * qpid \
                    + self.QH[9] * block_temp * dT

        elif self.stage == "cool":
            dT = heat_sink_temp - block_temp
            A = self.QC[3]
            B = self.QC[2] + self.QC[7] * heat_sink_temp + self.QC[9] * dT
            C = -qpid \
                + self.QC[0] \
                + self.QC[1] * heat_sink_temp \
                + self.QC[4] * dT \
                + self.QC[5] * dT**2 \
                + self.QC[6] * dT**3 \
                + self.QC[8] * dT * heat_sink_temp
            if B*B < 4*A*C:
                Iset = max_heat_current
            else:
                Iset = (-B + sqrt(B*B - 4*A*C)) / (A + A)
        else:
            pass
        if Iset > max_heat_current:
            Iset = max_heat_current
        elif Iset < -max_cool_current:
            Iset = -max_cool_current      
        Imeasure = self.model.predict([[heat_sink_temp, block_temp, Iset]])[0]
        return Iset, Imeasure
