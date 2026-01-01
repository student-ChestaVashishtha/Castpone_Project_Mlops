import numpy as np
import pandas as pd
import pickle
import json
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
import logging
import mlflow
import mlflow.sklearn
import dagshub
import os
from src.logger import logging


# Below code block is for production use
# -------------------------------------------------------------------------------------
# Set up DagsHub credentials for MLflow tracking
dagshub_token = os.getenv("CAPSTONE_TEST")
if not dagshub_token:
    raise EnvironmentError("CAPSTONE_TEST environment variable is not set")

os.environ["MLFLOW_TRACKING_USERNAME"] = dagshub_token
os.environ["MLFLOW_TRACKING_PASSWORD"] = dagshub_token

dagshub_url = "https://dagshub.com"
repo_owner = "student-ChestaVashishtha"
repo_name = "Castpone_Project_Mlops"

# Set up MLflow tracking URI
mlflow.set_tracking_uri(f'{dagshub_url}/{repo_owner}/{repo_name}.mlflow')
# -------------------------------------------------------------------------------------

# Below code block is for local use
# -------------------------------------------------------------------------------------
# MLFLOW_TRACKING_URI = "https://dagshub.com/student-ChestaVashishtha/Castpone_Project_Mlops.mlflow"
# dagshub.init(repo_owner="student-ChestaVashishtha", repo_name="Castpone_Project_Mlops", mlflow=True)
# mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
# -------------------------------------------------------------------------------------


def load_model(file_path: str):
    """Load the trained model from a file."""
    try:
        with open(file_path, 'rb') as file:
            model = pickle.load(file)
        logging.info('Model loaded from %s', file_path)
        return model
    except FileNotFoundError:
        logging.error('File not found: %s', file_path)
        raise
    except Exception as e:
        logging.error('Unexpected error occurred while loading the model: %s', e)
        raise

def load_data(file_path: str) -> pd.DataFrame:
    """Load data from a CSV file."""
    try:
        df = pd.read_csv(file_path)
        logging.info('Data loaded from %s', file_path)
        return df
    except pd.errors.ParserError as e:
        logging.error('Failed to parse the CSV file: %s', e)
        raise
    except Exception as e:
        logging.error('Unexpected error occurred while loading the data: %s', e)
        raise

def evaluate_model(clf, X_test: np.ndarray, y_test: np.ndarray) -> dict:
    """Evaluate the model and return the evaluation metrics."""
    try:
        y_pred = clf.predict(X_test)
        y_pred_proba = clf.predict_proba(X_test)[:, 1]

        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_pred_proba)

        metrics_dict = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'auc': auc
        }
        logging.info('Model evaluation metrics calculated')
        return metrics_dict
    except Exception as e:
        logging.error('Error during model evaluation: %s', e)
        raise

def save_metrics(metrics: dict, file_path: str) -> None:
    """Save the evaluation metrics to a JSON file."""
    try:
        with open(file_path, 'w') as file:
            json.dump(metrics, file, indent=4)
        logging.info('Metrics saved to %s', file_path)
    except Exception as e:
        logging.error('Error occurred while saving the metrics: %s', e)
        raise

def save_model_info(run_id: str, model_path: str, file_path: str) -> None:
    """Save the model run ID and path to a JSON file."""
    try:
        model_info = {'run_id': run_id, 'model_path': model_path}
        with open(file_path, 'w') as file:
            json.dump(model_info, file, indent=4)
        logging.debug('Model info saved to %s', file_path)
    except Exception as e:
        logging.error('Error occurred while saving the model info: %s', e)
        raise

import shutil
import os

def main():
    # Ensure local directory for reports exists
    os.makedirs('reports', exist_ok=True)
    
    # Initialize DagsHub/MLflow connection
    # Note: Ensure DAGSHUB_USER and DAGSHUB_TOKEN are set in your environment
    # dagshub.init(repo_owner="student-ChestaVashishtha", 
    #              repo_name="Castpone_Project_Mlops", 
    #              mlflow=True)
    
    mlflow.set_experiment("my-dvc-pipeline")
    
    with mlflow.start_run() as run:
        try:
            # 1. Load your local model and test data
            clf = load_model('./models/model.pkl')
            test_data = load_data('./data/processed/test_bow.csv')
            
            X_test = test_data.iloc[:, :-1].values
            y_test = test_data.iloc[:, -1].values

            # 2. Evaluate and save metrics locally
            metrics = evaluate_model(clf, X_test, y_test)
            save_metrics(metrics, 'reports/metrics.json')
            
            # 3. Log metrics & parameters to MLflow
            for metric_name, metric_value in metrics.items():
                mlflow.log_metric(metric_name, metric_value)
            
            if hasattr(clf, 'get_params'):
                mlflow.log_params(clf.get_params())

            # --- THE FIX FOR THE MISSING MODEL FOLDER ---
            # 4. Save the model locally in MLflow format first
            temp_model_path = "temp_mlflow_model"
            if os.path.exists(temp_model_path):
                shutil.rmtree(temp_model_path)
            
            # This command creates the 'MLmodel' file that the Registry needs
            mlflow.sklearn.save_model(sk_model=clf, path=temp_model_path)

            # 5. Force upload the entire folder to DagsHub
            # This will create the "model" folder you see in the DagsHub UI
            mlflow.log_artifacts(temp_model_path, artifact_path="model")
            
            # Clean up the local temporary folder
            shutil.rmtree(temp_model_path)

            # 6. Save registry info for your register_model.py script
            # Path is "model" because that is the folder containing MLmodel
            save_model_info(run.info.run_id, "model", 'reports/experiment_info.json')
            
            # Log the JSON files as artifacts
            mlflow.log_artifact('reports/metrics.json')
            mlflow.log_artifact('reports/experiment_info.json')

            print(f"✅ Success! Model folder logged to run: {run.info.run_id}")

        except Exception as e:
            logging.error('Failed to complete the process: %s', e)
            print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()