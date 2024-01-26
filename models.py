import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn import svm
import joblib

class Document:
    def __init__(self, binary, models):
        self._binary = binary
        self._models = models
    
    def load(self):
        try:
            self._data = pd.read_csv(self._binary)
            return True
        except Exception as e:
            print(e)
            return False
    
    def process(self, model):
        y = self._models.process(model, self._data['Product Title'])
        self._data['Category ID'] = y
        return self._data.to_csv().encode()

    

class Models:
    def __init__(self):
        self._vectorizer = joblib.load('models/vectorizer.pkl')
        MNB = joblib.load('models/MNB.pkl')
        SVC = joblib.load('models/SVC.pkl')

        self._models = {'SVC': SVC, 'MNB': MNB}
    
    def get_models(self):
        return self._models.keys()
    
    def is_correct_model(self, model):
        return model in self._models

    def create_document(self, binary):
        return Document(binary, self)
    
    def process(self, model, X):
        X_v = self._vectorizer.transform(X)
        return self._models[model].predict(X_v)