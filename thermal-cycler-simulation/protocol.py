from pcr_machine import PCR_Machine
from tbc_controller import TBC_Controller
import pandas as pd

class Protocol:
    def __init__(self, listSP, listRate, listHold, nCycles):
        self.time = 0
        self.checkpoint = 0
        self.period = 0.2
        self.dt = 0.008        
        self.listSP = listSP
        self.listRate = listRate
        self.listHold = listHold
        self.nCycles = nCycles
        self.pcr_machine = PCR_Machine( "pcr_trained_model.ml",
                                        sample_volume=10,
                                        sample_temp=25,
                                        block_temp=25,
                                        heat_sink_temp=25,
                                        block_rate=0,
                                        sample_rate=0,                                        
                                        amb_temp=25,
                                        update_period=self.dt,
                                        start_time=0
                                        
        )
        self.tbc_controller = TBC_Controller(self.pcr_machine,
                                            start_time=0,
                                            update_period=self.dt,
                                            volume=10
        )
        self.protocolData = pd.DataFrame(columns=["Epoch Time", 
                                             "Sample Temp", 
                                             "Block Temp", 
                                             "Heat Sink Temp",
                                             "QPID",
                                             "Iset",
                                             "Imeasure",
                                             "Control Stage",
                                             "PID SP",
                                             "PID PV"
                                             ]
        )

    def record(self):
        data = {
            "Epoch Time"    :   self.time,
            "Sample Temp"   :   self.pcr_machine.sample_temp,
            "Block Temp"    :   self.pcr_machine.block_temp,
            "Heat Sink Temp":   self.pcr_machine.heat_sink_temp,
            "QPID"          :   self.tbc_controller.qpid,
            "Iset"          :   self.pcr_machine.Iset,
            "Imeasure"      :   self.pcr_machine.Imeasure,
            "Control Stage" :   self.tbc_controller.stage,
            "PID SP"        :   self.tbc_controller.pid.SP,
            "PID PV"        :   self.tbc_controller.pid.PV
        }
        self.protocolData = self.protocolData.append(data, ignore_index=True)

    def tick(self, dt):
        self.time += dt
        if self.time - self.checkpoint >= self.period:
            self.record()
            self.checkpoint = self.time

    def run(self):
        for i in range(0, self.nCycles):
            for setpoint, rate, hold_time in zip(self.listSP, self.listRate, self.listHold):
                self.tbc_controller.ramp_to(setpoint, rate)
                while abs(self.pcr_machine.sample_temp - setpoint) > 1:
                    self.pcr_machine.tick(self.dt)
                    self.tbc_controller.tick(self.dt)
                    self.tick(self.dt)
                hold = 0
                while hold < hold_time:
                    self.pcr_machine.tick(self.dt)
                    self.tbc_controller.tick(self.dt)
                    hold += self.dt
                    self.tick(self.dt)
        self.protocolData.to_csv("protocol.csv", index=False)

if __name__ == "__main__":
    protocol = Protocol([95,60], [100, 100], [35, 35], 6)
    protocol.run()

