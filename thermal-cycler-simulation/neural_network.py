import pandas as pd
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Dropout
from keras.wrappers.scikit_learn import KerasRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from keras.models import load_model
import joblib
import pickle
import os


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
    
    def save_model(self, pipeline, folder='pcr_model'):
        os.makedirs(folder, exist_ok=True)
        pickle.dump(pipeline.named_steps['standardize'], open(f'{folder}/standardize.pkl', 'wb'))    
        pipeline.named_steps['estimator'].model.save(f'{folder}/estimator.h5')

    def load_model(self, folder='pcr_model'):
        standardize = pickle.load(open(f'{folder}/standardize.pkl','rb'))    
        build_model = lambda: x
        regressor = KerasRegressor(build_fn=build_model, epochs=1, batch_size=10, verbose=0)
        regressor.model = load_model(f'{folder}/estimator.h5')
        return Pipeline([('standardize', standardize), ('estimator', regressor)])

    
if __name__ == "__main__":
    learning = MachineLearning()
    pipeline = learning.train_model(train_path="train/pcr_training_set.csv")
    score = learning.test_model(pipeline, test_path="test/pcr_testing_set.csv", acc_win=0.1)
    print("Accuracy = {score:.2f}%")
    
    learning.save_model(pipeline)
    pipeline = learning.load_model()
    
    
