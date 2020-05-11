from dna import DNA
from pid_specs import PID_Specs
from pcr_machine import PCR_Machine
from tbc_controller import TBC_Controller
from random import randint
from random import random
from protocol import Protocol
from peltier import Peltier

class PopulationManager:
    def __init__(self, pop_size=100,
                    max_generation=50,
                    mutation_chance=0.01,
                    stagnant_period=10,
                    pcr_model=None,
                    pcr_model_path="best_pcr_model.ml",
                    record_filepath="protocol.csv"):
        self.pcr_model = pcr_model        
        self.pop_size = pop_size
        self.max_generation = max_generation
        self.mutation_chance = mutation_chance
        self.stagnant_period = stagnant_period
        self.pcr_model_path = pcr_model_path        
        self.record_filepath = record_filepath

    def create_population(self, pop_size):
        population = []
        
        for i in range(0, pop_size - 1):
            creature = DNA(PID_Specs())
            creature.rand_DNA()
            population.append(creature)
        
        population.append(self.create_genius())
        return population

    def init_environment(self, block_temp=60, amb_temp=25, update_period=0.05, sample_volume=10):
        
        pcr_machine = PCR_Machine(  pcr_model=self.pcr_model,
                                    path_to_model=self.pcr_model_path,
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

        peltier = Peltier()
            
        tbc_controller = TBC_Controller(    PCR_Machine=pcr_machine,
                                            Peltier=peltier,
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

    def eval_fitness_score(self, creature, update_period=0.05, dt=0.05):
        setpoint1 = 60
        setpoint2 = 95
        hold_time = 10
        pcr, tbc = self.init_environment(block_temp=setpoint1, update_period=update_period)
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
            pcr, tbc = self.init_environment(block_temp=setpoint2, update_period=update_period)
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
            
        if up_deviation > 0.25:
            creature.score -= up_deviation * 50
        if down_deviation > 0.25:
            creature.score -= down_deviation * 50
        
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

        return creature.score

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
        protocol.run(record_mode='a')  

    def run(self):
        population = []
        best_creature = DNA(PID_Specs())
        best_creature.score = -1000000
        best_pop_score = -1000000
        cgeneration = 0
        for noGeneration in range(0, self.max_generation):
            population = self.breed_population(population)
            print(f"-------- Generation={noGeneration} Population={len(population)}")
            
            for loc, creature in enumerate(population):
                self.eval_fitness_score(creature)                
                print(f"Creature {loc} scores {creature.score} fitness points")

            population.sort(key=self.getScore, reverse=True)
            if population[0].score > best_creature.score:
                best_creature.score = population[0].score
                best_creature.genes = population[0].genes.copy()
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
            elif cgeneration >= self.stagnant_period:
                print(f"WARNING: Population hasn't improved its score {best_pop_score} for {self.stagnant_period} generations. Algorithm ends.\n")
                break
            else:
                cgeneration += 1


        print("==============================================================")
        print(f"The best creature score is {best_creature.score} fitness points")
        group_name = ["Ramp Up", "Overshoot Over", "Hold Over", "Land Over", "Hold", "Ramp Down", "Overshoot Under", "Hold Under", "Land Under"]
        for k in range(0, 9):
            P  = best_creature.genes[5 * k]
            I  = best_creature.genes[5 * k + 1]
            D  = best_creature.genes[5 * k + 2]
            KI = best_creature.genes[5 * k + 3]
            KD = best_creature.genes[5 * k + 4]                
            print(f"Stage {group_name[k]}: P={P:.4f} I={I:.4f} D={D:.4f} KI={KI:.4f} KD={KD:.4f}")
            
        self.export_creature(best_creature, self.record_filepath[:-4] + f"score{int(best_creature.score)}" + self.record_filepath[-4:])
        
    
          

if __name__ == "__main__":
    max_gen = 500
    max_pop = 20
    popMan = PopulationManager( max_generation=max_gen, 
                                pop_size=max_pop, 
                                mutation_chance=0.0222,
                                stagnant_period=25,
                                pcr_model_path="hybrid_pcr_model.ml",
                                record_filepath=f"pop{max_pop}gen{max_gen}.csv",
                              )    
    popMan.run()
