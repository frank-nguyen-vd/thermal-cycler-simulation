from PID_Controller import PID_Controller

class TBC_Controller:
    def __init__(self, PCR_Machine, start_time=0, update_freq=20):
        self._pcr_machine = PCR_Machine
        self._time = start_time
        self._checkpoint = start_time        
        self._period = 1 / update_freq # update_freq in Hz, period in second
        self._pid = PID_Controller()        

    def is_timer_fired(self):
        if (self._time - self._checkpoint) >= self._period:
            self._checkpoint = self._time
            return True
        return False

    def update(self, tick):
        self._time += tick
        if self.is_timer_fired():
            pass