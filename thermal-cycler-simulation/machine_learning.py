import pandas as pd
import joblib

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
        self.accuracy_window = 0.25    
        
    def set_accuracy_window(self, value):
        self.accuracy_window = value
    
    def load_data(self, path):
        dataset = pd.read_csv(path)        
        condition = dataset.iloc[:, :-1].values        
        result = dataset.iloc[:, -1].values        
        condition = self.feature_scaling(condition)    
        return condition, result

    def feature_scaling(self, dataset):
        if dataset.shape[1] == 6:
            scaler = [1, 0.1, 100, 1, 1, 1]
        elif dataset.shape[1] == 4:
            scaler = [0.1, 0.1, 1, 1]
        else:
            return dataset

        return dataset * scaler
    
    def train_model(self, train_path, test_path, algo='auto'):
        train_condition, train_result = self.load_data(train_path)        

        # Training the model
        if algo == "auto":
            list_models = []
            list_names = []
            print("--- Evaluating the score of all regressors")
            list_models.append( MLPRegressor(hidden_layer_sizes=(8,8,8,),
                                activation='relu',
                                solver='adam',
                                verbose=False,
                                warm_start=True,
                                max_iter=1000))
            list_names.append("Neural Network")

            list_models.append(KNeighborsRegressor(n_neighbors=5, weights='distance', leaf_size=30))
            list_names.append("K-Neighbors")

            list_models.append(RandomForestRegressor(n_estimators=10, n_jobs=-1, warm_start=True))
            list_names.append("Random Forest")

            list_models.append(AdaBoostRegressor(loss='square'))
            list_names.append("Ada Boost")

            list_models.append(GradientBoostingRegressor(loss='lad', warm_start=True))
            list_names.append("Gradient Boosting")

            list_models.append(BaggingRegressor(warm_start=True))
            list_names.append("Bagging")

            list_models.append(DecisionTreeRegressor(criterion='friedman_mse'))
            list_names.append("Decision Tree")

            list_models.append(SVR())
            list_names.append("SVR")

            list_models.append(NuSVR())
            list_names.append("NuSVR")            

            list_models.append(SGDRegressor(warm_start=True, average=False, learning_rate='optimal'))
            list_names.append("SGD")


            list_models.append(VotingRegressor(list(zip(list_names, list_models))))
            list_names.append("Voting")

            list_models.append(StackingRegressor(list(zip(list_names, list_models))))
            list_names.append("Stacking")


            max_score = 0
            model_loc = 0

            for loc in range(0, len(list_models)):
                list_models[loc] = list_models[loc].fit(train_condition, train_result)
                score = self.test_model(list_models[loc], test_path, model_name=list_names[loc], report=True)
                if score > max_score:
                    max_score = score
                    model_loc = loc
            print(f"--- The best regressor is {list_names[model_loc]} which scores {max_score}%\n")
            
            return list_models[model_loc]
        else:
            print("ERROR: Algorithm must be 'auto'")
            raise Exception

    
    def test_model(self, model, path, model_name="N.A.", report=True):        
        test_condition, test_result = self.load_data(path)
        test_prediction = model.predict(test_condition)
        total = len(test_prediction)
        correct = 0
        for i in range(0, total):
            if test_result[i] == 0:
                if abs(test_prediction[i]) <= 0.01:
                    correct += 1
            elif abs(test_prediction[i] - test_result[i]) / test_result[i] * 100 <= self.accuracy_window:               
                correct += 1
        accuracy = round(correct * 100 / total, 2)
        if report:
            print("[{}] Accuracy = {}% ({} / {})".format(model_name, accuracy, correct, total))
        return accuracy
    
    def save_model(self, model, path):
        # save the model to disk        
         joblib.dump(model, path)

    def load_model(self, path):
        # load the model from disk
        return joblib.load(path)

if __name__ == "__main__":
    learning = MachineLearning()
    
    learning.set_accuracy_window(5)
    model = learning.train_model(train_path="train/pcr_training_set.csv", 
                                 test_path="test/pcr_testing_set.csv")    
    learning.save_model(model, "pcr_trained_model.ml")

    learning.set_accuracy_window(10)
    model = learning.train_model(train_path="train/peltier_training_set.csv",
                                 test_path="test/peltier_testing_set.csv")    
    learning.save_model(model, "peltier_trained_model.ml")
