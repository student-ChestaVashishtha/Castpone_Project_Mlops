from flask import Flask,render_template,request
import mlflow,pickle,os
import pandas as pd
from prometheus_client import Counter,Histogram,generate_latest,CollectorRegistry,CONTENT_TYPE_LATEST
import time,string,re,dagshub
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import warnings
warnings.simplefilter("ignore",UserWarning)
warnings.filterwarnings("ignore")
import numpy as np
def lemmatization(text):
    lem=WordNetLemmatizer()
    t=text.split()
    text=[lem.lemmatize(word) for word in t]
    return " ".join(text)
def remove_stop_words(text):
    stop_words=set(stopwords.words('english'))
    text=[word for word in str(text).split() if word not in stop_words]
    return " ".join(text)
def removing_numbers(text):
    text=[char for char in text if not char.isdigit()]
    return "".join(text)
def lower_case(text):
    text=text.split()
    text=[word.lower() for word in text]
    return " ".join(text)
def removing_punctuations(text):
    text=re.sub('[%s]' % re.escape(string.punctuation),' ',text)
    text=text.replace('.',"")
    text=re.sub('/s+',' ',text).strip()
    return text
def removing_urls(text):
    url_pattern = re.compile(r'https?://\S+|www\.\S+')
    return url_pattern.sub(r'', text)
def removing_small_sentence(df):
    for i in range(len(df)):
        if len(df.text.iloc[i].split())<3:
            df.text.iloc[i] = np.nan
def normalize_text(text):
    text = lower_case(text)
    text = remove_stop_words(text)
    text = removing_numbers(text)
    text = removing_punctuations(text)
    text = removing_urls(text)
    text = lemmatization(text)

    return text 

MLFLOW_TRACKING_URI = "https://dagshub.com/student-ChestaVashishtha/Castpone_Project_Mlops.mlflow"
dagshub.init(repo_owner="student-ChestaVashishtha", repo_name="Castpone_Project_Mlops", mlflow=True)
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

app= Flask(__name__)
registry=CollectorRegistry()
REQUEST_COUNT=Counter("app_request_count","Total number of requests to repo",["method","endpoint"],registry=registry)
REQUEST_LATENCY=Histogram(  "app_request_latency_seconds", "Latency of requests in seconds", ["endpoint"], registry=registry
)
PREDICTION_COUNT = Counter(
    "model_prediction_count", "Count of predictions for each class", ["prediction"], registry=registry
)

model_name='my_model'
def get_latest_version_model(model_name):
    client=mlflow.MlflowClient()
    latest_version=client.get_latest_versions(model_name,stages=['Production'])
    if not latest_version:
        latest_version = client.get_latest_versions(model_name,stages=['None'])
    return latest_version[0].version if latest_version else None
model_version=get_latest_version_model(model_name)
model_uri=f'models:/{model_name}/{model_version}'
print(f'fetching model from {model_uri}')
model=mlflow.pyfunc.load_model(model_uri)
vectorizer=pickle.load(open('models/vectorizer.pkl','rb'))

@app.route('/')
def home():
    REQUEST_COUNT.labels(method="GET", endpoint="/").inc()
    start_time=time.time()
    response=render_template("index.html",result=None)
    REQUEST_LATENCY.labels(endpoint='/').observe(time.time()-start_time)
    return response
@app.route("/predict", methods=["POST"])
def predict():
    REQUEST_COUNT.labels(method="POST",endpoint='/predict').inc()
    start=time.time()
    text=request.form['text']
    text=normalize_text(text)
    features=vectorizer.transform([text])
    features_df=pd.DataFrame(features.toarray(),columns=[str(i) for i in range(features.shape[1])])
    result=model.predict(features_df)
    prediction=result[0]
    PREDICTION_COUNT.labels(prediction=str(prediction)).inc()

    # Measure latency
    REQUEST_LATENCY.labels(endpoint="/predict").observe(time.time() - start)

    return render_template("index.html", result=prediction)
@app.route("/metrics",methods=["GET"])
def metrics():
    return generate_latest(registry),200,{"Content-type" : CONTENT_TYPE_LATEST}
if __name__ == "__main__":
    # app.run(debug=True) # for local use
    app.run(debug=True, host="0.0.0.0", port=5000)  # Accessible from outside Docker


                    
