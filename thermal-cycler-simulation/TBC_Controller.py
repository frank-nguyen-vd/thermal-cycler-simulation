from pid_controller import PID_Controller
from pcr_machine import PCR_Machine

class TBC_Controller:
    def __init__(self, PCR_Machine, start_time=0, update_freq=20, set_point=25):
        self._pcr = PCR_Machine
        self._time = start_time
        self._checkpoint = start_time        
        self._period = 1 / update_freq # update_freq in Hz, period in second
        self._set_point = set_point
        self._ramp_time = 0
        self._ramp_dist = 0
        self._sample_rate = 0 # sample ramp rate
        self._block_rate = 0 # block ramp rate        
        self._sample_approaching = False
        self._stage = "Hold"     
        self.init_pid()
    def init_pid(self):
        self._pid = PID_Controller()
        self._pid_const = {}
        self._pid_const["Ramp Up"        ] = {"P": 3, "I": 0, "D": 0, "KI": 0, "KD": 0}
        self._pid_const["Overshoot Over" ] = {"P": 3, "I": 0, "D": 0, "KI": 0, "KD": 0}
        self._pid_const["Hold Over"      ] = {"P": 3, "I": 0, "D": 0, "KI": 0, "KD": 0}
        self._pid_const["Land Over"      ] = {"P": 3, "I": 0, "D": 0, "KI": 0, "KD": 0}
        self._pid_const["Ramp Down"      ] = {"P": 3, "I": 0, "D": 0, "KI": 0, "KD": 0}
        self._pid_const["Overshoot Under"] = {"P": 3, "I": 0, "D": 0, "KI": 0, "KD": 0}
        self._pid_const["Hold Under"     ] = {"P": 3, "I": 0, "D": 0, "KI": 0, "KD": 0}
        self._pid_const["Land Under"     ] = {"P": 3, "I": 0, "D": 0, "KI": 0, "KD": 0}
        self._pid_const["Hold"           ] = {"P": 3, "I": 0, "D": 0, "KI": 0, "KD": 0}

    def update_pid_PV(self):
        if self._stage == "Ramp Up" or self._stage == "Ramp Down":
            self._pid._PV = self._pcr.sample_rate
        elif self._stage == "Overshoot Over" or self._stage == "Overshoot Under":
            self._pid._PV = self._pcr.sample_rate if self._sample_approaching else self._pcr.block_rate
            self._pid2._PV = self._pcr.block_temp * 0.5
        elif self._stage == "Land Over" or self._stage == "Land Under":
            self._pid._PV = self._pcr.block_rate
        else:
            self._pid._PV = self._pcr.block_temp * 0.5

    def is_timer_fired(self):
        if (self._time - self._checkpoint) >= self._period:
            self._checkpoint = self._time
            return True
        return False

    def ramp_to(self, set_point, ramp_rate):
    def ramp_to(self, new_set_point, sample_rate):
        if self._set_point == new_set_point:
            return
        self._stage = "Ramp Up" if self._set_point < new_set_point else "Ramp Down"        
        self._ramp_time = 0
        self._ramp_dist = new_set_point - self._pcr.block_temp
        self._set_point = new_set_point        
        self._sample_rate = sample_rate if self._stage == "Ramp Up" else -sample_rate
        self._block_rate = self.calc_block_rate()

        self._pid.reset()
        self._pid._SP = sample_rate
        self._pid._ffwd = self.calc_feed_forward()
        self._pid._P = self._pid_const[self._stage]["P"]
        self._pid._I = self._pid_const[self._stage]["I"]
        self._pid._D = self._pid_const[self._stage]["D"]
        self._pid._KI = self._pid_const[self._stage]["KI"]
        self._pid._KD = self._pid_const[self._stage]["KD"]
        pass
 
    def update(self):
        self.update_pid_PV()
        self.run_control_stage()
        self.calc_Iset()
        self.calc_Imeasure()
        self.output()
    
    def tick(self, tick):
        self._time += tick
        if self.is_timer_fired():
            self.update()