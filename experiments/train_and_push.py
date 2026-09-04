import os
import shutil
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, log_loss
from sklearn.model_selection import train_test_split


MLFLOW_TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI",
    "http://localhost:5000",
)

PUSHGATEWAY_URL = os.getenv(
    "PUSHGATEWAY_URL",
    "http://localhost:9091",
)

BEST_MODEL_DIR = Path("best_model")
MODELS_DIR = Path("models")

BEST_MODEL_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)


def push_metrics(run_id: str, accuracy: float, loss: float) -> None:
    registry = CollectorRegistry()

    accuracy_gauge = Gauge(
        "mlflow_accuracy",
        "Model accuracy logged from MLflow experiment",
        registry=registry,
    )

    loss_gauge = Gauge(
        "mlflow_loss",
        "Model log loss logged from MLflow experiment",
        registry=registry,
    )

    accuracy_gauge.set(accuracy)
    loss_gauge.set(loss)

    push_to_gateway(
        PUSHGATEWAY_URL,
        job="mlflow_experiments",
        grouping_key={"run_id": run_id},
        registry=registry,
    )


def main() -> None:
    print(f"MLflow tracking URI: {MLFLOW_TRACKING_URI}")
    print(f"PushGateway URL: {PUSHGATEWAY_URL}")

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment("iris-logistic-regression")

    iris = load_iris()

    X_train, X_test, y_train, y_test = train_test_split(
        iris.data,
        iris.target,
        test_size=0.2,
        random_state=42,
        stratify=iris.target,
    )

    experiments = [
        {"C": 0.1, "max_iter": 100},
        {"C": 1.0, "max_iter": 100},
        {"C": 10.0, "max_iter": 100},
        {"C": 1.0, "max_iter": 200},
    ]

    best_accuracy = -1.0
    best_model_path = None

    for params in experiments:
        with mlflow.start_run() as run:
            model = LogisticRegression(
                C=params["C"],
                max_iter=params["max_iter"],
                random_state=42,
            )

            model.fit(X_train, y_train)

            predictions = model.predict(X_test)
            probabilities = model.predict_proba(X_test)

            accuracy = accuracy_score(y_test, predictions)
            loss = log_loss(y_test, probabilities)

            mlflow.log_params(params)
            mlflow.log_metric("accuracy", accuracy)
            mlflow.log_metric("loss", loss)

            model_path = MODELS_DIR / f"model_{run.info.run_id}.joblib"
            joblib.dump(model, model_path)

            mlflow.log_artifact(str(model_path))

            push_metrics(
                run.info.run_id,
                accuracy,
                loss,
            )

            print(
                f"Run {run.info.run_id}: "
                f"C={params['C']}, "
                f"max_iter={params['max_iter']}, "
                f"accuracy={accuracy:.4f}, "
                f"loss={loss:.4f}"
            )

            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_model_path = model_path

    if best_model_path is None:
        raise RuntimeError("No successful MLflow runs found.")

    best_model_destination = BEST_MODEL_DIR / "best_model.joblib"

    shutil.copy2(
        best_model_path,
        best_model_destination,
    )

    print()
    print(f"Best accuracy: {best_accuracy:.4f}")
    print(f"Best model: {best_model_destination}")


if __name__ == "__main__":
    main()
