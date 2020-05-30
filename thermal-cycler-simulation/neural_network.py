import pandas as pd
from joblib import dump, load
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Dropout
from keras.wrappers.scikit_learn import KerasRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


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
        # define base model
        def baseline_model():
            model = Sequential()
            model.add(Dense(13, input_dim=5, kernel_initializer='normal', activation='relu'))
            model.add(Dense(1, kernel_initializer='normal'))
            model.compile(loss='mean_squared_error', optimizer='adam')
            return model
        X_train, y_train = self.load_data(train_path)        
        # evaluate model with standardized dataset
        pipeline = []
        pipeline.append(('standardize', StandardScaler()))
        pipeline.append(('estimator', KerasRegressor(build_fn=baseline_model, epochs=25, batch_size=10, verbose=0)))
        pipeline = Pipeline(pipeline)
        pipeline.fit(X_train, y_train)
        
        return pipeline
    
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
