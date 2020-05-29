import pandas as pd
from joblib import dump, load
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Dropout


class MachineLearning:
    def __init__(self):
        pass
   
    def load_data(self, path):
        dataset = pd.read_csv(path)        
        condition = dataset.iloc[:, :-1].values        
        result = dataset.iloc[:, -1].values        
        condition = self.feature_scaling(condition)    
        return condition, result

    def feature_scaling(self, dataset):
        return dataset
    
    def train_model(self, train_path=None):
        X_train, y_train = self.load_data(train_path)        
        
        # Training the model
        regressor = Sequential()        
        regressor.add(Dense(units = 100, kernel_initializer = 'random_normal', activation = 'relu', input_dim = 5, bias_initializer='zeros'))
        regressor.add(Dropout(0.1))
        regressor.add(Dense(units = 1, kernel_initializer = 'random_normal', activation = 'relu'))

        # Compiling the ANN
        regressor.compile(optimizer = 'adam', loss = 'mean_squared_error',  metrics = ['accuracy'])

        # Fitting the ANN to the Training set
        regressor.fit(X_train, y_train, epochs = 100, batch_size = 20)     
        
        return regressor
    
    def test_model(self, regressor, test_path=None, acc_win=0.1,):
        
        X_test, y_true = self.load_data(test_path)        
        y_pred = regressor.predict(X_test)

        total = len(y_true)
        correct = 0
        for i in range(0, total):
            if abs(y_true[i] - y_pred[i]) <= acc_win:               
                correct += 1            
        score = correct / total * 100
        return score
    
    def save_model(self, model, path):
        # save the model to disk        
         dump(model, path)

    def load_model(self, path):
        # load the model from disk
        return load(path)

if __name__ == "__main__":
    learning = MachineLearning()
    regressor = learning.train_model(train_path="train/pcr_training_set.csv")
    score = learning.test_model(regressor, test_path="test/pcr_testing_set.csv", acc_win=0.25)
    print(score)
