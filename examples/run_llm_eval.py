"""Run with python -m examples.run_llm_eval."""
import argparse
from pathlib import Path

from evaluation.artifacts import save_run
from evaluation.comparison_report import render_report
from evaluation.contracts import EvaluationRequest
from evaluation.pipeline import evaluate
from examples.ab_demo import run_ab_demo
from examples.demo_data import make_demo_request
from examples.failure_analysis_demo import run_failure_analysis_demo
from examples.judge_workflow import run_judge_demo
from examples.retrieval_eval_demo import run_retrieval_demo
from examples.significance_demo import run_significance_demo


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Request JSON; otherwise use authored fixtures.")
    parser.add_argument("--output", type=Path, default=Path("runs"))
    args = parser.parse_args(argv)
    request = (EvaluationRequest.model_validate_json(args.input.read_text(encoding="utf-8"))
               if args.input else make_demo_request())
    result = evaluate(request)
    # Independent workflow demos are deliberately separate from model-comparison scores.
    supplements = {"judge_workflow": run_judge_demo(), "independent_ab": run_ab_demo(),
                  "retrieval_evaluation": run_retrieval_demo(),
                  "failure_analysis": run_failure_analysis_demo(),
                  "significance_review": run_significance_demo()}
    directory = save_run(request, result, render_report(result), args.output, supplements)
    print(f"{result['decision']['status']}: {directory / 'report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())