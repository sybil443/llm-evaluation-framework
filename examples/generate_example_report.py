from pathlib import Path

from evaluation.comparison_report import render_report
from evaluation.pipeline import evaluate
from examples.demo_data import make_demo_request


def main():
    request = make_demo_request()
    result = evaluate(request)
    report = render_report(result)

    output_path = Path(__file__).with_name("example_report.md")
    output_path.write_text(report, encoding="utf-8")

    print(f"Report saved to: {output_path.resolve()}")


if __name__ == "__main__":
    main()