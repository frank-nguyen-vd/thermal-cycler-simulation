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
    
    def train_model(self, train_file_path=None, 
                          test_method="single points",
                          test_file_path=None, 
                          algo='auto', 
                          default_pcr_path=None, 
                          default_peltier_path=None):

        train_condition, train_result = self.load_data(train_file_path)        
        # Training the model
        if algo == "auto":
            list_models = []
            list_names = []
            print("--- Evaluating the score of all regressors")
            list_models.append( MLPRegressor(hidden_layer_sizes=(8,8,8,),
                                activation='relu',
                                solver='adam',
                                verbose=False,
                                warm_start=False,                                
                                max_iter=1000,))
            list_names.append("Neural Network")

            list_models.append(RandomForestRegressor(n_estimators=10, n_jobs=-1, warm_start=False))
            list_names.append("Random Forest")

            list_models.append(GradientBoostingRegressor())
            list_names.append("Gradient Boosting")

            list_models.append(BaggingRegressor(warm_start=True))
            list_names.append("Bagging")

            list_models.append(DecisionTreeRegressor(criterion='friedman_mse'))
            list_names.append("Decision Tree")

            list_models.append(KNeighborsRegressor(n_neighbors=10, weights='distance', leaf_size=30))
            list_names.append("K-Neighbors")

            list_models.append(VotingRegressor(list(zip(list_names, list_models))))
            list_names.append("Voting")


            max_score = -1000000
            model_loc = 0
            pcr_model = None
            peltier_model = None            
            if test_method == "thermal profile":
                if default_pcr_path != None:
                    pcr_model = self.load_model(default_pcr_path)
                if default_peltier_path != None:
                    peltier_model = self.load_model(default_peltier_path)

            for loc in range(0, len(list_models)):
                list_models[loc] = list_models[loc].fit(train_condition, train_result)
                if pcr_model == None:
                    score = self.test_model(test_method=test_method,
                                            pcr_model=list_models[loc],
                                            peltier_model=peltier_model,
                                            test_file_path=test_file_path,
                                           )
                else:
                    score = self.test_model(test_method=test_method,
                                            pcr_model=pcr_model,
                                            peltier_model=list_models[loc],
                                            test_file_path=test_file_path,
                                           )

                if score > max_score:
                    max_score = score
                    model_loc = loc
            print(f"--- The best regressor is {list_names[model_loc]} which scores {max_score}\n")
            
            return list_models[model_loc], max_score
        else:
            print("ERROR: Algorithm must be 'auto'")
            raise Exception

    
    def test_model(self,
                    test_method="single points",
                    pcr_model=None,                     
                    peltier_model=None,                     
                    test_file_path=None,
                  ):
        if test_method == "single points":
            test_condition, test_result = self.load_data(test_file_path)
            if pcr_model == None:
                test_prediction = peltier_model.predict(test_condition)
            else:
                test_prediction = pcr_model.predict(test_condition)

            total = len(test_prediction)
            correct = 0
            for i in range(0, total):
                if test_result[i] == 0:
                    if abs(test_prediction[i]) <= 0.1:
                        correct += 1
                elif abs(test_prediction[i] - test_result[i]) / test_result[i] * 100 <= self.accuracy_window:               
                    correct += 1            
            return round(correct * 100 / total, 2)
        elif test_method == "thermal profile":
            pop_man = PopulationManager(pcr_model=pcr_model, peltier_model=peltier_model,)
            return pop_man.eval_fitness_score(pop_man.create_genius())
        else:
            print("ERROR: undefined test method")
            raise Exception        

    def pickBestMLmodels(self, 
                            test_method="thermal profile",
                            pcr_train_path="train/pcr_training_set.csv",
                            pcr_test_path="test/pcr_testing_set.csv",
                            peltier_train_path="train/peltier_training_set.csv",
                            peltier_test_path="test/peltier_testing_set.csv",                            
                            default_pcr_path="default_pcr_model.ml",
                            default_peltier_path="default_peltier_model.ml",
                            max_iters=1,
                        ):        
        best_score = -1000000
        best_pcr_model = None
        for i in range(0, max_iters):            
            pcr_model, score = self.train_model(train_file_path=pcr_train_path, 
                                            test_file_path=pcr_test_path,
                                            test_method=test_method,
                                            default_peltier_path=default_peltier_path,
                                            )        
            
            if score > best_score:
                best_score = score
                best_pcr_model = pcr_model
                print(f"\nThe best PCR Model scores: {best_score}\n")        

        best_score = -1000000
        best_peltier_model = None
        for i in range(0, max_iters):
            
            peltier_model,score = learning.train_model(train_file_path=peltier_train_path, 
                                            test_file_path=peltier_test_path,
                                            test_method=test_method,
                                            default_pcr_path=default_pcr_path,
                                            )           
            
            if score > best_score:
                best_score = score
                best_peltier_model = peltier_model
                print(f"\nThe best Peltier Model scores: {best_score}\n")

        return best_pcr_model, best_peltier_model
    
    def save_model(self, model, path):
        # save the model to disk        
         joblib.dump(model, path)

    def load_model(self, path):
        # load the model from disk
        return joblib.load(path)

if __name__ == "__main__":
    learning = MachineLearning()

    # best_pcr, best_peltier = learning.pickBestMLmodels(test_method="single points")
    # learning.save_model(best_pcr, "default_pcr_model.ml")
    # learning.save_model(best_peltier, "default_peltier_model.ml")

    best_pcr, best_peltier = learning.pickBestMLmodels(test_method="thermal profile")
    learning.save_model(best_pcr, "best_pcr_model.ml")
    learning.save_model(best_peltier, "best_peltier_model.ml")    

