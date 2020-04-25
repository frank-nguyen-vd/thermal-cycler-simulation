import math

class  PCR_Machine:
    def __init__(self, 
                 model, 
                 sample_volume, 
                 sample_temp, 
                 block_temp, 
                 heat_sink_temp, 
                 block_rate=0, 
                 sample_rate=0,
                 update_period=0.2,
                 amb_temp=25
                ):
        self.model = model
        self.sample_volume = sample_volume
        self.sample_temp = sample_temp
        self.block_temp = block_temp
        self.heat_sink_temp = heat_sink_temp
        self.block_rate = block_rate
        self.sample_rate = sample_rate
        self.update_period = update_period                
        self.amb_temp = amb_temp
        self.calculate_conversion_constant(self.sample_volume)
        
    def calculate_conversion_constant(self, volume):
        heat_coeffs = [1.9017543860, 0.0604385965, -0.0000643860, 0.0000002982]
        cool_coeffs = [2.6573099415, 0.0906608187, -0.0006599415, 0.0000020760]     
        no_coeffs = len(heat_coeffs)
        self.heat_const = 0
        self.cool_const = 0        
        for i in range(0, no_coeffs):
            self.heat_const += heat_coeffs[i] * volume**i
            self.cool_const += cool_coeffs[i] * volume**i
        self.heat_conv = 1 - math.exp(-self.update_period / self.heat_const)
        self.cool_conv = 1 - math.exp(-self.update_period / self.cool_const)

    @property
    def heat_const(self):
        return self.heat_const

    @property
    def cool_const(self):
        return self.cool_const

    @property
    def sample_volume(self):        
        return self.sample_volume
    
    @sample_volume.setter
    def sample_volume(self, value):        
        self.sample_volume = value  
        
    @property
    def sample_temp(self):        
        return self.sample_temp
    
    @sample_temp.setter
    def sample_temp(self, value):        
        self.sample_temp = value        
        
    @property
    def block_temp(self):        
        return self.block_temp
    
    @block_temp.setter
    def block_temp(self, value):        
        self.block_temp = value

    @property
    def heat_sink_temp(self):        
        return self.heat_sink_temp
    
    @heat_sink_temp.setter
    def heat_sink_temp(self, value):        
        self.heat_sink_temp = value        
        
    @property
    def block_rate(self):        
        return self.block_rate
    
    @block_rate.setter
    def block_rate(self, value):        
        self.block_rate = value
        
    @property
    def sample_rate(self):        
        return self.sample_rate
    
    @sample_rate.setter
    def sample_rate(self, value):        
        self.sample_rate = value
        
    @property
    def update_period(self):        
        return self.update_period
    
    @update_period.setter
    def update_period(self, value):        
        self.update_period = value        
        
    def update_sample_params(self, new_block_temp):
        if new_block_temp > self.block_temp: # block is heating up
            conv_const = self.heat_conv
        else: # block is cooling down
            conv_const = self.cool_conv        
        new_sample_temp = self.sample_temp + conv_const * (new_block_temp - self.sample_temp)            
        self.sample_rate = (new_sample_temp - self.sample_temp) / self.update_period
        self.sample_temp = new_sample_temp
    
    
    def update_block_params(self, new_block_temp):
        self.block_rate = (new_block_temp - self.block_temp) / self.update_period
        self.block_temp = new_block_temp
    
    def update_heat_sink_temp(self, delta_Tblock):        
        if delta_Tblock > 0: # block is heating up
            # for peltier, when block is heated up, the heat sink is cooled down
            self.heat_sink_temp -= 0.01 * delta_Tblock 
        else: # block is cooling down
            # for peltier, when block is cooled down, the heat sink is heated up
            self.heat_sink_temp -= 0.05 * delta_Tblock

        # heat sink temp is cooled by fan
        self.heat_sink_temp -= 0.005 * (self.heat_sink_temp - self.amb_temp)
    
    def update(self, Iset, Imeasure):
        condition = [self.sample_volume,
                     self.update_period,
                     self.heat_sink_temp,
                     self.block_temp,
                     self.block_rate,
                     Iset,
                     Imeasure
                    ]
        new_block_temp = self.model.predict(condition)
        self.update_heat_sink_temp(new_block_temp - self.block_temp)
        self.update_sample_params(new_block_temp)        
        self.update_block_params(new_block_temp)
