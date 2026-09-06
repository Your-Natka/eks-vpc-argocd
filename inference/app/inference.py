import hashlib
import os
from pathlib import Path

import torch
from PIL import Image
from torchvision.models import MobileNet_V2_Weights


MODEL_PATH = Path(__file__).resolve().parent.parent / "model" / "model.pt"

EXPECTED_MODEL_SHA256 = os.getenv(
    "MODEL_SHA256",
    "446577ee7d7fb0eced219e8b4c4e3d130ba93206258a9041fa8e9e2ddc642abc",
)


def calculate_sha256(path: Path) -> str:
    sha256 = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


actual_sha256 = calculate_sha256(MODEL_PATH)

if actual_sha256 != EXPECTED_MODEL_SHA256:
    raise RuntimeError("Model checksum verification failed")


weights = MobileNet_V2_Weights.DEFAULT
preprocess = weights.transforms()

model = torch.jit.load(MODEL_PATH, map_location="cpu")
model.eval()


def predict_image(image: Image.Image) -> list[dict]:
    image = image.convert("RGB")

    tensor = preprocess(image).unsqueeze(0)

    with torch.no_grad():
        output = model(tensor)

    probabilities = torch.nn.functional.softmax(output[0], dim=0)
    top3 = torch.topk(probabilities, 3)

    predictions = []

    for score, class_id in zip(top3.values, top3.indices):
        predictions.append(
            {
                "class_id": class_id.item(),
                "confidence": round(score.item(), 4),
            }
        )

    return predictions
