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
        self.target_sample_rate = 0 
        self.sample_approaching = False
        self.stage = "Hold"     
        self.Iset = 0
        self.Imeasure = 0
        self.calcHeatBlkOS = 0
        self.calcHeatBlkWin = 0
        self.calcHeatSmpWin = 0
        self.calcCoolBlkOS = 0
        self.calcCoolBlkWin = 0
        self.calcCoolSmpWin = 0
        self.unachievable = 10
        self.block_slow_rate = 0.5
        self.sample_slow_rate = 0.2
        self.max_up_ramp = 0
        self.max_down_ramp = 0
        self.rampup_minP = 3
        self.rampdown_minP = 3
        self.max_qpid = 150
        self.qpid = 0
        self.target_block_rate = 0
        self.target_sample_rate = 0
        self.heat_brake_const = 0
        self.heat_brake = 0
        self.cool_brake_const = 0
        self.cool_brake = 0
        self.max_block_temp = 109
        self.qHeatLoss = 0
        self.qMaxRampPid = 150
        self.qMaxHoldPid = 40
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

    def prepare_overshoot_over(self):
        self.pid.reset()
        self.pid.load(self.pid_const, "Overshoot Over")

        self.pid2.reset()
        self.pid2.load(self.pid_const, "Hold Over")        
        if self.pcr.block_temp >= self.max_block_temp or self.set_point + self.calcHeatBlkOS >= self.max_block_temp:
            self.pid2.SP = self.max_block_temp * 0.5
        else:
            self.pid2.SP = (self.set_point + self.calcHeatBlkOS) * 0.5
        self.pid2.ffwd = self.qHeatLoss / self.qMaxRampPid * 100
        self.pid2.y = self.pcr.block_temp * 0.5

        self.stage = "Overshoot Over"
        self.spCtrlFirstActFlag = False
        self.rampUpStageRampTime = self.time_elapsed

    def prepare_hold(self):
        pass

    def ctrl_ramp_up(self):
        if self.pcr.block_temp < self.set_point \
            and self.pcr.block_temp + self.calcHeatBlkWin <= self.set_point + self.calcHeatBlkOS:

            if self.time_elapsed >= self.ramp_time:
                self.pid.SP = self.unachievable
            else:
                self.pid.SP = (self.set_point - self.pcr.sample_temp) / (self.ramp_time - self.time_elapsed)

            if self.pid.SP > 1.05 * self.target_sample_rate:
                self.pid.SP = 1.05 * self.target_sample_rate

            if self.target_block_rate <= self.block_slow_rate:
                if self.target_sample_rate / self.max_up_ramp < 0.1:
                    stash = self.pid.P
                    factor = self.target_sample_rate / self.max_up_ramp * 10
                    self.pid.P *= factor
                    if self.pid.P < self.rampup_minP:
                        self.pid.P = self.rampup_minP          
                    self.qpid = self.max_qpid * self.pid.update() * 0.01
                    self.pid.P = stash
                else:
                    self.qpid = self.max_qpid * self.pid.update() * 0.01

            else:
                self.qpid = self.max_qpid * self.pid.update() * 0.01

        else: # block temp. has overshot the set point
            if self.pcr.sample_rate <= self.sample_slow_rate:
                self.prepare_hold()
            else:
                self.smpWinInRampUpFlag = False
                overshoot_gap = self.set_point + self.calcHeatBlkOS - self.pcr.block_temp
                if self.pcr.block_rate > self.pcr.sample_rate:
                    time_to_maxOS = overshoot_gap / self.pcr.block_rate
                    self.rampUpStageRate = self.pcr.block_rate
                else:
                    time_to_maxOS = overshoot_gap / self.pcr.sample_rate
                    self.rampUpStageRate = self.pcr.sample_rate
                if self.calcHeatBlkOS > self.calcHeatBlkWin:
                    self.heat_brake = self.heat_brake_const * self.calcHeatBlkOS / time_to_maxOS
                else:
                    self.heat_brake = self.heat_brake_const * self.calcHeatBlkWin / time_to_maxOS

                self.heat_brake = self.heat_brake_const * self.calcHeatBlkOS / time_to_maxOS
                self.prepare_overshoot_over()

        if self.pcr.sample_temp >= self.set_point - self.calcHeatSmpWin:
            if self.pcr.sample_rate <= 0:
                return

            self.smpWinInRampUpFlag = True
            time_to_setpoint = (self.set_point - self.pcr.sample_temp) / self.pcr.sample_rate
            self.heat_brake = self.heat_brake_const * self.calcHeatSmpWin / time_to_setpoint
            self.rampUpStageRate = self.pcr.sample_rate
            self.prepare_overshoot_over()

        self.peltier.mode = "heat"


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
            self.ramp_time = self.ramp_dist / self.target_sample_rate

    def calc_feed_forward(self):
        return 0

    def ramp_to(self, new_set_point, sample_rate):
        if self.set_point == new_set_point:
            return
        self.stage = "Ramp Up" if self.set_point < new_set_point else "Ramp Down"        
        self.start_time = self.time
        self.ramp_dist = new_set_point - self.pcr.sample_temp
        self.set_point = new_set_point        
        self.target_sample_rate = sample_rate if self.stage == "Ramp Up" else -sample_rate
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