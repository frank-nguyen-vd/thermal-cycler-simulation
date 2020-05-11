import math
import joblib

class  PCR_Machine:
    def __init__(self, 
                 pcr_model=None,
                 path_to_model="default_pcr_model.ml", 
                 sample_volume=10, 
                 sample_temp=60, 
                 block_temp=60, 
                 heat_sink_temp=25, 
                 block_rate=0, 
                 sample_rate=0,                 
                 amb_temp=25,
                 update_period=0.05,
                 start_time=0
                ):
        if pcr_model == None:
            self.pcr_model = self.load_model(path_to_model)
        else:
            self.pcr_model = pcr_model
        self.sample_volume = sample_volume
        self.sample_temp = sample_temp
        self.block_temp = block_temp
        self.prev_block_temp = block_temp
        self.heat_sink_temp = heat_sink_temp
        self.block_rate = block_rate
        self.sample_rate = sample_rate
        self.amb_temp = amb_temp        
        self.period = update_period
        self.time = start_time
        self.checkpoint = start_time
        self.calculate_conversion_constant(self.sample_volume)
        self.Iset = 0
        self.Imeasure = 0
        self.Vset = 0
        self.FIR_Filter = [0.0264, 0.1405, 0.3331, 0.3331, 0.1405, 0.0264]
        self.BlkTempData = [block_temp] * 5
        self.SmpRateData = [0] * 5
    
    def load_model(self, path):
        return joblib.load(path)
        
    def calculate_conversion_constant(self, volume):
        heat_coeffs = [1.9017543860, 0.0604385965, -0.0000643860, 0.0000002982]
        cool_coeffs = [2.6573099415, 0.0906608187, -0.0006599415, 0.0000020760]     
        no_coeffs = len(heat_coeffs)
        self.heat_const = 0
        self.cool_const = 0        
        for i in range(0, no_coeffs):
            self.heat_const += heat_coeffs[i] * volume**i
            self.cool_const += cool_coeffs[i] * volume**i
        self.heat_conv = 1 - math.exp(-self.period / self.heat_const)
        self.cool_conv = 1 - math.exp(-self.period / self.cool_const)

    def calcBlockInfo(self, new_block_temp):
        new_data = self.FIR_Filter[0] * new_block_temp
        for i in range(0, len(self.BlkTempData)):
            new_data += self.FIR_Filter[i + 1] * self.BlkTempData[i]
        self.BlkTempData.pop()
        self.BlkTempData.insert(0, new_block_temp)
        self.block_rate = (new_data - self.prev_block_temp) / self.period
        self.prev_block_temp = new_data
        self.block_temp = new_block_temp

    def calcSampleInfo(self, new_block_temp, isHeating):
        if isHeating:
            conv_const = self.heat_conv
        else:
            conv_const = self.cool_conv

        # update sample 
        new_sample_temp = self.sample_temp + conv_const * (new_block_temp - self.sample_temp)
        new_sample_rate = (new_sample_temp - self.sample_temp) / self.period

        self.SmpRateData.pop(0)
        self.SmpRateData.append(new_sample_rate)

        self.sample_rate = sum(self.SmpRateData) / 5
        self.sample_temp = new_sample_temp    

    def calcHeatSinkInfo(self, d_Tblock):
        if d_Tblock > 0: # block is heating up            
            # for peltier, when block is heated up, the heat sink is cooled down
            self.heat_sink_temp -= 0.01 * d_Tblock 

        else: # block is cooling down            
            # for peltier, when block is cooled down, the heat sink is heated up
            self.heat_sink_temp -= 0.1 * d_Tblock

        # heat sink temp is heated up by block temperature
        self.heat_sink_temp += 0.001 * (self.block_temp - self.heat_sink_temp)
        # heat sink temp is cooled by fan
        self.heat_sink_temp -= 0.007 * (self.heat_sink_temp - self.amb_temp)        

    def update(self):
        condition = [self.sample_volume,                     
                     self.block_temp,
                     self.block_rate,
                     self.Imeasure,
                    ]        
        d_Tblock = (self.pcr_model.predict([condition])[0] - self.block_temp) * self.period / 0.2
        new_block_temp = self.block_temp + d_Tblock
        self.calcBlockInfo(new_block_temp)
        self.calcSampleInfo(new_block_temp, d_Tblock > 0)
        self.calcHeatSinkInfo(d_Tblock)

    def is_timer_fired(self):
        if round(self.time - self.checkpoint, 3) >= self.period:
            self.checkpoint = self.time
            return True
        return False

    def tick(self, tick):
        self.time += tick
        if self.is_timer_fired():
            self.update()