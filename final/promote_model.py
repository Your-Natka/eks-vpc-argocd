import argparse
import json
import logging
import os
from datetime import datetime, timezone

import mlflow
from mlflow import MlflowClient
from mlflow.exceptions import MlflowException


MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "iris-logistic-regression",
)

MLFLOW_TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI",
    "http://localhost:5000",
)


logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)

audit_logger = logging.getLogger("model_registry_audit")


def audit_event(
    event: str,
    *,
    version: str | None = None,
    previous_version: str | None = None,
    actor: str = "manual",
    status: str = "success",
    reason: str | None = None,
) -> None:
    payload = {
        "event": event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model_name": MODEL_NAME,
        "version": version,
        "previous_version": previous_version,
        "actor": actor,
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


def promote(version: str) -> None:
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    client = MlflowClient()

    try:
        target = client.get_model_version(
            name=MODEL_NAME,
            version=version,
        )

        old_production = None

        try:
            old_production = client.get_model_version_by_alias(
                MODEL_NAME,
                "production",
            )
        except MlflowException:
            pass

        if old_production and old_production.version == version:
            audit_event(
                "model_promotion",
                version=version,
                previous_version=version,
                reason="production alias already points to requested version",
            )
            print(
                f"Production already points to version {version}."
            )
            return

        if old_production:
            client.set_model_version_tag(
                MODEL_NAME,
                old_production.version,
                "lifecycle_state",
                "archived",
            )

            client.set_model_version_tag(
                MODEL_NAME,
                old_production.version,
                "archived_at",
                datetime.now(timezone.utc).isoformat(),
            )

        client.set_registered_model_alias(
            MODEL_NAME,
            "production",
            target.version,
        )

        client.set_model_version_tag(
            MODEL_NAME,
            target.version,
            "lifecycle_state",
            "production",
        )

        audit_event(
            "model_promotion",
            version=target.version,
            previous_version=(
                old_production.version
                if old_production
                else None
            ),
            reason="staging_to_production",
        )

        print(
            f"Promoted {MODEL_NAME} version "
            f"{target.version} to production."
        )

    except Exception as exc:
        audit_event(
            "model_promotion",
            version=version,
            status="failed",
            reason=str(exc),
        )
        raise


def delete_version(version: str) -> None:
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    client = MlflowClient()

    try:
        client.delete_model_version(
            name=MODEL_NAME,
            version=version,
        )

        audit_event(
            "model_version_deleted",
            version=version,
            reason="manual deletion",
        )

        print(
            f"Deleted {MODEL_NAME} version {version}."
        )

    except Exception as exc:
        audit_event(
            "model_version_deleted",
            version=version,
            status="failed",
            reason=str(exc),
        )
        raise


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Promote or delete MLflow model versions."
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    promote_parser = subparsers.add_parser(
        "promote",
        help="Promote a model version to production.",
    )
    promote_parser.add_argument(
        "--version",
        required=True,
    )

    delete_parser = subparsers.add_parser(
        "delete",
        help="Delete a model version.",
    )
    delete_parser.add_argument(
        "--version",
        required=True,
    )

    args = parser.parse_args()

    if args.command == "promote":
        promote(args.version)

    elif args.command == "delete":
        delete_version(args.version)


if __name__ == "__main__":
    main()
