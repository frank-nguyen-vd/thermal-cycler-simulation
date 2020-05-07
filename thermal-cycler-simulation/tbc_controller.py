from pid_controller import PID_Controller
from pcr_machine import PCR_Machine
from peltier import Peltier
from math import exp

class TBC_Controller:
    def __init__(self, PCR_Machine, start_time=0, update_period=0.05, volume=10):
        self.pcr = PCR_Machine
        self.time = self.checkpoint = start_time              
        self.period = update_period
        self.volume = volume
        self.set_point = self.pcr.sample_temp
        self.max_block_temp = 109
        self.max_ramp_dist = 35
        self.unachievable = 10
        self.smpWinInRampUpFlag = False
        self.smpWinInRampDownFlag = False
        self.init_pid()
        self.init_peltier()        
        self.load_tuning_params()
        self.max_up_ramp = self.calc_poly_eqn(self.upRrEqn, self.volume)
        self.max_down_ramp = self.calc_poly_eqn(self.downRrEqn, self.volume)
    
    def calc_poly_eqn(self, eqn, vol):
        return sum([vol**deg * coeff for deg, coeff in enumerate(eqn)])
    
    def init_peltier(self):
        self.peltier = Peltier()
        self.peltier.mode = "heat"
    
    def init_pid(self):
        self.pid = PID_Controller()
        self.pid.dt = self.period / 60 # dt is in minute
        self.pid2 = PID_Controller()
        self.pid2.dt = self.period / 60 # dt is in minute

    def load_tuning_params(self):
        self.blockMCP = 10.962
        self.upRrEqn = [
            4.8440929020,
           -0.0325607505,
           -0.0001714895,
            0.0000018869
        ]
        self.downRrEqn = [
            3.7445968870,
           -0.0309892434,
            0.0001028925,
           -0.0000001561
        ]
        self.pid_const = {}
        self.pid_const["Ramp Up"        ] = {
            "P"  : 3, 
            "I"  : 0.06, 
            "D"  : 0.0001, 
            "KI" : 10, 
            "KD" : 5
        }
        self.pid_const["Overshoot Over" ] = {
            "P"  : 7, 
            "I"  : 0.05, 
            "D"  : 0.0, 
            "KI" : 2, 
            "KD" : 5
        }
        self.pid_const["Hold Over"      ] = {
            "P"  : 1, 
            "I"  : 0.04, 
            "D"  : 0.01, 
            "KI" : 5, 
            "KD" : 10
        }
        self.pid_const["Land Over"      ] = {
            "P"  : 10, 
            "I"  : 0.03, 
            "D"  : 0.00, 
            "KI" : 2, 
            "KD" : 5
        }
        self.pid_const["Hold"           ] = {
            "P"  : 0.9, 
            "I"  : 0.04, 
            "D"  : 0.01, 
            "KI" : 5, 
            "KD" : 10
        }
        self.pid_const["Ramp Down"      ] = {
            "P"  : 3, 
            "I"  : 0.06, 
            "D"  : 0.0001, 
            "KI" : 10, 
            "KD" : 5
        }
        self.pid_const["Overshoot Under"] = {
            "P"  : 7, 
            "I"  : 0.05, 
            "D"  : 0.00, 
            "KI" : 2, 
            "KD" : 5
        }
        self.pid_const["Hold Under"     ] = {
            "P"  : 1, 
            "I"  : 0.04, 
            "D"  : 0.01, 
            "KI" : 5, 
            "KD" : 10
        }
        self.pid_const["Land Under"     ] = {
            "P"  : 10, 
            "I"  : 0.03, 
            "D"  : 0.00, 
            "KI" : 2, 
            "KD" : 5
        }
        self.slow_upramp_qpid = -15
        self.block_slow_rate = 0.5
        self.sample_slow_rate = 0.0226
        self.rampup_minP = 3
        self.rampdown_minP = 3
        self.smoothRegionOverRR = 1.6
        self.smoothRegionUnderRR = 1.5
        self.smoothRegionOverWin = 1.5
        self.smoothRegionUnderWin = 1.75

        if self.volume <= 5:
            pass
        elif self.volume <= 10:
            self.maxHeatBlkOS       = 2.8
            self.maxCoolBlkOS       = 3.4
            self.maxHeatSmpWin      = 2
            self.maxCoolSmpWin      = 2
            self.qMaxHoldPid        = 40
            self.qMaxRampPid        = 150
            self.maxHeatIset        = 6.5
            self.maxCoolIset        = 6.5
            self.maxHeatBlkWin      = 4
            self.maxCoolBlkWin      = 3
            self.qHeatLoss          = 10
            self.heat_brake_const   = 1.2
            self.heatSpCtrlActivRR  = 0.2
            self.heatSpCtrlActivSP  = 0.1
            self.cool_brake_const   = 1.5
            self.coolSpCtrlActivRR  = 0.3
            self.coolSpCtrlActivSP  =-0.1
        elif self.volume <= 30:
            pass
        elif self.volume <= 50:
            pass
        else:
            pass


    def update_feedback(self):
        # update pid process variable (PV)
        if self.stage == "Ramp Up" or self.stage == "Ramp Down":
            self.pid.PV = self.pcr.sample_rate
        elif self.stage == "Overshoot Over" or self.stage == "Overshoot Under":
            if self.smpWinInRampDownFlag or self.smpWinInRampUpFlag:
                self.pid.PV = self.pcr.sample_rate
            else:
                self.pid.PV = self.pcr.block_rate
            self.pid2.PV = self.pcr.block_temp * 0.5
        elif self.stage == "Land Over" or self.stage == "Land Under":
            self.pid.PV = self.pcr.block_rate
        else:
            self.pid.PV = self.pcr.block_temp * 0.5
        self.time_elapsed = self.time - self.start_time        

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
        self.stage = "Hold"
        self.pid.reset()
        self.pid.load(self.pid_const, "Hold")
        self.pid.SP = self.set_point * 0.5
        self.pid.y = self.pcr.block_temp * 0.5
        self.pid.ffwd = self.qHeatLoss / self.qMaxHoldPid * 100

    def calcBlockRate(self, timeConst):
        # assume ramp_time and ramp_dist are calculated before calling this function
        if self.ramp_time == 0 or timeConst == 0:
            return self.target_sample_rate
        return self.ramp_dist / (self.ramp_time - timeConst * (1 - exp(-self.ramp_time / timeConst)))

    def prepare_ramp_up(self):
        self.stage = "Ramp Up"    
        self.target_block_rate = self.calcBlockRate(self.pcr.heat_const)

        self.pid.load(self.pid_const, "Ramp Up")
        self.pid.SP = self.target_sample_rate
        initial_qpid = self.blockMCP * self.target_block_rate
        self.pid.ffwd = initial_qpid / self.qMaxRampPid * 100

        if self.target_block_rate < self.block_slow_rate:
            self.pid.ffwd = self.slow_upramp_qpid / self.qMaxRampPid * 100
        
        if self.pid.ffwd > 100:
            self.pid.ffwd = 100

        overshoot_dt_const = (self.ramp_dist - 2) / (self.max_ramp_dist - 2)
        overshoot_rr_const = 1 if self.target_sample_rate >= self.max_up_ramp else self.target_sample_rate / self.max_up_ramp

        if overshoot_dt_const > 1:
            blkOS_const = overshoot_rr_const
            smpWin_const = overshoot_rr_const
        else:
            blkOS_const = overshoot_dt_const * overshoot_rr_const
            smpWin_const = overshoot_dt_const * overshoot_rr_const

        self.calcHeatBlkOS  = blkOS_const * self.maxHeatBlkOS
        self.calcHeatSmpWin = smpWin_const * self.maxHeatSmpWin
        self.calcHeatBlkWin = overshoot_rr_const * self.maxHeatBlkWin
        self.smpWinInRampUpFlag = False

    def prepare_ramp_down(self):
        self.stage = "Ramp Down"        
        self.target_block_rate = self.calcBlockRate(self.pcr.cool_const) # target_block_rate is negative        

        self.pid.load(self.pid_const, "Ramp Down")
        self.pid.SP = self.target_sample_rate

        if abs(self.target_block_rate) < self.block_slow_rate:
            initial_qpid = self.blockMCP * self.block_slow_rate
        else:
            initial_qpid = self.blockMCP * self.target_block_rate

        self.pid.ffwd = -initial_qpid / self.qMaxRampPid * 100        
        
        if self.pid.ffwd < -100:
            self.pid.ffwd = -100

        overshoot_dt_const = (self.ramp_dist - 2)/ (self.max_ramp_dist - 2)
        if abs(self.target_sample_rate) <= self.max_down_ramp:
            overshoot_rr_const = 1
        else:
            overshoot_rr_const = self.target_sample_rate / self.max_down_ramp

        if overshoot_dt_const > 1:
            blkOS_const = overshoot_rr_const            
        else:
            blkOS_const = overshoot_dt_const * overshoot_rr_const
        smpWin_const = overshoot_dt_const * overshoot_rr_const            

        self.calcCoolBlkOS  = blkOS_const * self.maxCoolBlkOS
        self.calcCoolSmpWin = smpWin_const * self.maxCoolSmpWin
        self.calcCoolBlkWin = overshoot_rr_const * self.maxCoolBlkWin        

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
                    self.qpid = self.qMaxRampPid * self.pid.update() * 0.01
                    self.pid.P = stash
                else:
                    self.qpid = self.qMaxRampPid * self.pid.update() * 0.01

            else:
                self.qpid = self.qMaxRampPid * self.pid.update() * 0.01

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

                self.prepare_overshoot_over()

        if self.pcr.sample_temp >= self.set_point - self.calcHeatSmpWin:
            if self.pid.PV <= 0:
                return

            self.smpWinInRampUpFlag = True
            time_to_setpoint = (self.set_point - self.pcr.sample_temp) / self.pid.PV
            self.heat_brake = self.heat_brake_const * self.calcHeatSmpWin / time_to_setpoint
            self.rampUpStageRate = self.pid.PV
            self.prepare_overshoot_over()

        self.peltier.mode = "heat"

    def prepare_hold_over(self):
        if self.pcr.block_temp >= self.max_block_temp:
            self.pid.SP = self.max_block_temp * 0.5
        else:
            self.pid.SP = (self.set_point + self.calcHeatBlkOS) * 0.5

        if self.pid.SP > self.max_block_temp * 0.5:
            self.pid.SP = self.max_block_temp * 0.5

        self.pid.m = self.pid2.m
        self.pid.b = self.pid2.b
        self.pid.y = self.pid2.y
        self.pid.ffwd = self.qHeatLoss / self.qMaxHoldPid * 100
        self.pid.load(self.pid_const, "Hold Over")
        self.stage = "Hold Over"


    def ctrl_overshoot_over(self):
        if not self.smpWinInRampUpFlag:
            if self.pcr.sample_temp >= self.set_point - self.calcHeatSmpWin:
                self.prepare_hold()
                return

            if self.calcHeatBlkOS >= self.calcHeatBlkWin:
                tempSP = self.rampUpStageRate * exp(-self.heat_brake * (self.time_elapsed - self.rampUpStageRampTime) / self.calcHeatBlkOS)
            else:
                tempSP = self.rampUpStageRate * exp(-self.heat_brake * (self.time_elapsed - self.rampUpStageRampTime) / self.calcHeatBlkWin)
        else:
            if self.calcHeatSmpWin != 0:
                tempSP = self.rampUpStageRate * exp(-self.heat_brake * (self.time_elapsed - self.rampUpStageRampTime) / self.calcHeatSmpWin)
            else:
                tempSP = 0
            
            if self.pcr.sample_temp >= self.set_point - 0.2 or self.pcr.block_temp > self.set_point:
                tempSP = self.pid.b
                temp_b = self.pid2.b
                temp_ffwd = self.pid2.ffwd
                temp_y = self.pid2.y
                self.prepare_hold()
                self.pid.b  = temp_b + tempSP
                self.pid.m  = self.pid.b
                self.pid.b -= temp_ffwd
                self.pid.y  = temp_y
            return
        
        self.pid.SP = tempSP
        qPower = tempSP / self.rampUpStageRate * self.qMaxRampPid + (1 - tempSP / self.rampUpStageRate) * self.qMaxHoldPid
        self.pid.ffwd = self.pid.SP * self.blockMCP / qPower * 100
        self.qpid = qPower * self.pid.update() / 100

        if self.pid.SP <= self.heatSpCtrlActivRR * self.rampUpStageRate \
            or self.pid.SP <= self.heatSpCtrlActivSP:
            if not self.spCtrlFirstActFlag:
                self.pid2.y = self.pcr.block_temp * 0.5
                self.spCtrlFirstActFlag = True
            self.qpid += qPower * self.pid2.update() / 100

        if self.pcr.block_temp >= self.set_point + self.calcHeatBlkOS \
            or self.pcr.block_temp >= self.max_block_temp:

            self.prepare_hold_over()
        
        self.peltier.mode = "heat"

    def prepare_land_over(self):
        self.pid.reset()
        self.pid.load(self.pid_const, "Land Over")
        self.stage = "Land Over"

    def ctrl_hold_over(self):
        self.qpid = self.qMaxHoldPid * self.pid.update() / 100
        if self.pcr.sample_temp >= self.set_point - self.calcHeatSmpWin:
            self.prepare_land_over()
        self.peltier.mode = "heat"

    def ctrl_land_over(self):
        timeToSetPt = (self.set_point - self.pcr.sample_temp) / self.pcr.sample_rate
        if timeToSetPt > 0:
            self.pid.SP = (self.set_point - self.pcr.block_temp) / timeToSetPt
        else:
            self.pid.SP = -3
        if self.pcr.block_temp - self.smoothRegionOverWin <= self.set_point:
            if self.pid.SP < -self.smoothRegionOverRR:
                self.pid.SP = -self.smoothRegionOverRR
        self.pid.ffwd = self.pid.SP * self.blockMCP / self.qMaxRampPid * 100
        self.qpid = self.qMaxRampPid * self.pid.update() / 100
        if self.pcr.block_temp - 0.25 <= self.set_point:
            self.prepare_hold()
        self.peltier.mode = "cool"

    def ctrl_ramp_down(self):
        if self.pcr.block_temp > self.set_point \
            and self.pcr.block_temp - self.calcCoolBlkWin >= self.set_point - self.calcCoolBlkOS:

            if self.time_elapsed >= self.ramp_time:
                self.pid.SP = -self.unachievable
            else:
                self.pid.SP = (self.set_point - self.pcr.sample_temp) / (self.ramp_time - self.time_elapsed)

            if self.pid.SP < -1.05 * self.target_sample_rate:
                self.pid.SP = -1.05 * self.target_sample_rate

            if self.target_block_rate <= self.block_slow_rate:
                if self.target_sample_rate / self.max_down_ramp < 0.1:
                    stash = self.pid.P
                    factor = self.target_sample_rate / self.max_down_ramp * 10
                    self.pid.P *= factor
                    if self.pid.P < self.rampdown_minP:
                        self.pid.P = self.rampdown_minP          
                    self.qpid = self.qMaxRampPid * self.pid.update() * 0.01
                    self.pid.P = stash
                else:
                    self.qpid = self.qMaxRampPid * self.pid.update() * 0.01

            else:
                self.qpid = self.qMaxRampPid * self.pid.update() * 0.01

        else: # block temp. has overshot the set point
            if self.pcr.sample_rate >= -self.sample_slow_rate:
                self.prepare_hold()
            else:
                self.smpWinInRampDownFlag = False
                overshoot_gap = self.set_point - self.calcHeatBlkOS - self.pcr.block_temp
                if self.pcr.block_rate < self.pcr.sample_rate:
                    time_to_maxOS = overshoot_gap / self.pcr.block_rate
                    self.rampDownStageRate = abs(self.pcr.block_rate)
                else:
                    time_to_maxOS = overshoot_gap / self.pcr.sample_rate
                    self.rampDownStageRate = abs(self.pcr.sample_rate)

                if self.calcCoolBlkOS > self.calcCoolBlkWin:
                    self.cool_brake = self.cool_brake_const * self.calcCoolBlkOS / time_to_maxOS
                else:
                    self.cool_brake = self.cool_brake_const * self.calcCoolBlkWin / time_to_maxOS
                
                self.prepare_overshoot_under()

        if self.pcr.sample_temp <= self.set_point + self.calcCoolSmpWin:
            if self.pid.PV >= 0:
                return

            self.smpWinInRampDownFlag = True
            time_to_setpoint = (self.set_point - self.pcr.sample_temp) / self.pid.PV
            self.cool_brake = self.cool_brake_const * self.calcCoolSmpWin / time_to_setpoint
            self.rampDownStageRate = self.pid.PV
            self.prepare_overshoot_under()

        self.peltier.mode = "cool"

    def prepare_overshoot_under(self):
        self.rampDownStageRampTime = self.time_elapsed
        self.pid.load(self.pid_const, "Overshoot Under")
        self.pid2.reset()
        self.pid2.load(self.pid_const, "Hold Under")
        self.pid2.SP = (self.set_point - self.calcCoolBlkOS) * 0.5
        self.pid2.ffwd = -self.qHeatLoss / self.qMaxHoldPid * 100
        self.pid2.y = self.pcr.block_temp * 0.5
        self.spCtrlFirstActFlag = False
        self.stage = "Overshoot Under"

    def prepare_land_under(self):
        self.pid.reset()
        self.pid.load(self.pid_const, "Land Under")
        self.stage = "Land Under"

    def ctrl_overshoot_under(self):
        if self.smpWinInRampDownFlag == False:
            if self.calcCoolBlkOS >= self.calcCoolBlkWin:
                tempSP = self.rampDownStageRate * exp(-self.cool_brake / self.calcCoolBlkOS * (self.time_elapsed - self.rampDownStageRampTime))
            else:
                tempSP = self.rampDownStageRate * exp(-self.cool_brake / self.calcCoolBlkWin * (self.time_elapsed - self.rampDownStageRampTime))

            if self.pcr.sample_temp <= self.set_point + self.calcCoolSmpWin:
                self.prepare_land_under()
                return

        else:
            if self.calcCoolSmpWin != 0:
                tempSP = self.rampDownStageRate * exp(-self.cool_brake / self.calcCoolSmpWin *(self.time_elapsed - self.rampDownStageRampTime))
            else:
                tempSP = 0

            if self.pcr.sample_temp <= self.set_point + 1:
                self.prepare_hold()
                self.pid.m = self.pid2.m
                self.pid.b = self.pid2.b
                self.pid.y = self.pid2.y
                return
        qPower  = (tempSP / self.rampDownStageRate)     * self.qMaxRampPid
        qPower += (1 - tempSP / self.rampDownStageRate) * self.qMaxHoldPid
        self.pid.SP = -tempSP
        self.pid.ffwd = self.pid.SP * self.blockMCP / qPower * 100
        self.qpid = qPower * self.pid.update() / 100
        if self.pid.SP >= self.coolSpCtrlActivRR * self.rampDownStageRate \
            or self.pid.SP >= self.coolSpCtrlActivSP:
            if self.spCtrlFirstActFlag == False:
                self.pid2.y = self.pcr.block_temp * 0.5
                self.spCtrlFirstActFlag = True
            self.qpid += qPower * self.pid2.update() / 100
        if self.pcr.block_temp <= self.set_point - self.calcCoolBlkOS:
            self.prepare_hold_under()
        self.peltier.mode = "cool"

    def ctrl_land_under(self):
        timeToSetPt = (self.set_point - self.pcr.sample_temp) / self.pcr.sample_rate
        if timeToSetPt < 0:
            self.pid.SP = (self.set_point - self.pcr.block_temp) / timeToSetPt
        else:
            self.pid.SP = 3
        if self.pcr.block_temp + self.smoothRegionOverWin >= self.set_point:
            if self.pid.SP > self.smoothRegionOverRR:
                self.pid.SP = self.smoothRegionOverRR
        self.pid.ffwd = self.pid.SP * self.blockMCP / self.qMaxRampPid * 100
        self.qpid = self.qMaxRampPid * self.pid.update() / 100
        if self.pcr.block_temp + 0.25 >= self.set_point:
            self.prepare_hold()
        self.peltier.mode = "heat"

    def ctrl_hold_under(self):
        self.qpid = self.qMaxHoldPid * self.pid.update() / 100
        if self.pcr.sample_temp <= self.set_point + self.calcCoolSmpWin:
            self.prepare_land_under()
        self.peltier.mode = "heat"

    def ctrl_hold(self):
        self.qpid = self.qMaxHoldPid * self.pid.update() / 100
        self.peltier.mode = "heat"

    def prepare_hold_under(self):
        self.pid.reset()
        self.pid.load(self.pid_const, "Hold Under")
        self.pid.SP = (self.set_point - self.calcCoolBlkOS) * 0.5
        self.pid.m = self.pid2.m
        self.pid.b = self.pid2.b
        self.pid.y = self.pid2.y
        self.pid.ffwd = -self.qHeatLoss / self.qMaxHoldPid * 100        
        self.stage = "Hold Under"        

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
        if round(self.time - self.checkpoint, 3) >= self.period:
            self.checkpoint = self.time
            return True
        return False

    def calc_feed_forward(self):
        return 0

    def ramp_to(self, new_set_point, sample_rate):
        if self.set_point == new_set_point:
            return            
        self.pid.reset()
        self.start_time = self.time
        self.time_elapsed = 0
        self.set_point = new_set_point
        self.smpWinInRampUpFlag = False
        self.smpWinInRampDownFlag = False

        if new_set_point - self.pcr.block_temp > 2:
            self.ramp_dist = new_set_point - self.pcr.block_temp
            self.target_sample_rate = sample_rate / 100 * self.max_up_ramp
            self.ramp_time = self.ramp_dist / self.target_sample_rate
            self.prepare_ramp_up()
        elif new_set_point - self.pcr.block_temp < -2:
            self.ramp_dist = self.pcr.block_temp - new_set_point
            self.target_sample_rate = sample_rate / 100 * self.max_down_ramp
            self.ramp_time = self.ramp_dist / self.target_sample_rate
            self.prepare_ramp_down()
        else:
            self.prepare_hold()

    def output(self):
        Iset, Imeasure = self.peltier.output( self.qpid, 
                                            self.pcr.heat_sink_temp,
                                            self.pcr.block_temp,
                                            self.maxHeatIset,
                                            self.maxCoolIset
        )
        self.pcr.Iset = Iset
        self.pcr.Imeasure = Imeasure
 
    def update(self):
        self.update_feedback()
        self.run_control_stage()
        self.output()
    
    def tick(self, tick):
        self.time += tick
        if self.is_timer_fired():
            self.update()