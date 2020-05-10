from dna import DNA
from pid_specs import PID_Specs
from pcr_machine import PCR_Machine
from tbc_controller import TBC_Controller
from random import randint
from random import random
from protocol import Protocol

class PopulationManager:
    def __init__(self, pop_size=100, max_generation=50, mutation_chance=0.01, record_filepath="protocol.csv"):
        self.pop_size = pop_size
        self.max_generation = max_generation
        self.mutation_chance = mutation_chance
        self.record_filepath = record_filepath

    def create_population(self, pop_size):
        population = []
        
        for i in range(0, pop_size - 1):
            creature = DNA(PID_Specs())
            creature.rand_DNA()
            population.append(creature)
        
        population.append(self.create_genius())
        return population

    def init_environment(self, block_temp=60, amb_temp=25, update_period=0.05, dt=0.025, sample_volume=10):
        pcr_machine = PCR_Machine(      "pcr_trained_model.ml",
                                        sample_volume=sample_volume,
                                        sample_temp=block_temp,
                                        block_temp=block_temp,
                                        heat_sink_temp=amb_temp,
                                        block_rate=0,
                                        sample_rate=0,                                        
                                        amb_temp=amb_temp,
                                        update_period=dt,
                                        start_time=0
                                        
        )
        tbc_controller = TBC_Controller(    pcr_machine,
                                            start_time=0,
                                            update_period=update_period,
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

    def create_genius(self):
        genius = DNA(PID_Specs())
        genius.genes = [3,0.06,0.0001,10,5,
                        7,0.05,0,2,5,
                        1,0.04,0.01,5,10,
                        10,0.03,0,2,5,
                        0.9,0.04,0.01,5,10,
                        3,0.06,0.0001,10,5,
                        7,0.05,0,2,5,
                        1,0.04,0.01,5,10,
                        10,0.03,0,2,5
                        ]
        return genius


    def breed_population(self, population):
        if population == []:
            return self.create_population(self.pop_size)

        if len(population) <= 1:
            print("ERROR: Only one creature left. Population is dead.")
            raise Exception

        new_pop = []
        size = len(population) - 1
        count_creatures = 2
        for i, dad in enumerate(population):            
            for no_of_offspring in range(0, 2):
                while True:
                    j = randint(0, size)
                    if i != j:                       
                        break
                mom = population[j]
                new_pop.append(self.mate(dad, mom))
                count_creatures += 1
                if count_creatures >= self.pop_size:
                    break        
        new_pop.append(self.create_genius())
        return new_pop

    def eval_fitness_score(self, creature, update_period=0.05, dt=0.025):
        setpoint1 = 60
        setpoint2 = 95
        hold_time = 35
        pcr, tbc = self.init_environment(block_temp=setpoint1, update_period=update_period, dt=dt)
        creature.blend_in(tbc)
        creature.score = 0
        tbc.ramp_to(new_set_point=setpoint2, sample_rate=100)
        time_limit = 2.5 * (setpoint2 - setpoint1) / tbc.max_up_ramp
        ctime = 0
        up_deviation = 0
        while tbc.stage != "Hold":
            if ctime > time_limit:
                creature.alive = False
                break
            tbc.tick(dt)
            pcr.tick(dt)
            ctime += dt
            if pcr.sample_temp - setpoint2 > up_deviation:
                up_deviation = pcr.sample_temp - setpoint2                    

        if not creature.alive:
            creature.score -= 1000
            # giving the creature second chance to live
            creature.alive = True                    
            pcr, tbc = self.init_environment(block_temp=setpoint2, update_period=update_period, dt=dt)
            creature.blend_in(tbc)
            tbc.ramp_to(new_set_point=setpoint2, sample_rate=100)                    
        else:
            avg_rate = (pcr.sample_temp - setpoint1) / ctime
            creature.score -= abs(avg_rate - tbc.max_up_ramp) / tbc.max_up_ramp * 100
            if up_deviation > 0.25:
                creature.score -= up_deviation * 50

        up_deviation = 0
        down_deviation = 0
        ctime = 0
        while ctime < hold_time:
            if tbc.stage != "Hold":
                print("ERROR: TBC Controller is not at stage HOLD while holding at setpoint")
                raise Exception
            tbc.tick(dt)
            pcr.tick(dt)
            ctime += dt
            if pcr.sample_temp - setpoint2 > up_deviation:
                up_deviation = pcr.sample_temp - setpoint2
            elif setpoint2 - pcr.sample_temp > down_deviation:
                down_deviation = setpoint2 - pcr.sample_temp
            
        if up_deviation > 0.1:
            creature.score -= (up_deviation - 0.1) * 50
        if down_deviation > 0.1:
            creature.score -= (down_deviation - 0.1) * 50
        
        tbc.ramp_to(new_set_point=setpoint1, sample_rate=100)
        time_limit = 2.5 * (setpoint2 - setpoint1) / tbc.max_down_ramp
        ctime = 0
        down_deviation = 0
        while tbc.stage != "Hold":
            if ctime > time_limit:
                creature.alive = False
                break
            tbc.tick(dt)
            pcr.tick(dt)
            ctime += dt
            if setpoint1 - pcr.sample_temp > down_deviation:
                down_deviation = setpoint1 - pcr.sample_temp

        if not creature.alive:
            creature.score -= 1000
        else:
            avg_rate = (setpoint2 - pcr.sample_temp) / ctime
            creature.score -= abs(avg_rate - tbc.max_down_ramp) / tbc.max_down_ramp * 100
            if down_deviation > 0.25:
                creature.score -= down_deviation * 50

    def export_creature(self, creature, filepath):
        import csv
        stage = [  "Ramp Up", 
                    "Overshoot Over", 
                    "Hold Over", 
                    "Land Over", 
                    "Hold", 
                    "Ramp Down", 
                    "Overshoot Under", 
                    "Hold Under", 
                    "Land Under"
                ]
        with open(filepath, 'w', newline='') as file:
            writer = csv.writer(file)            
            writer.writerow(["Score"])
            writer.writerow([creature.score])            
            writer.writerow(["Stage", "P", "I", "D", "KI", "KD"])
            for k in range(0, 9):
                P  = creature.genes[5 * k]
                I  = creature.genes[5 * k + 1]
                D  = creature.genes[5 * k + 2]
                KI = creature.genes[5 * k + 3]
                KD = creature.genes[5 * k + 4]                                
                writer.writerow([stage[k], P, I, D, KI, KD])

        protocol = Protocol(listSP   =[ 95,  60], 
                            listRate =[100, 100], 
                            listHold =[ 35,  35], 
                            nCycles  =1, 
                            Tblock   =60, 
                            Tamb     =25,
                            record_filepath=filepath
                            )
        creature.blend_in(protocol.tbc_controller)
        protocol.run()  

    def run(self):
        population = []
        for noGeneration in range(0, self.max_generation):
            population = self.breed_population(population)
            print(f"-------- Generation={noGeneration} Population={len(population)}")
            for loc, creature in enumerate(population):
                self.eval_fitness_score(creature)
                print(f"Creature {loc} scores {creature.score} fitness points")

            population.sort(key=self.getScore, reverse=True)
            for i in range(0, self.pop_size // 2):
                population.pop()
            

        population.sort(key=self.getScore, reverse=True)
        print("==============================================================")
        print(f"The best score is {population[0].score} fitness points")
        group_name = ["Ramp Up", "Overshoot Over", "Hold Over", "Land Over", "Hold", "Ramp Down", "Overshoot Under", "Hold Under", "Land Under"]
        for k in range(0, 9):
            P  = population[0].genes[5 * k]
            I  = population[0].genes[5 * k + 1]
            D  = population[0].genes[5 * k + 2]
            KI = population[0].genes[5 * k + 3]
            KD = population[0].genes[5 * k + 4]                
            print(f"Stage {group_name[k]}: P={P:.4f} I={I:.4f} D={D:.4f} KI={KI:.4f} KD={KD:.4f}")
            
        self.export_creature(population[0], self.record_filepath)
        
    
          

if __name__ == "__main__":
    popMan = PopulationManager(max_generation=200, pop_size=100, mutation_chance=0.01, record_filepath="protocol.csv")
    popMan.run()