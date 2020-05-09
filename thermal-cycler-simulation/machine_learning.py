import pandas as pd
import joblib
from sklearn.neural_network import MLPRegressor

class MachineLearning:
    def __init__(self):
        self.accuracy_window = 0.25    
        
    def set_accuracy_window(self, value):
        self.accuracy_window = value
    
    def load_data(self, path):
        dataset = pd.read_csv(path)        
        condition = dataset.iloc[:, :-1].values        
        result = dataset.iloc[:, -1].values        
    
        return condition, result
    
    def train_model(self, path, mod):
        train_condition, train_result = self.load_data(path)

        # Training the model
        if mod == "pcr":
            model = MLPRegressor(hidden_layer_sizes=(100,100,100,),
                                activation='relu',
                                solver='adam',
                                verbose=True,
                                max_iter=100)
        elif mod == "peltier":
            model = MLPRegressor(hidden_layer_sizes=(100,),
                                activation='relu',
                                solver='adam',
                                verbose=True,
                                max_iter=100)

        model = model.fit(train_condition, train_result)
        return model
    
    def test_model(self, model, path, report=True):        
        test_condition, test_result = self.load_data(path)
        test_prediction = model.predict(test_condition)
        total = len(test_prediction)
        correct = 0
        for i in range(0, total):
            if test_result[i] - self.accuracy_window <= test_prediction[i] <= test_result[i] + self.accuracy_window:
                correct += 1
        accuracy = round(correct * 100 / total, 2)
        if report:
            print("Total = {} Correct = {} Accuracy = {}".format(total, correct, accuracy))
        return accuracy
    
    def save_model(self, model, path):
        # save the model to disk        
         joblib.dump(model, path)

    def load_model(self, path):
        # load the model from disk
        return joblib.load(path)

if __name__ == "__main__":
    learning = MachineLearning()
    
    learning.set_accuracy_window(0.1)
    model = learning.train_model("train/pcr_training_set.csv", mod="pcr")
    learning.test_model(model, "test/pcr_testing_set.csv", report=True)
    learning.save_model(model, "pcr_trained_model.ml")

    learning.set_accuracy_window(0.25)
    model = learning.train_model("train/peltier_training_set.csv", mod="peltier")
    learning.test_model(model, "test/peltier_testing_set.csv", report=True)
    learning.save_model(model, "peltier_trained_model.ml")
