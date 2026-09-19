import argparse
from pathlib import Path

import pandas as pd
from evidently import Report
from evidently.metrics import ValueDrift
from evidently.presets import DataDriftPreset


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evidently data and prediction drift monitoring."
    )
    parser.add_argument("--reference", required=True)
    parser.add_argument("--current", required=True)
    parser.add_argument(
        "--output",
        default="monitoring/evidently/drift-report.html",
    )
    args = parser.parse_args()

    reference = pd.read_csv(args.reference)
    current = pd.read_csv(args.current)

    if "prediction" not in reference.columns:
        raise ValueError("Reference dataset must contain 'prediction'.")

    if "prediction" not in current.columns:
        raise ValueError("Current dataset must contain 'prediction'.")

    report = Report(
        [
            DataDriftPreset(
                drift_share=0.5,
            ),
            ValueDrift(
                column="prediction",
            ),
        ]
    )

    result = report.run(current, reference)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    result.save_html(str(output))

    print(f"Drift report saved to: {output}")


if __name__ == "__main__":
    main()
