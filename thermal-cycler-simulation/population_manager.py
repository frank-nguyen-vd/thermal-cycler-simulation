from dna import DNA
from pcr_machine import PCR_Machine
from tbc_controller import TBC_Controller
from random import randint
from random import random
from protocol import Protocol
from peltier import Peltier
import joblib

class PopulationManager:
    def __init__(self, 
                    pop_size=100,
                    max_generation=50,
                    mutation_chance=0.01,                    
                    fast_test="points_pcr_model.ml",
                    detailed_test="profile_pcr_model.ml",
                    accurate_test="hybrid_pcr_model.ml",                    
                ):        
        self.pop_size = pop_size
        self.max_generation = max_generation
        self.mutation_chance = mutation_chance        
        self.fast_test = fast_test
        self.detailed_test = detailed_test
        self.accurate_test = accurate_test        
        

    def create_population(self, pop_size, genius=True):
        population = []
        
        for i in range(0, pop_size - 1):
            creature = DNA()
            creature.generate_DNA()
            population.append(creature)

        if genius:
            population.append(self.create_genius())
        else:
            creature = DNA()
            creature.generate_DNA()
            population.append(creature)

        return population
    
    def load_model(self, path):
        return joblib.load(path)

    def init_environment(self, pcr_model, block_temp=60, amb_temp=25, update_period=0.05, sample_volume=10):        
        pcr_machine = PCR_Machine(  pcr_model=pcr_model,                                    
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

        tbc_controller = TBC_Controller(    PCR_Machine=pcr_machine,
                                            Peltier=Peltier(),
                                            start_time=0,
                                            update_period=update_period,
                                            volume=10
        )
        return pcr_machine, tbc_controller

    def getScore(self, creature):
        return creature.score

    def mate(self, dad, mom):
        size = dad.dnaLength
        offspring = DNA()
        for i in range(0, size):
            if random() > 0.5: # 50% chance to get dad's gene
                offspring.dna[i] = dad.dna[i]
            else: # 50% chance to get mom's gene
                offspring.dna[i] = mom.dna[i]
            if random() < self.mutation_chance:
                offspring.mutate_gene(i)
        return offspring

    def create_genius(self):
        genius = DNA()
        genius.dna = [  3,0.06,0.0001,10,5, # PID Ramp Up
                        7,0.05,0,2,5,       # PID Overshoot Over 
                        1,0.04,0.01,5,10,   # PID Hold Over
                        10,0.03,0,2,5,      # PID Land Over
                        0.9,0.04,0.01,5,10, # PID Hold
                        3,0.06,0.0001,10,5, # PID Ramp Down
                        7,0.05,0,2,5,       # PID Overshoot Under
                        1,0.04,0.01,5,10,   # PID Hold Under
                        10,0.03,0,2,5,      # PID Land Under
                        2.8, # Max Heat Overshoot
                        3.4, # Max Cool Overshoot
                        2, # Heat Sample Window
                        2, # Cool Sample Window
                        40, # Max Hold Power
                        150, # Max Ramp Power
                        4, # Heat Block Window
                        3, # Cool Block Window
                        1.2, # Heat Overshoot Attenuation
                        0.2, # Heat Overshoot Activation RR
                        0.1, # Heat Overshoot Activation SP
                        1.5, # Cool Overshoot Attenuation
                        0.3, # Cool Overshoot Activation RR
                       -0.1, # Cool Overshoot Activation SP
                        1.6, # Temp Ctrl Over RR Limit
                        1.5, # Temp Ctrl Under RR Limit
                        1.5, # Temp Ctrl Over Block Window
                        1.75, # Temp Ctrl Under Block Window
                    ]
        return genius

    def breed_population(self, population, genius=True):
        if population == []:
            return self.create_population(pop_size=self.pop_size, genius=genius)

        if len(population) <= 1:
            print("ERROR: Only one creature left. Population is dead.")
            raise Exception

        new_pop = []
        if genius:
            new_pop.append(self.create_genius())
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
        if genius:
            new_pop.pop()
        return new_pop

    def eval_fitness_score(self, creature, pcr_model, update_period=0.05, dt=0.05,
                           death_penalty=1000, rr_penalty=1, temp_penalty=50, temp_window=0.25,
                           time_window=2,):
        low_temp = 60
        high_temp = 95
        hold_time = 10
        pcr, tbc = self.init_environment(pcr_model, block_temp=low_temp, update_period=update_period)
        creature.blend_in(tbc)
        creature.target_up_rate = tbc.max_up_ramp
        creature.target_down_rate = tbc.max_down_ramp

        ####### EVALUATE "RAMP UP" #######
        creature.score = 0
        tbc.ramp_to(new_set_point=high_temp, sample_rate=100)
        time_limit = time_window * (high_temp - low_temp) / tbc.max_up_ramp
        ctime = 0        
        checkpoint = high_temp - 1
        while pcr.sample_temp < checkpoint:
            if ctime > time_limit:
                creature.alive = False
                break
            tbc.tick(dt)
            pcr.tick(dt)
            ctime += dt

        if not creature.alive:
            # Death Penalty for not completing RAMP UP
            creature.score -= death_penalty
            # Death Penalty for not going through PRE HOLD
            creature.score -= death_penalty

            # giving the creature another chance to live
            creature.alive = True                    
            pcr.reset(sample_temp=high_temp, block_temp=high_temp)
            tbc.reset(set_point=high_temp)            
            # Skip PRE HOLD, go to HOLD
            tbc.ramp_to(new_set_point=high_temp, sample_rate=100)                    
        else:
            creature.measured_up_rate = (pcr.sample_temp - low_temp) / ctime
            creature.score -= abs(creature.measured_up_rate - tbc.max_up_ramp) / tbc.max_up_ramp * 100 * rr_penalty


        ####### EVALUATE "PRE HOLD" AND "HOLD" #######
        overshoot = 0
        up_deviation = 0
        down_deviation = 0
        ctime = 0
        while ctime < hold_time:
            if tbc.stage == "Hold":
                if pcr.sample_temp - high_temp > up_deviation:
                    up_deviation = pcr.sample_temp - high_temp
                elif high_temp - pcr.sample_temp > down_deviation:
                    down_deviation = high_temp - pcr.sample_temp
            else:
                if pcr.sample_temp - high_temp > overshoot:
                    overshoot = pcr.sample_temp - high_temp
            tbc.tick(dt)
            pcr.tick(dt)
            ctime += dt
        
        creature.heat_overshoot = overshoot
        creature.max_up_deviation = up_deviation
        creature.max_down_deviation = down_deviation

        if up_deviation > 1 or down_deviation > 1:
            creature.score -= death_penalty # creature is dead
            # give the creature another chance to live
            pcr.reset(sample_temp=high_temp, block_temp=high_temp)
            tbc.reset(set_point=high_temp)            
        else:
            if overshoot > temp_window:
                creature.score -= overshoot * temp_penalty
            if up_deviation > temp_window:
                creature.score -= up_deviation * temp_penalty
            if down_deviation > temp_window:
                creature.score -= down_deviation * temp_penalty
        

        ####### EVALUATE "RAMP DOWN" #######        
        tbc.ramp_to(new_set_point=low_temp, sample_rate=100)
        time_limit = time_window * (high_temp - low_temp) / tbc.max_down_ramp
        ctime = 0
        checkpoint = low_temp + 1        
        while pcr.sample_temp > checkpoint:
            if ctime > time_limit:
                creature.alive = False
                break
            tbc.tick(dt)
            pcr.tick(dt)
            ctime += dt

        if not creature.alive:
             # Death Penalty for not completing RAMP DOWN
            creature.score -= death_penalty
             # Death Penalty for not making it to PRE HOLD
            creature.score -= death_penalty

            return creature.score  # no more chance to live
        
        creature.measured_down_rate = (high_temp - pcr.sample_temp) / ctime
        creature.score -= abs(creature.measured_down_rate - tbc.max_down_ramp) / tbc.max_down_ramp * 100 * rr_penalty

        ####### EVALUATE "PRE HOLD" #######
        overshoot = 0
        while tbc.stage != "Hold":
            if ctime > time_limit:
                creature.alive = False
                break
            if low_temp - pcr.sample_temp > overshoot:
                overshoot = low_temp - pcr.sample_temp
            tbc.tick(dt)
            pcr.tick(dt)
            ctime += dt
        creature.cool_overshoot = overshoot
        if not creature.alive:
            creature.score -= death_penalty
        elif overshoot > temp_window:
            creature.score -= temp_penalty

        return creature.score

    def export_creature(self, creature, filepath):
        import csv
        with open(filepath, 'w', newline='') as file:
            writer = csv.writer(file)            
            writer.writerow([f"Creature scores {creature.score:.2f} (higher score, better performance)"])
            writer.writerow([f"Target Up Rate = {creature.target_up_rate:.2f} Measure Up Rate = {creature.measured_up_rate:.2f}"])
            writer.writerow([f"Target Down Rate = {creature.target_down_rate:.2f} Measure Up Rate = {creature.measured_down_rate:.2f}"])
            writer.writerow([f"Heat Overshoot = {creature.heat_overshoot:.2f} Cool Overshoot = {creature.cool_overshoot:.2f}"])
            writer.writerow([f"Sample deviation during Hold: +{creature.max_up_deviation:.2f} to -{creature.max_down_deviation:.2f}"])            
            writer.writerow(["========== LIST OF TUNING PARAMETERS =========="])
            for k in range(0, creature.dnaLength):
                writer.writerow([creature.specs[k][3] + f" = {creature.dna[k]:.4f}"])

        protocol = Protocol(listSP   =[ 95,  60], 
                            listRate =[100, 100], 
                            listHold =[ 35,  35], 
                            nCycles  =1, 
                            Tblock   =60, 
                            Tamb     =25,
                            pcr_path=self.accurate_test,                            
                            )
        creature.blend_in(protocol.tbc_controller)
        protocol.run(record_path=filepath, record_mode='a')  

    def run(self, stone_age=-800, golden_age=-40, record_path=None, genius=True, stagnant_period=50):
        population = []
        best_creature = DNA()
        best_creature.score = -1000000
        best_pop_score = -1000000
        pop_score = -1000000
        cgeneration = 0
        for noGeneration in range(0, self.max_generation):
            population = self.breed_population(population=population, genius=genius)
            print(f"-------- Generation={noGeneration} Population={len(population)}")
            
            if pop_score < stone_age:
                strategy = self.fast_test
            elif pop_score < golden_age:
                strategy = self.detailed_test
            else:
                strategy = self.accurate_test

            for loc, creature in enumerate(population):
                self.eval_fitness_score(creature=creature, pcr_model=self.load_model(strategy))
                print(f"Creature {loc} scores {creature.score} fitness points")

            population.sort(key=self.getScore, reverse=True)
            if population[0].score > best_creature.score:
                best_creature = population[0].copy()                
            pop_score = 0
            pop_size = self.pop_size // 2
            for i in range(0, pop_size):
                pop_score += population[i].score
                population.pop()
            pop_score = pop_score / pop_size
            print(f"*** Generation {noGeneration} scores {pop_score} fitness points\n\n")

            if pop_score > best_pop_score:
                best_pop_score = pop_score
                cgeneration = 0
            elif cgeneration >= stagnant_period:
                print(f"WARNING: Population hasn't improved its score {best_pop_score} for {stagnant_period} generations. Algorithm ends.\n")
                break
            else:
                cgeneration += 1


        print("==============================================================")
        print(f"The best creature score is {best_creature.score} fitness points")
        self.export_creature(best_creature, record_path[:-4] + f"score{int(best_creature.score)}" + record_path[-4:])
          

if __name__ == "__main__":
    max_gen = 1
    max_pop = 4
    popMan = PopulationManager( max_generation=max_gen, 
                                pop_size=max_pop, 
                                mutation_chance=0.01,                                
                                fast_test="points_pcr_model.ml",
                                detailed_test="profile_pcr_model.ml",
                                accurate_test="hybrid_pcr_model.ml",                                
                              )    
    popMan.run(record_path=f"pop{max_pop}gen{max_gen}.csv", 
               genius=True, 
               stagnant_period=50,
               stone_age=-800,
               golden_age=-40,
              )
