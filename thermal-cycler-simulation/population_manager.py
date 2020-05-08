from dna import DNA
from pid_specs import PID_Specs
from pcr_machine import PCR_Machine
from tbc_controller import TBC_Controller

class PopulationManager:
    def __init__(self, pop_size=10, max_generation=50):
        self.pop_size = pop_size
        self.max_generation = max_generation

    def create_population(self, pop_size):
        population = []
        pid_specs = PID_Specs()
        for i in range(0, pop_size):
            creature = DNA(pid_specs)
            population.append(creature)
        return population

    def init_environment(self):
        pcr_machine = PCR_Machine(      "pcr_trained_model.ml",
                                        sample_volume=10,
                                        sample_temp=60,
                                        block_temp=60,
                                        heat_sink_temp=25,
                                        block_rate=0,
                                        sample_rate=0,                                        
                                        amb_temp=25,
                                        update_period=0.05,
                                        start_time=0
                                        
        )
        tbc_controller = TBC_Controller(    pcr_machine,
                                            start_time=0,
                                            update_period=0.05,
                                            volume=10
        )
        return pcr_machine, tbc_controller

    def getScore(self, creature):
        return creature.score

    def run(self):
        population = self.create_population(self.pop_size)
        for i in range(0, self.max_generation):
            for creature in population:
                pcr, tbc = self.init_environment()                
                creature.score = 0
                tbc.ramp_to(new_set_point=95, sample_rate=100)
                creature.blend_in(tbc)
                expected_ramp_time = 34 / tbc.max_up_ramp
                time_limit = 1.5 * expected_ramp_time
                ctime = 0
                while tbc.stage == "Ramp Up" and ctime < time_limit:
                    tbc.tick(0.05)
                    pcr.tick(0.05)
                    ctime += 0.05

                avg_rate = 34 / ctime
                creature.score -= abs((avg_rate - tbc.max_up_ramp) / tbc.max_up_ramp)
                creature.score -= ctime - expected_ramp_time

                population.sort(self.getScore)
