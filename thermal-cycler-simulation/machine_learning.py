import pandas as pd
import joblib
from sklearn.tree import DecisionTreeRegressor

class MachineLearning:
    def __init__(self):
        self.accuracy_window = 0    
        
    def set_accuracy_window(self, value):
        self.accuracy_window = value
    
    def load_data(self, path):
        dataset = pd.read_csv(path)        
        condition = dataset.iloc[:, :-1].values        
        result = dataset.iloc[:, -1].values        
    
        return condition, result
    
    def train_model(self, path):
        train_condition, train_result = self.load_data(path)
        # Training the model
        model = DecisionTreeRegressor(random_state=0)
        model.fit(train_condition, train_result)

        return model
    
    def test_model(self, model, path):
        test_condition, test_result = self.load_data(path)
        test_prediction = model.predict(test_condition)
        window = 0.25
        total = len(test_prediction)
        correct = 0
        for i in range(0, total):
            if test_result[i] - self.accuracy_window <= test_prediction[i] <= test_result[i] + self.accuracy_window:
                correct += 1
        value = round(correct * 100 / total, 2)
        print("The accuracy of model is {}".format(value))
    
    def save_model(self, model, path):
        # save the model to disk        
         joblib.dump(model, path)

    def load_model(self, path):
        # load the model from disk
        return joblib.load(path)