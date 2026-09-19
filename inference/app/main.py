import json
import logging
import time
from collections import defaultdict, deque

from fastapi import FastAPI, HTTPException, Request
from prometheus_client import Counter, Histogram, make_asgi_app
from pydantic import BaseModel, Field, field_validator

from app.inference import predict_iris


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


RATE_LIMIT_REQUESTS = 30
RATE_LIMIT_WINDOW_SECONDS = 60
_rate_limit_store: dict[str, deque[float]] = defaultdict(deque)


class IrisRequest(BaseModel):
    features: list[float] = Field(..., min_length=4, max_length=4)

    @field_validator("features")
    @classmethod
    def validate_features(cls, value: list[float]) -> list[float]:
        if any(feature < 0 or feature > 10 for feature in value):
            raise ValueError("Each feature must be between 0 and 10")
        return value


def is_rate_limited(client_ip: str) -> bool:
    now = time.monotonic()
    timestamps = _rate_limit_store[client_ip]

    while timestamps and now - timestamps[0] >= RATE_LIMIT_WINDOW_SECONDS:
        timestamps.popleft()

    if len(timestamps) >= RATE_LIMIT_REQUESTS:
        return True

    timestamps.append(now)
    return False


@app.middleware("http")
async def audit_logging(request: Request, call_next):
    start_time = time.perf_counter()
    client_ip = request.client.host if request.client else "unknown"

    response = await call_next(request)

    audit_logger.info(
        json.dumps(
            {
                "event": "http_request",
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "client_ip": client_ip,
                "duration_ms": round(
                    (time.perf_counter() - start_time) * 1000,
                    2,
                ),
            },
            separators=(",", ":"),
        )
    )

    return response


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
def predict(request: Request, payload: IrisRequest):
    start_time = time.perf_counter()
    client_ip = request.client.host if request.client else "unknown"

    try:
        if is_rate_limited(client_ip):
            REQUEST_COUNT.labels("/predict", "POST", "429").inc()
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Try again later.",
            )

        result = predict_iris(payload.features)

        REQUEST_COUNT.labels("/predict", "POST", "200").inc()
        return result

    except HTTPException:
        raise

    except ValueError as exc:
        REQUEST_COUNT.labels("/predict", "POST", "400").inc()
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

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
