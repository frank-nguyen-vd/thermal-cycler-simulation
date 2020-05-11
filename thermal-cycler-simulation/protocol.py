from pcr_machine import PCR_Machine
from tbc_controller import TBC_Controller
from peltier import Peltier
import pandas as pd

class Protocol:
    def __init__(self, 
                listSP=[ 95,  60], 
                listRate=[100, 100], 
                listHold=[35, 35], 
                nCycles=6, 
                Tblock=25, 
                Tamb=25, 
                pcr_path="best_pcr_model.ml",
                peltier_path="best_peltier_model.ml",
                record_filepath="protocol.csv"):
        self.time = 0
        self.checkpoint = 0
        self.record_period = 0.2
        self.control_period = 0.05
        self.dt = 0.05
        self.listSP = listSP
        self.listRate = listRate
        self.listHold = listHold
        self.nCycles = nCycles
        self.record_filepath = record_filepath
        self.pcr_machine = PCR_Machine( path_to_model=pcr_path,
                                        sample_volume=10,
                                        sample_temp=Tblock,
                                        block_temp=Tblock,
                                        heat_sink_temp=Tamb,
                                        block_rate=0,
                                        sample_rate=0,                                        
                                        amb_temp=Tamb,
                                        update_period=self.control_period,
                                        start_time=0
                                        
        )
        self.peltier = Peltier(path_to_model=peltier_path)
        self.tbc_controller = TBC_Controller(PCR_Machine=self.pcr_machine,
                                            Peltier=self.peltier,
                                            start_time=0,
                                            update_period=self.control_period,
                                            volume=10
        )
        self.protocolData = pd.DataFrame(columns=[
                "Epoch Time",
                "Sample Temp",
                "Block Temp",
                "Heat Sink Temp",
                "QPID",
                "Iset",
                "Imeasure",
                "Vset",
                "Control Stage",
                "PID SP",
                "PID PV",
                "PID m",
                "PID b",
                "PID y",
                "PID ffwd",
                "PID2 SP",
                "PID2 PV"
        ])        

    def record(self):
        data = {
            "Epoch Time"    :   self.time,
            "Sample Temp"   :   self.pcr_machine.sample_temp,
            "Block Temp"    :   self.pcr_machine.block_temp,
            "Heat Sink Temp":   self.pcr_machine.heat_sink_temp,
            "QPID"          :   self.tbc_controller.qpid,
            "Iset"          :   self.pcr_machine.Iset,
            "Imeasure"      :   self.pcr_machine.Imeasure,
            "Vset"          :   self.pcr_machine.Vset,
            "Control Stage" :   self.tbc_controller.stage,
            "PID SP"        :   self.tbc_controller.pid.SP,
            "PID PV"        :   self.tbc_controller.pid.PV,
            "PID m"         :   self.tbc_controller.pid.m,
            "PID b"         :   self.tbc_controller.pid.b,
            "PID y"         :   self.tbc_controller.pid.y,
            "PID ffwd"      :   self.tbc_controller.pid.ffwd,
            "PID2 SP"       :   self.tbc_controller.pid2.SP,
            "PID2 PV"       :   self.tbc_controller.pid2.PV
        }
        self.protocolData = self.protocolData.append(data, ignore_index=True)

    def tick(self, dt):
        self.time += dt
        if round(self.time - self.checkpoint, 3) >= self.record_period:
            self.record()
            self.checkpoint = self.time

    def run(self, record_mode='w'):
        for i in range(0, self.nCycles):
            for setpoint, rate, hold_time in zip(self.listSP, self.listRate, self.listHold):
                self.tbc_controller.ramp_to(setpoint, rate)
                time_limit = 2 * abs(setpoint - self.pcr_machine.sample_temp) / (rate / 100 * self.tbc_controller.max_down_ramp)
                ctime = 0
                print(f"Ramping to {setpoint}")
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
                print(f"Holding at {setpoint}")
                while ctime < hold_time:                    
                    self.tbc_controller.tick(self.dt)
                    self.pcr_machine.tick(self.dt)                    
                    self.tick(self.dt)
                    ctime += self.dt
        print("Saving protocol data")
        self.protocolData.to_csv(self.record_filepath, index=False, mode=record_mode)

if __name__ == "__main__":
    protocol = Protocol(listSP   =[ 95,  60], 
                        listRate =[100, 100], 
                        listHold =[ 10,  10], 
                        nCycles  =1, 
                        Tblock   =60, 
                        Tamb     =25
                        )
    protocol.run()

