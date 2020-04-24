from PID_Controller import PID_Controller

class TBC_Controller:
    def __init__(self, PCR_Machine, start_time=0, update_freq=20):
        self._pcr_machine = PCR_Machine
        self._time = start_time
        self._checkpoint = start_time        
        self._period = 1 / update_freq # update_freq in Hz, period in second
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


    def is_timer_fired(self):
        if (self._time - self._checkpoint) >= self._period:
            self._checkpoint = self._time
            return True
        return False

    def ramp_to(self, set_point, ramp_rate):
        pass

    def update(self, tick):
        self._time += tick
        if self.is_timer_fired():
            pass