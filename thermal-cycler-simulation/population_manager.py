from dna import DNA
from pid_specs import PID_Specs
from pcr_machine import PCR_Machine
from tbc_controller import TBC_Controller
from random import randint
from random import random
from protocol import Protocol

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

    def init_environment(self, block_temp=60, amb_temp=25, update_period=0.05, sample_volume=10):
        pcr_machine = PCR_Machine(      "pcr_trained_model.ml",
                                        sample_volume=sample_volume,
                                        sample_temp=block_temp,
                                        block_temp=block_temp,
                                        heat_sink_temp=amb_temp,
                                        block_rate=0,
                                        sample_rate=0,                                        
                                        amb_temp=amb_temp,
                                        update_period=update_period,
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
        if len(population) <= 1:
            print("ERROR: Only one creature left. Population is dead.")
            raise Exception

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
                
                setpoint1 = 60
                setpoint2 = 95
                hold_time = 35
                pcr, tbc = self.init_environment(block_temp=setpoint1)
                creature.blend_in(tbc)
                creature.score = 0                

                tbc.ramp_to(new_set_point=setpoint2, sample_rate=100)
                time_limit = 10 * (setpoint2 - setpoint1) / tbc.max_up_ramp
                sys_time = 0
                ctime = 0
                start_temp = setpoint1
                while True:
                    if tbc.stage != "Ramp Up":
                        avg_rate = (pcr.sample_temp - start_temp) / ctime
                        creature.score -= abs((avg_rate - tbc.max_up_ramp) / tbc.max_up_ramp) * 100
                        break
                    
                    if sys_time > time_limit:
                        creature.alive = False
                        break

                    tbc.tick(0.05)
                    pcr.tick(0.05)
                    ctime += 0.05
                    sys_time += 0.05

                if tbc.stage == "Overshoot Over" and creature.alive:
                    start_temp = pcr.sample_temp
                    ctime = 0
                    while True:
                        if tbc.stage != "Overshoot Over":
                            avg_rate = (pcr.sample_temp - start_temp) / ctime
                            creature.score -= abs((avg_rate - tbc.max_up_ramp) / tbc.max_up_ramp) * 100
                            break

                        if sys_time > time_limit:
                            creature.alive = False
                            break

                        tbc.tick(0.05)
                        pcr.tick(0.05)
                        ctime += 0.05
                        sys_time += 0.05                    

                if tbc.stage == "Hold Over" and creature.alive:
                    hold_temp = tbc.pid2.SP * 2
                    min_deviation = 0
                    max_deviation = 0                    
                    while True:
                        if tbc.stage != "Hold Over":
                            if max_deviation > 0.25:
                                creature.score -= (max_deviation - 0.25) * 10
                            if min_deviation > 0.25:
                                creature.score -= (min_deviation - 0.25) * 10
                            break
                            
                        if sys_time > time_limit:
                            creature.alive = False
                            break

                        tbc.tick(0.05)
                        pcr.tick(0.05)  
                        if pcr.block_temp - hold_temp > max_deviation:
                            max_deviation = pcr.block_temp - hold_temp
                        elif hold_temp - pcr.block_temp > min_deviation:
                            min_deviation = hold_temp - pcr.block_temp                     
                        sys_time += 0.05     

                if tbc.stage == "Land Over" and creature.alive:
                    start_temp = pcr.block_temp
                    sample_overshoot = 0                    
                    ctime = 0
                    while True:
                        if tbc.stage != "Land Over":
                            avg_rate = abs(pcr.block_temp - start_temp) / ctime
                            creature.score += avg_rate / 2
                            creature.score -= sample_overshoot * 20
                            break
                        
                        if sys_time > time_limit:
                            creature.alive = False
                            break

                        tbc.tick(0.05)
                        pcr.tick(0.05)
                        if pcr.sample_temp - setpoint2 > sample_overshoot:
                            sample_overshoot = pcr.sample_temp - setpoint2
                        ctime += 0.05
                        sys_time += 0.05                         

                # tbc_controller must reach stage "Hold" at this point
                if not creature.alive:
                    creature.score -= 200
                    # giving the creature second chance to live
                    creature.alive = True
                    setpoint1 = 60
                    setpoint2 = 95
                    hold_time = 35
                    pcr, tbc = self.init_environment(block_temp=setpoint2)
                    tbc.ramp_to(new_set_point=setpoint2, sample_rate=100)
                    creature.blend_in(tbc)
                else:
                    avg_rate = (pcr.sample_temp - setpoint1) / sys_time                
                    creature.score -= abs((avg_rate - tbc.max_up_ramp) / tbc.max_up_ramp) * 200

                max_deviation = 0
                min_deviation = 0
                hold_temp = setpoint2                
                time_limit = hold_time                
                ctime = 0
                while True:
                    if tbc.stage != "Hold" or ctime > time_limit:
                        if max_deviation > 0.1:
                            creature.score -= (max_deviation - 0.1) * 30
                        if min_deviation > 0.1:
                            creature.score -= (min_deviation - 0.1) * 30
                        break

                    tbc.tick(0.05)
                    pcr.tick(0.05)
                    if pcr.sample_temp - hold_temp > max_deviation:
                        max_deviation = pcr.sample_temp - hold_temp
                    elif hold_temp - pcr.sample_temp > min_deviation:
                        min_deviation = hold_temp - pcr.sample_temp
                    ctime += 0.05

                tbc.ramp_to(new_set_point=setpoint1, sample_rate=100)
                time_limit = 10 * abs(setpoint2 - setpoint1) / tbc.max_down_ramp
                sys_time = 0
                ctime = 0
                start_temp = setpoint2
                while True:
                    if tbc.stage != "Ramp Down":
                        avg_rate = abs(pcr.sample_temp - start_temp) / ctime
                        creature.score -= abs((avg_rate - tbc.max_down_ramp) / tbc.max_down_ramp) * 100
                        break
                    if sys_time > time_limit:
                        creature.alive = False
                        break
                    tbc.tick(0.05)
                    pcr.tick(0.05)
                    ctime += 0.05
                    sys_time += 0.05                    

                if tbc.stage == "Overshoot Under" and creature.alive:
                    start_temp = pcr.sample_temp
                    ctime = 0
                    while True:
                        if tbc.stage != "Overshoot Under":
                            avg_rate = abs(pcr.sample_temp - start_temp) / ctime
                            creature.score -= abs((avg_rate - tbc.max_down_ramp) / tbc.max_down_ramp) * 100
                            break

                        if sys_time > time_limit:
                            creature.alive = False
                            break

                        tbc.tick(0.05)
                        pcr.tick(0.05)
                        ctime += 0.05
                        sys_time += 0.05                    

                if tbc.stage == "Hold Under" and creature.alive:
                    hold_temp = tbc.pid2.SP * 2
                    min_deviation = 0
                    max_deviation = 0                    
                    while True:
                        if tbc.stage != "Hold Under":
                            if max_deviation > 0.25:
                                creature.score -= (max_deviation - 0.25) * 10
                            if min_deviation > 0.25:
                                creature.score -= (min_deviation - 0.25) * 10
                            break
                            
                        if sys_time > time_limit:
                            creature.alive = False
                            break

                        tbc.tick(0.05)
                        pcr.tick(0.05)  
                        if pcr.block_temp - hold_temp > max_deviation:
                            max_deviation = pcr.block_temp - hold_temp
                        elif hold_temp - pcr.block_temp > min_deviation:
                            min_deviation = hold_temp - pcr.block_temp                     
                        sys_time += 0.05        

                if tbc.stage == "Land Under" and creature.alive:
                    start_temp = pcr.block_temp
                    sample_overshoot = 0                    
                    ctime = 0
                    while True:
                        if tbc.stage != "Land Under":
                            avg_rate = abs(pcr.block_temp - start_temp) / ctime
                            creature.score += avg_rate / 2                            
                            creature.score -= sample_overshoot * 20
                            break

                        if sys_time > time_limit:
                            creature.alive = False
                            break

                        tbc.tick(0.05)
                        pcr.tick(0.05)
                        if setpoint1 - pcr.sample_temp > sample_overshoot:
                            sample_overshoot = setpoint1 - pcr.sample_temp
                        ctime += 0.05
                        sys_time += 0.05         

                # tbc_controller must reach stage "Hold" at this point
                if not creature.alive:
                    creature.score -= 200
                else:
                    avg_rate = abs(pcr.sample_temp - setpoint2) / sys_time                
                    creature.score -= abs((avg_rate - tbc.max_down_ramp) / tbc.max_down_ramp) * 200

                print(f"Creature {loc} scores {creature.score}")

            population.sort(key=self.getScore, reverse=True)
            if i + 1 >= self.max_generation:
                break
            for i in range(0, self.pop_size // 2):
                population.pop()
            population = self.breed_population(population)

        population.sort(key=self.getScore, reverse=True)
        print("==============================================================")
        print(f"Best score is {population[0].score}")
        k = 0
        for group_index in range(0, 9):
            P  = population[0].genes[k]
            I  = population[0].genes[k + 1]
            D  = population[0].genes[k + 2]
            KI = population[0].genes[k + 3]
            KD = population[0].genes[k + 4]            
            k += 5
            print(f"Group {group_index}: P={P} I={I} D={D} KI={KI} KD={KD}")
        protocol = Protocol(listSP   =[ 95,  60], 
                            listRate =[100, 100], 
                            listHold =[ 35,  35], 
                            nCycles  =1, 
                            Tblock   =60, 
                            Tamb     =25
                            )
        population[0].blend_in(protocol.tbc_controller)
        protocol.run()            

if __name__ == "__main__":
    popMan = PopulationManager(max_generation=2, pop_size=4, mutation_chance=0.005)
    popMan.run()