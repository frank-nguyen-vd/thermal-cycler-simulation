from pcr_machine import PCR_Machine
from tbc_controller import TBC_Controller
import pandas as pd

class Protocol:
    def __init__(self, listSP, listRate, listHold, nCycles, Tblock=25, Tamb=25):
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
                                        sample_temp=Tblock,
                                        block_temp=Tblock,
                                        heat_sink_temp=Tamb,
                                        block_rate=0,
                                        sample_rate=0,                                        
                                        amb_temp=Tamb,
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
            "PID PV"        :   self.tbc_controller.pid.PV,
            "PID2 SP"       :   self.tbc_controller.pid2.SP,
            "PID2 PV"       :   self.tbc_controller.pid2.PV

        }
        self.protocolData = self.protocolData.append(data, ignore_index=True)

    def tick(self, dt):
        self.time += dt
        if round(self.time - self.checkpoint, 3) >= self.period:
            self.record()
            self.checkpoint = self.time

    def run(self):
        for i in range(0, self.nCycles):
            for setpoint, rate, hold_time in zip(self.listSP, self.listRate, self.listHold):
                self.tbc_controller.ramp_to(setpoint, rate)
                time_limit = 2 * abs(setpoint - self.pcr_machine.sample_temp) / (rate / 100 * self.tbc_controller.max_down_ramp)
                ctime = 0
                while abs(self.pcr_machine.sample_temp - setpoint) > 1:                    
                    self.tbc_controller.tick(self.dt)
                    self.pcr_machine.tick(self.dt)
                    self.tick(self.dt)
                    ctime += self.dt
                    if ctime >= time_limit:
                        print("ERROR: Ramp time exceeds the time limit.")
                        self.protocolData.to_csv("protocol.csv", index=False)
                        return
                ctime = 0
                while ctime < hold_time:                    
                    self.tbc_controller.tick(self.dt)
                    self.pcr_machine.tick(self.dt)                    
                    self.tick(self.dt)
                    ctime += self.dt
        self.protocolData.to_csv("protocol.csv", index=False)

if __name__ == "__main__":
    protocol = Protocol(listSP   =[ 95,  60], 
                        listRate =[ 50,  50], 
                        listHold =[100, 100], 
                        nCycles  =2, 
                        Tblock   =60, 
                        Tamb     =25
                        )
    protocol.run()

