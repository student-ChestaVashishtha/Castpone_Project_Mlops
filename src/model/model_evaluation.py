import numpy as np
import pandas as pd
import pickle
import json
import os

import mlflow
import mlflow.sklearn
import dagshub

from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
from mlflow.tracking import MlflowClient
from src.logger import logging


# ============================
# DAGsHub + MLflow Setup
# ============================
dagshub.init(
    repo_owner="Student-ChestaVashishtha",
    repo_name="Castpone_Project_Mlops",
    mlflow=True
)

EXPERIMENT_NAME = "my-dvc-pipeline"

client = MlflowClient()
experiment = client.get_experiment_by_name(EXPERIMENT_NAME)

if experiment is None:
    client.create_experiment(EXPERIMENT_NAME)

mlflow.set_experiment(EXPERIMENT_NAME)

os.makedirs("reports", exist_ok=True)


# ============================
# Utility Functions
# ============================
def load_model(file_path: str):
    try:
        with open(file_path, "rb") as file:
            model = pickle.load(file)
        logging.info("Model loaded from %s", file_path)
        return model
    except Exception as e:
        logging.error("Error loading model: %s", e)
        raise


def load_data(file_path: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(file_path)
        logging.info("Data loaded from %s", file_path)
        return df
    except Exception as e:
        logging.error("Error loading data: %s", e)
        raise


def evaluate_model(clf, X_test, y_test) -> dict:
    try:
        y_pred = clf.predict(X_test)
        y_pred_proba = clf.predict_proba(X_test)[:, 1]

        metrics = {
            "accuracy": accuracy_score(y_test, y_pred),
            "precision": precision_score(y_test, y_pred),
            "recall": recall_score(y_test, y_pred),
            "auc": roc_auc_score(y_test, y_pred_proba),
        }

        logging.info("Model evaluation completed")
        return metrics
    except Exception as e:
        logging.error("Error during evaluation: %s", e)
        raise


def save_json(data: dict, file_path: str):
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)


# ============================
# Main
# ============================
def main():
    try:
        with mlflow.start_run(run_name="model_evaluation") as run:

            clf = load_model("models/model.pkl")
            test_data = load_data("data/processed/test_bow.csv")

            X_test = test_data.iloc[:, :-1].values
            y_test = test_data.iloc[:, -1].values

            metrics = evaluate_model(clf, X_test, y_test)

            # Save & log metrics
            save_json(metrics, "reports/metrics.json")
            mlflow.log_metrics(metrics)

            # Log model params
            if hasattr(clf, "get_params"):
                mlflow.log_params(clf.get_params())

            # Log model (IMPORTANT: artifact_path = "model")
            mlflow.sklearn.log_model(clf, artifact_path="model")

            # Save model info for registration
            model_info = {
                "run_id": run.info.run_id,
                "model_path": "model",
            }
            save_json(model_info, "reports/experiment_info.json")

            # Log artifacts
            mlflow.log_artifact("reports/metrics.json")
            mlflow.log_artifact("reports/experiment_info.json")

            logging.info("Model evaluation and logging completed successfully")

    except Exception as e:
        logging.error("Failed model evaluation pipeline: %s", e)
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
