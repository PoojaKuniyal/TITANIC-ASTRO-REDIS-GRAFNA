# For calculating DATA DRIFT we want *current data* and *reference data*
# reference data - data on which our model is trained stored in feature store
# current data - user input into app

import pickle
import numpy as np
import pandas as pd
from flask import Flask,render_template,request,jsonify
from config.paths_config import *
from alibi_detect.cd import KSDrift
from src.feature_store import RedisFeatureStore
from sklearn.preprocessing import StandardScaler # scaling reference and current data
from src.logger import get_logger

from prometheus_client import start_http_server, Counter, Gauge

logger = get_logger(__name__)

app = Flask(__name__, template_folder="templates")

# set 2 counters -> *custom metrics* (prometheus)
# 1st counter - how many time drift is detected 
# 2d counter- how many time predicitons are made on your flask app

prediction_count = Counter('prediction_count', "Number of prediction count")
drift_count = Counter('drift_count', "Number of times data drift is detected" )


MODEL_PATH = MODEL_PATH
with open(MODEL_PATH,'rb') as model_file:
    model = pickle.load(model_file)

FEATURE_NAMES = ['Age', 'Fare', 'Pclass', 'Sex', 'Embarked', 'Familysize', 'Isalone',
       'HasCabin', 'Title', 'Pclass_Fare', 'Age_Fare']

feature_store = RedisFeatureStore()
scaler = StandardScaler()

def fit_scaler_on_reference_data():
    # retrieve all the data from feature_store, convert to pandas df and apply scaling
    entity_ids = feature_store.get_all_entiy_ids()
    all_features = feature_store.get_batch_features(entity_ids)

    all_features_df = pd.DataFrame.from_dict(all_features, orient='index')[FEATURE_NAMES]

    scaler.fit(all_features_df)

    return scaler.transform(all_features_df)

# training_data/ historcial data/ reference data

historical_data = fit_scaler_on_reference_data()
ksd = KSDrift(x_ref=historical_data, p_val=0.05)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.form
        Age = float(data['Age'])
        Fare =float(data['Fare'])
        Pclass = int(data['Pclass'])
        Sex = int(data['Sex'])
        Embarked = int(data["Embarked"])
        Familysize = int(data['Familysize'])
        Isalone = int(data["Isalone"])
        HasCabin = int(data['HasCabin'])
        Title = int(data['Title'])
        Pclass_Fare = float(data['Pclass_Fare'])
        Age_Fare = float(data['Age_Fare'])

        features = pd.DataFrame([[Age,Fare,Pclass,Sex,Embarked,Familysize,Isalone,HasCabin,Title,Pclass_Fare,Age_Fare]], columns=FEATURE_NAMES)

        ###  DATA DRIFT DETECTION

        features_scaled = scaler.transform(features)

        drift = ksd.predict(features_scaled)
        print("Drift response : ", drift)

        drift_response = drift.get('data',{})
        is_drift = drift_response.get('is_drift', None)

        if is_drift is not None and is_drift ==1 :
            print("Drift detected....")

            logger.info("Drift detected...")

            drift_count.inc()

            
        prediction = model.predict(features)[0]

        prediction_count.inc()

        result ='SURVIVED' if prediction==1 else 'DID NOT SURVIVED'

        return render_template('index.html', prediction_text=f'The prediction is: {result}')

    except Exception as e:
        return jsonify({'error': str(e)})
    
# inbuilt metrics of prometheus
@app.route('/metrics')

def metrics():
    from prometheus_client import generate_latest # will send all the metrics to route
    from flask import Response

    return Response(generate_latest(), content_type='text/plain') # prometheus dont understand text.html
if __name__ == "__main__":
    start_http_server(8000) # default port for metrics collection
    app.run(debug=True, host='0.0.0.0', port=5000)