from pid_controller import PID_Controller
from pcr_machine import PCR_Machine
from peltier import Peltier

class TBC_Controller:
    def __init__(self, PCR_Machine, start_time=0, update_freq=20, set_point=25):
        self.pcr = PCR_Machine
        self.time = start_time
        self.checkpoint = start_time        
        self.period = 1 / update_freq # update_freq in Hz, period in second
        self.set_point = set_point
        self.ramp_time = 0
        self.ramp_dist = 0
        self.assigned_sample_rate = 0 # sample ramp rate
        self.assigned_block_rate = 0 # block ramp rate        
        self.sample_approaching = False
        self.stage = "Hold"     
        self.Iset = 0
        self.Imeasure = 0
        self.init_pid()
        self.init_peltier()
    
    def init_peltier(self):
        self.peltier = Peltier()
        self.peltier.mode = "heat"
    
    def init_pid(self):
        self.pid = PID_Controller()
        self.pid2 = PID_Controller()

        self.pid_const = {}
        self.pid_const["Ramp Up"        ] = {"P": 3, "I": 0, "D": 0, "KI": 0, "KD": 0}
        self.pid_const["Overshoot Over" ] = {"P": 3, "I": 0, "D": 0, "KI": 0, "KD": 0}
        self.pid_const["Hold Over"      ] = {"P": 3, "I": 0, "D": 0, "KI": 0, "KD": 0}
        self.pid_const["Land Over"      ] = {"P": 3, "I": 0, "D": 0, "KI": 0, "KD": 0}
        self.pid_const["Ramp Down"      ] = {"P": 3, "I": 0, "D": 0, "KI": 0, "KD": 0}
        self.pid_const["Overshoot Under"] = {"P": 3, "I": 0, "D": 0, "KI": 0, "KD": 0}
        self.pid_const["Hold Under"     ] = {"P": 3, "I": 0, "D": 0, "KI": 0, "KD": 0}
        self.pid_const["Land Under"     ] = {"P": 3, "I": 0, "D": 0, "KI": 0, "KD": 0}
        self.pid_const["Hold"           ] = {"P": 3, "I": 0, "D": 0, "KI": 0, "KD": 0}

    def update_feedback(self):
        # update pid process variable (PV)
        if self.stage == "Ramp Up" or self.stage == "Ramp Down":
            self.pid.PV = self.pcr.sample_rate
        elif self.stage == "Overshoot Over" or self.stage == "Overshoot Under":
            self.pid.PV = self.pcr.sample_rate if self.sample_approaching else self.pcr.block_rate
            self.pid2.PV = self.pcr.block_temp * 0.5
        elif self.stage == "Land Over" or self.stage == "Land Under":
            self.pid.PV = self.pcr.block_rate
        else:
            self.pid.PV = self.pcr.block_temp * 0.5

        self.time_elapsed = self.time - self.start_time
        self.ramp_dist = self.set_point - self.pcr.block_temp

    def ctrl_ramp_up(self):
        if self.pcr.block_temp < self.set_point
            and self.pcr.block_temp + self.calcHeatBlkWin <= self.set_point + self.calcHeatBlkOS:

            if (self.time_elapsed >= self.ramp_time)
                self.pid.SP = self.max_rate
            else:
                self.pid.SP = (self.set_point - self.pcr.sample_temp) / (self.ramp_time - self.time_elapsed)


    def run_control_stage(self):
        if self.stage == "Ramp Up":
            self.ctrl_ramp_up()

        elif self.stage == "Overshoot Over":
            self.ctrl_overshoot_over()

        elif self.stage == "Hold Over":
            self.ctrl_hold_over()

        elif self.stage == "Land Over":
            self.ctrl_land_over()

        elif self.stage == "Ramp Down":
            self.ctrl_ramp_down()

        elif self.stage == "Overshoot Under":
            self.ctrl_overshoot_under()

        elif self.stage == "Overshoot Under":
            self.ctrl_overshoot_under()

        elif self.stage == "Hold Under":
            self.ctrl_hold_under()

        elif self.stage == "Land Under":
            self.ctrl_land_under()

        elif self.stage == "Hold":
            self.ctrl_hold()


    def is_timer_fired(self):
        if (self.time - self.checkpoint) >= self.period:
            self.checkpoint = self.time
            return True
        return False

    def estimate_block_rate(self):
        if self.ramp_dist > 0:
            self.ramp_time = self.ramp_dist / self.assigned_sample_rate

    def calc_feed_forward(self):
        return 0

    def ramp_to(self, new_set_point, sample_rate):
        if self.set_point == new_set_point:
            return
        self.stage = "Ramp Up" if self.set_point < new_set_point else "Ramp Down"        
        self.start_time = self.time
        self.ramp_dist = new_set_point - self.pcr.sample_temp
        self.set_point = new_set_point        
        self.assigned_sample_rate = sample_rate if self.stage == "Ramp Up" else -sample_rate
        self.estimate_block_rate()

        self.pid.reset()
        self.pid.SP = sample_rate
        self.pid.ffwd = self.calc_feed_forward()
        self.pid.P = self.pid_const[self.stage]["P"]
        self.pid.I = self.pid_const[self.stage]["I"]
        self.pid.D = self.pid_const[self.stage]["D"]
        self.pid.KI = self.pid_const[self.stage]["KI"]
        self.pid.KD = self.pid_const[self.stage]["KD"]

    def calc_Iset(self):
        self.Iset = self.peltier.calc_Iset(self.pid.m)

    def calc_Imeasure(self):
        self.Imeasure = self.peltier.calc_Imeasure(self, 
                                                     self.pcr.heat_sink_temp,
                                                     self.pcr.block_temp, 
                                                     self.Iset
                                                     )

    def output(self):
        pass
 
    def update(self):
        self.update_feedback()
        self.run_control_stage()
        self.calc_Iset()
        self.calc_Imeasure()
        self.output()
    
    def tick(self, tick):
        self.time += tick
        if self.is_timer_fired():
            self.update()