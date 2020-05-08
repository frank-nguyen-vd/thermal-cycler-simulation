from dna import DNA
from pid_specs import PID_Specs
from pcr_machine import PCR_Machine
from tbc_controller import TBC_Controller
from random import randint
from random import random

class PopulationManager:
    def __init__(self, pop_size=100, max_generation=50, mutation_chance=0.01):
        self.pop_size = pop_size
        self.max_generation = max_generation
        self.mutation_chance = mutation_chance

    def create_population(self, pop_size):
        population = []
        
        for i in range(0, pop_size):
            creature = DNA(PID_Specs())
            creature.rand_DNA()
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

    def mate(self, dad, mom):
        size = dad.dnaLength
        offspring = DNA(PID_Specs())
        for i in range(0, size):
            if random() > 0.5: # 50% chance to get dad's gene
                offspring.genes[i] = dad.genes[i]
            else: # 50% chance to get mom's gene
                offspring.genes[i] = mom.genes[i]
            if random() < self.mutation_chance:
                offspring.rand_gene(i)
        return offspring

    def breed_population(self, population):
        new_pop = []
        size = len(population) - 1
        for i, dad in enumerate(population):            
            for no_of_offspring in range(0, 2):
                while True:
                    j = randint(0, size)
                    if i != j:                       
                        break
                mom = population[j]
                new_pop.append(self.mate(dad, mom))
        return new_pop

    def run(self):
        population = self.create_population(self.pop_size)        
        for i in range(0, self.max_generation):
            print(f"-------- Generation={i} Population={len(population)}")
            for loc, creature in enumerate(population):
                pcr, tbc = self.init_environment()                
                creature.score = 0
                tbc.ramp_to(new_set_point=95, sample_rate=100)
                creature.blend_in(tbc)
                
                time_limit = 1.5 * 34 / tbc.max_up_ramp
                ctime = 0
                while tbc.stage == "Ramp Up" and ctime < time_limit:
                    tbc.tick(0.05)
                    pcr.tick(0.05)
                    ctime += 0.05

                avg_rate = (pcr.sample_temp - 60) / ctime
                creature.score -= abs((avg_rate - tbc.max_up_ramp) / tbc.max_up_ramp)

                expected_ramp_time = (pcr.sample_temp - 60) / tbc.max_up_ramp
                creature.score -= ctime - expected_ramp_time

                print(f"Creature {loc} scores {creature.score}")

            population.sort(key=self.getScore, reverse=True)
            if i + 1 >= self.max_generation:
                break
            for i in range(0, self.pop_size // 2):
                population.pop()
            population = self.breed_population(population)

        population.sort(key=self.getScore, reverse=True)
        print(f"Best score is {population[0].score}")
        P = population[0].genes[0]
        I = population[0].genes[1]
        D = population[0].genes[2]
        KI = population[0].genes[3]
        KD = population[0].genes[4]
        print(f"P={P} I={I} D={D} KI={KI} KD={KD}")

if __name__ == "__main__":
    popMan = PopulationManager()
    popMan.run()