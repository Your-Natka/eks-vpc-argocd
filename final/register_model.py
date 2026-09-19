import os

import mlflow


MLFLOW_TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI",
    "http://localhost:5000",
)

RUN_ID = os.getenv("RUN_ID")

MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "iris-logistic-regression",
)

if not RUN_ID:
    raise SystemExit(
        "RUN_ID is required. Example: "
        "RUN_ID=<run_id> python3 final/register_model.py"
    )


mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

model_uri = f"runs:/{RUN_ID}/model"

result = mlflow.register_model(
    model_uri=model_uri,
    name=MODEL_NAME,
)

print(f"Registered model: {result.name}")
print(f"Version: {result.version}")
print(f"Run ID: {RUN_ID}")
