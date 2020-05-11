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
    
    def train_model(self, test_method="single points",                          
                          train_path=None, 
                          test_path=None, 
                          algo='auto', 
                          report=False):
        train_condition, train_result = self.load_data(train_path)        
        # Training the model
        if algo == "auto":
            list_models = []
            list_names = []
            print(f"--- Evaluating all regressors in {test_method} evaluation ---")
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
            for loc in range(0, len(list_models)):
                list_models[loc] = list_models[loc].fit(train_condition, train_result)
                score = self.test_model(test_method=test_method,
                                        pcr_model=list_models[loc],
                                        test_path=test_path,
                                        )
                if report:
                    print(f"{list_names[loc]} scores {score} in {test_method} evaluation")
                if score > max_score:
                    max_score = score
                    model_loc = loc
            if report:
                print(f"--- The best regressor is {list_names[model_loc]} which scores {max_score} in {test_method} evaluation\n")
            
            return list_models[model_loc], max_score
        else:
            print("ERROR: Algorithm must be 'auto'")
            raise Exception

    
    def test_model(self,
                    pcr_model=None,    
                    test_method="single points",
                    test_path=None,
                    acc_win=0.1,
                  ):
        score = 0
        if test_method == "single points" or test_method == "hybrid":
            test_condition, test_result = self.load_data(test_path)
            test_prediction = pcr_model.predict(test_condition)

            total = len(test_prediction)
            correct = 0
            for i in range(0, total):
                if abs(test_prediction[i] - test_result[i]) <= acc_win:               
                    correct += 1            
            score += round(correct * 100 / total, 2)
        if test_method == "thermal profile" or test_method == "hybrid":
            pop_man = PopulationManager(pcr_model=pcr_model)
            score += pop_man.eval_fitness_score(pop_man.create_genius())

        if score == 0:
            print("ERROR: undefined test method")
            raise Exception

        return score

    def pickBestMLmodels(   self, 
                            test_method="thermal profile",
                            pcr_train_path="train/pcr_training_set.csv",
                            pcr_test_path="test/pcr_testing_set.csv",
                            max_iters=10,
                            report=True,
                        ):        
        best_score = -1000000
        best_pcr_model = None
        for i in range(0, max_iters):            
            pcr_model, score = self.train_model(train_path=pcr_train_path, 
                                            test_path=pcr_test_path,
                                            test_method=test_method,
                                            report=True,
                                            )        
            
            if score > best_score:
                best_score = score
                best_pcr_model = pcr_model
                if report:
                    print(f"[Iteration {i}] The best PCR Model scores {best_score} in {test_method} evaluation\n")
        if report:
            print(f"\n*** The best PCR Model scores {best_score} after {max_iters} iterations in {test_method} evaluation\n")

        return best_pcr_model
    
    def save_model(self, model, path):
        # save the model to disk        
         joblib.dump(model, path)

    def load_model(self, path):
        # load the model from disk
        return joblib.load(path)

if __name__ == "__main__":
    learning = MachineLearning()

    default_pcr = learning.pickBestMLmodels(test_method="single points", max_iters=5,)
    learning.save_model(default_pcr, "points_pcr_model.ml")
    
    best_pcr = learning.pickBestMLmodels(test_method="thermal profile", max_iters=5,)
    learning.save_model(best_pcr, "profile_pcr_model.ml")
    
    default_pcr = learning.pickBestMLmodels(test_method="hybrid", max_iters=5,)
    learning.save_model(default_pcr, "hybrid_pcr_model.ml")


