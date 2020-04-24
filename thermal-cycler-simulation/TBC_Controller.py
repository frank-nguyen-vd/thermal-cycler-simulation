from PID_Controller import PID_Controller

class TBC_Controller:
    def __init__(self, PCR_Machine, start_time=0, update_freq=20):
        self._pcr_machine = PCR_Machine
        self._time = start_time
        self._checkpoint = start_time        
        self._period = 1 / update_freq # update_freq in Hz, period in second
        self._pid = PID_Controller()
        pass

