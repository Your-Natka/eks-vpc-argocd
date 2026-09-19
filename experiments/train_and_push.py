import hashlib
import json
import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
from mlflow import MlflowClient
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

REGISTERED_MODEL_NAME = "iris-logistic-regression"

BEST_MODEL_DIR = Path("best_model")
MODELS_DIR = Path("models")

BEST_MODEL_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)


def get_git_commit_sha() -> str:
    value = os.getenv("CI_COMMIT_SHA")
    if value:
        return value

    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def sha256_path(path: Path) -> str:
    hasher = hashlib.sha256()

    if path.is_file():
        hasher.update(path.name.encode())
        hasher.update(b"\0")
        hasher.update(path.read_bytes())
        return hasher.hexdigest()

    for file_path in sorted(p for p in path.rglob("*") if p.is_file()):
        relative_path = file_path.relative_to(path)

        hasher.update(str(relative_path).encode())
        hasher.update(b"\0")
        hasher.update(file_path.read_bytes())

    return hasher.hexdigest()


def audit_event(
    event: str,
    *,
    run_id: str,
    version: str | None = None,
    status: str = "success",
    reason: str | None = None,
) -> None:
    payload = {
        "event": event,
        "model_name": REGISTERED_MODEL_NAME,
        "run_id": run_id,
        "version": version,
        "status": status,
    }

    if reason:
        payload["reason"] = reason

    audit_logger.info(
        json.dumps(
            payload,
            separators=(",", ":"),
        )
    )


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
    mlflow.set_experiment(REGISTERED_MODEL_NAME)

    client = MlflowClient()

    iris = load_iris()

    dataset_hash = hashlib.sha256(
        iris.data.tobytes() + iris.target.tobytes()
    ).hexdigest()

    git_commit_sha = get_git_commit_sha()

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

            mlflow.set_tags(
                {
                    "git_commit_sha": git_commit_sha,
                    "dataset_sha256": dataset_hash,
                    "registered_model_name": REGISTERED_MODEL_NAME,
                }
            )

            model_path = MODELS_DIR / f"model_{run.info.run_id}.joblib"
            joblib.dump(model, model_path)

            mlflow.sklearn.log_model(
                sk_model=model,
                name="model",
                registered_model_name=REGISTERED_MODEL_NAME,
                input_example=X_train[:1],
            )

            with tempfile.TemporaryDirectory() as tmp_dir:
                downloaded_model = mlflow.artifacts.download_artifacts(
                    run_id=run.info.run_id,
                    artifact_path="model",
                    dst_path=tmp_dir,
                )

                artifact_sha256 = sha256_path(Path(downloaded_model))

            mlflow.set_tag("artifact_sha256", artifact_sha256)

            push_metrics(
                run.info.run_id,
                accuracy,
                loss,
            )

            versions = [
                version
                for version in client.search_model_versions(
                    f"name='{REGISTERED_MODEL_NAME}'"
                )
                if version.run_id == run.info.run_id
            ]

            if versions:
                model_version = max(
                    versions,
                    key=lambda version: int(version.version),
                )

                client.set_model_version_tag(
                    REGISTERED_MODEL_NAME,
                    model_version.version,
                    "artifact_sha256",
                    artifact_sha256,
                )

                client.set_model_version_tag(
                    REGISTERED_MODEL_NAME,
                    model_version.version,
                    "git_commit_sha",
                    git_commit_sha,
                )

                client.set_model_version_tag(
                    REGISTERED_MODEL_NAME,
                    model_version.version,
                    "dataset_sha256",
                    dataset_hash,
                )

                audit_event(
                    "model_registered",
                    run_id=run.info.run_id,
                    version=model_version.version,
                )

                client.set_registered_model_alias(
                    REGISTERED_MODEL_NAME,
                    "staging",
                    model_version.version,
                )

                audit_event(
                    "model_staged",
                    run_id=run.info.run_id,
                    version=model_version.version,
                )

                print(
                    f"Registered version {model_version.version} "
                    f"and assigned alias 'staging'."
                )

            print(
                f"Run {run.info.run_id}: "
                f"C={params['C']}, "
                f"max_iter={params['max_iter']}, "
                f"accuracy={accuracy:.4f}, "
                f"loss={loss:.4f}, "
                f"artifact_sha256={artifact_sha256}"
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
