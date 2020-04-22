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
                 update_period=0.2
                ):
        self.model = model
        self._sample_volume = sample_volume
        self._sample_temp = sample_temp
        self._block_temp = block_temp
        self._heat_sink_temp = heat_sink_temp
        self._block_rate = block_rate
        self._sample_rate = sample_rate
        self._update_period = update_period                
        self.calculate_conversion_constant(self._sample_volume)
        
    def calculate_conversion_constant(self, volume):
        heat_coeffs = [1.9017543860, 0.0604385965, -0.0000643860, 0.0000002982]
        cool_coeffs = [2.6573099415, 0.0906608187, -0.0006599415, 0.0000020760]     
        no_coeffs = len(heat_coeffs)
        heat_const = 0
        cool_const = 0        
        for i in range(0, no_coeffs):
            heat_const += heat_coeffs[i] * volume**i
            cool_const += cool_coeffs[i] * volume**i
        self.heat_conv = 1 - math.exp(-self.update_period / heat_const)
        self.heat_conv = 1 - math.exp(-self.update_period / cool_const)

    @property
    def sample_volume(self):        
        return self._sample_volume
    
    @sample_volume.setter
    def sample_volume(self, value):        
        self._sample_volume = value  
        
    @property
    def sample_temp(self):        
        return self._sample_temp
    
    @sample_temp.setter
    def sample_temp(self, value):        
        self._sample_temp = value        
        
    @property
    def block_temp(self):        
        return self._block_temp
    
    @block_temp.setter
    def block_temp(self, value):        
        self._block_temp = value

    @property
    def heat_sink_temp(self):        
        return self._heat_sink_temp
    
    @heat_sink_temp.setter
    def heat_sink_temp(self, value):        
        self._heat_sink_temp = value        
        
    @property
    def block_rate(self):        
        return self._block_rate
    
    @block_rate.setter
    def block_rate(self, value):        
        self._block_rate = value
        
    @property
    def sample_rate(self):        
        return self._sample_rate
    
    @block_rate.setter
    def sample_rate(self, value):        
        self._sample_rate = value
        
    @property
    def update_period(self):        
        return self._update_period
    
    @update_period.setter
    def update_period(self, value):        
        self._update_period = value        
        
    def update_sample_params(self, new_block_temp):
        if new_block_temp > self._block_temp: # block is heating up
            conv_const = self.heat_conv
        else: # block is cooling down
            conv_const = self.cool_conv        
        new_sample_temp = self._sample_temp + conv_const * (new_block_temp - self._sample_temp)            
        self._sample_rate = (new_sample_temp - self._sample_temp) / self._update_period
        self._sample_temp = new_sample_temp
    
    
    def update_block_params(self, new_block_temp):
        self._block_rate = (new_block_temp - self._block_temp) / self._update_period
        self._block_temp = new_block_temp
    
    def update_heat_sink_params(self, delta_Tblock):        
        if delta_Tblock > 0: # block is heating up
            self._heat_sink_temp -= 0.01 * delta_Tblock
        else: # block is cooling down
            self._heat_sink_temp -= 0.05 * delta_Tblock
    
    def update(self, Iset, Imeasure):
        condition = [self._sample_volume,
                     self._update_period,
                     self._heat_sink_temp,
                     self._block_temp,
                     self._block_rate,
                     Iset,
                     Imeasure
                    ]
        new_block_temp = self.model.predict(condition)
        self.update_heat_sink_temp(new_block_temp - self._block_temp)
        self.update_sample_params(new_block_temp)        
        self.update_block_params(new_block_temp)
