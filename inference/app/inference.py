import hashlib
import os
from pathlib import Path

import mlflow
import mlflow.sklearn
import numpy as np
from mlflow import MlflowClient


MLFLOW_TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI",
    "http://mlflow.mlflow.svc.cluster.local:5000",
)

MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "iris-logistic-regression",
)

MODEL_ALIAS = os.getenv(
    "MODEL_ALIAS",
    "production",
)


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


def load_verified_model():
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

    client = MlflowClient()

    model_version = client.get_model_version_by_alias(
        MODEL_NAME,
        MODEL_ALIAS,
    )

    expected_sha256 = model_version.tags.get("artifact_sha256")

    if not expected_sha256:
        raise RuntimeError(
            "Production model does not contain artifact_sha256 metadata."
        )

    downloaded_model = mlflow.artifacts.download_artifacts(
        artifact_uri=model_version.source,
    )

    actual_sha256 = sha256_path(Path(downloaded_model))

    if actual_sha256 != expected_sha256:
        raise RuntimeError(
            "Model artifact checksum validation failed."
        )

    print(
        f"Verified model {MODEL_NAME} "
        f"version {model_version.version} "
        f"with SHA256 {actual_sha256}"
    )

    return mlflow.sklearn.load_model(downloaded_model)


model = load_verified_model()


def predict_iris(features: list[float]) -> dict:
    if len(features) != 4:
        raise ValueError("Exactly 4 features are required")

    data = np.array([features], dtype=float)

    prediction = model.predict(data)[0]
    probabilities = model.predict_proba(data)[0]

    return {
        "predicted_class": int(prediction),
        "probabilities": [
            round(float(probability), 6)
            for probability in probabilities
        ],
    }
