import io
import time

from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image
from prometheus_client import Counter, Histogram, make_asgi_app

from app.inference import predict_image


app = FastAPI(title="ML Inference API")


REQUEST_COUNT = Counter(
    "inference_requests_total",
    "Total number of inference requests",
    ["endpoint", "method", "status"],
)

REQUEST_LATENCY = Histogram(
    "inference_request_latency_seconds",
    "Inference request latency in seconds",
    ["endpoint"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    start_time = time.perf_counter()

    try:
        if not file.content_type or not file.content_type.startswith("image/"):
            REQUEST_COUNT.labels("/predict", "POST", "400").inc()
            raise HTTPException(
                status_code=400,
                detail="File must be an image",
            )

        contents = await file.read()

        try:
            image = Image.open(io.BytesIO(contents)).convert("RGB")
        except Exception:
            REQUEST_COUNT.labels("/predict", "POST", "400").inc()
            raise HTTPException(
                status_code=400,
                detail="Invalid image file",
            )

        result = predict_image(image)

        REQUEST_COUNT.labels("/predict", "POST", "200").inc()

        return {"predictions": result}

    except HTTPException:
        raise

    except Exception:
        REQUEST_COUNT.labels("/predict", "POST", "500").inc()
        raise HTTPException(
            status_code=500,
            detail="Internal inference error",
        )

    finally:
        REQUEST_LATENCY.labels("/predict").observe(
            time.perf_counter() - start_time
        )


metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
