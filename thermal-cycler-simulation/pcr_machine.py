import math
import joblib

class  PCR_Machine:
    def __init__(self, 
                 path_to_model, 
                 sample_volume, 
                 sample_temp, 
                 block_temp, 
                 heat_sink_temp, 
                 block_rate=0, 
                 sample_rate=0,                 
                 amb_temp=25,
                 update_period=0.008,
                 start_time=0
                ):
        self.model = self.load_model(path_to_model)
        self.sample_volume = sample_volume
        self.sample_temp = sample_temp
        self.block_temp = block_temp
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
        
    def update_sample_params(self, new_block_temp):
        if new_block_temp > self.block_temp: # block is heating up
            conv_const = self.heat_conv
        else: # block is cooling down
            conv_const = self.cool_conv        
        new_sample_temp = self.sample_temp + conv_const * (new_block_temp - self.sample_temp)            
        self.sample_rate = (new_sample_temp - self.sample_temp) / self.period
        self.sample_temp = new_sample_temp
    
    
    def update_block_params(self, new_block_temp):
        self.block_rate = (new_block_temp - self.block_temp) / self.period
        self.block_temp = new_block_temp
    
    def update_heat_sink_temp(self, new_block_temp):
        delta_Tblock = abs(new_block_temp - self.block_temp)
        if delta_Tblock > 0: # block is heating up
            # for peltier, when block is heated up, the heat sink is cooled down
            self.heat_sink_temp -= 0.01 * delta_Tblock 
        else: # block is cooling down
            # for peltier, when block is cooled down, the heat sink is heated up
            self.heat_sink_temp += 0.05 * delta_Tblock
        # heat sink temp is heated up by block temperature
        self.heat_sink_temp += 0.002 * (new_block_temp - self.heat_sink_temp)
        # heat sink temp is cooled by fan
        self.heat_sink_temp -= 0.007 * (self.heat_sink_temp - self.amb_temp)
    
    def update(self):
        condition = [self.sample_volume,
                     self.period,
                     self.heat_sink_temp,
                     self.block_temp,
                     self.block_rate,
                     self.Iset,
                     self.Imeasure
                    ]
        new_block_temp = self.model.predict([condition])[0]
        self.update_heat_sink_temp(new_block_temp)
        self.update_sample_params(new_block_temp)        
        self.update_block_params(new_block_temp)

    def is_timer_fired(self):
        if (self.time - self.checkpoint) >= self.period:
            self.checkpoint = self.time
            return True
        return False

    def tick(self, tick):
        self.time += tick
        if self.is_timer_fired():
            self.update()