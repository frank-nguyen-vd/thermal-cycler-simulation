import pandas as pd
import joblib
from population_manager import PopulationManager

from sklearn.neural_network import MLPRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import AdaBoostRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.ensemble import VotingRegressor
from sklearn.ensemble import BaggingRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.linear_model import SGDRegressor
from sklearn.ensemble import StackingRegressor
from sklearn.svm import SVR
from sklearn.svm import NuSVR        

class MachineLearning:
    def __init__(self):
        self.accuracy_window = 0.1
        
    def set_accuracy_window(self, value):
        self.accuracy_window = value
    
    def load_data(self, path):
        dataset = pd.read_csv(path)        
        condition = dataset.iloc[:, :-1].values        
        result = dataset.iloc[:, -1].values        
        condition = self.feature_scaling(condition)    
        return condition, result

    def feature_scaling(self, dataset):
        return dataset
    
    def train_model(self, train_path=None, test_path=None, algo='auto', report=False):
        train_condition, train_result = self.load_data(train_path)        
        # Training the model
        if algo == "auto":
            list_models = []
            list_names = []
            
            list_models.append( MLPRegressor(hidden_layer_sizes=(8,8,8,),
                                activation='relu',
                                solver='adam',
                                verbose=False,
                                warm_start=False,                                
                                max_iter=1000,))
            list_names.append("Neural Network")

            list_models.append(RandomForestRegressor(n_estimators=10, n_jobs=-1, warm_start=False))
            list_names.append("Random Forest")

            list_models.append(BaggingRegressor(warm_start=True))
            list_names.append("Bagging")
            
            list_models.append(VotingRegressor(list(zip(list_names, list_models))))
            list_names.append("Voting")

            for loc in range(0, len(list_models)):
                list_models[loc] = list_models[loc].fit(train_condition, train_result)

            max_score = {"single points":-1000000, "thermal profile":-1000000, "hybrid":-1000000}
            model_loc = {"single points": 0, "thermal profile":0, "hybrid":0}
            model_name = {}
            best_model = {}
            for loc in range(0, len(list_models)):
                score = self.test_model(pcr_model=list_models[loc], test_path=test_path,)
                for test_method in ["single points", "thermal profile", "hybrid"]:
                    if report:                    
                        print(f"{list_names[loc]} scores {score[test_method]} in {test_method} evaluation")
                    if score[test_method] > max_score[test_method]:
                        max_score[test_method] = score[test_method]
                        model_loc[test_method] = loc
            print("Conclusion:")
            for test_method in ["single points", "thermal profile", "hybrid"]:
                if report:                    
                    print(f"    - {list_names[model_loc[test_method]]} scores {max_score[test_method]}, the best in {test_method} evaluation")
                best_model[test_method] = list_models[model_loc[test_method]]
                model_name[test_method] = list_names[model_loc[test_method]]
            
            return best_model, model_name, max_score
        else:
            print("ERROR: Algorithm must be 'auto'")
            raise Exception

    
    def test_model(self, pcr_model, test_path=None, acc_win=0.1,):
        score = {}
        score["single points"] = 0
        score["thermal profile"] = 0
        score["hybrid"] = 0
        
        test_condition, test_result = self.load_data(test_path)
        test_prediction = pcr_model.predict(test_condition)

        total = len(test_prediction)
        correct = 0
        for i in range(0, total):
            if abs(test_prediction[i] - test_result[i]) <= acc_win:               
                correct += 1            
        score["single points"] = round(correct * 100 / total, 2)
        
        pop_man = PopulationManager()
        score["thermal profile"] = pop_man.eval_fitness_score(creature=pop_man.create_genius(),
                                                              pcr_model=pcr_model)

        score["hybrid"] = score["thermal profile"] + score["single points"]
        return score

    def pickBestMLmodels(   self,                             
                            pcr_train_path="train/pcr_training_set.csv",
                            pcr_test_path="test/pcr_testing_set.csv",
                            max_iters=10,
                            report=True,
                        ):        
        best_score = {"single points":-1000000, "thermal profile":-1000000, "hybrid":-1000000}
        best_model = {}
        best_technique = {}
        for i in range(0, max_iters): 
            if report:
                print(f"\n--- Iteration {i} ---")           
            pcr_model, model_name, score = self.train_model(train_path=pcr_train_path, test_path=pcr_test_path, report=True,)        
            for test_method in ["single points", "thermal profile", "hybrid"]:            
                if score[test_method] > best_score[test_method]:
                    best_score[test_method] = score[test_method]
                    best_model[test_method] = pcr_model[test_method]
                    best_technique[test_method] = model_name[test_method]
        if report:
            print("\n")
            for test_method in ["single points", "thermal profile", "hybrid"]:            
                print(f"\n*** {best_technique[test_method]} scores {best_score[test_method]} after {max_iters} iterations in {test_method} evaluation\n")

        return best_model
    
    def save_model(self, model, path):
        # save the model to disk        
         joblib.dump(model, path)

    def load_model(self, path):
        # load the model from disk
        return joblib.load(path)

if __name__ == "__main__":
    learning = MachineLearning()

    best_model = learning.pickBestMLmodels(max_iters=100,)
    learning.save_model(best_model["single points"], "points_pcr_model.ml")
    learning.save_model(best_model["thermal profile"], "profile_pcr_model.ml")
    learning.save_model(best_model["hybrid"], "hybrid_pcr_model.ml")


