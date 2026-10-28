"""Reference-based benchmark scoring and conservative live scoring."""
import math
import os
import re
import json
from pathlib import Path
import pandas as pd
from deepeval.test_case import LLMTestCase
try:
    from deepeval.test_case import SingleTurnParams as Params
except ImportError:
    from deepeval.test_case import LLMTestCaseParams as Params
from deepeval.metrics import GEval
from deepeval.models import OpenAIModel
from routing import WEIGHTS, THRESHOLDS, route_scores


def make_metrics(include_recall=True):
    judge = OpenAIModel(
        model=os.getenv("EVAL_MODEL", "gpt-4o"),
        api_key=os.environ["OPENAI_API_KEY"],
        base_url=os.getenv("OPENAI_API_BASE") or os.getenv("OPENAI_BASE_URL") or None,
    )
    eval_model = judge
    # Faithfulness
    # Checks whether the generated answer is factually supported by
    # the information retrieved from the knowledge base.
    faithfulness_metric = GEval(
        name="Faithfulness",

        # Defines what the evaluator should judge.
        criteria=(
            "Determine whether the actual output is factually supported by "
            "the provided retrieval context."
        ),

        # Step-by-step instructions given to the evaluator.
        evaluation_steps=[
            # First, identify the individual factual claims made in the answer.
            "Break the actual output into individual factual claims.",

            # Check each claim against the retrieved context.
            "Check whether each claim is supported by the retrieval context.",

            # Lower the score if the answer contains unsupported or conflicting claims.
            "Penalize claims that are unsupported or contradicted by the retrieval context.",

            # Differences in wording should not affect the score if the meaning is supported.
            "Do not penalize differences in wording when the meaning is supported by the context.",

            # Give a high score when the important claims are supported.
            "Give a higher score when all important claims are supported by the context."
        ],

        # Specifies which parts of the test case are used for evaluation.
        evaluation_params=[
            Params.ACTUAL_OUTPUT,
            Params.RETRIEVAL_CONTEXT
        ],

        # Minimum score required for the test case to pass.
        threshold=0.85,

        # LLM used to perform the evaluation.
        model=eval_model
    )


    # Contextual Recall
    # Checks whether the retrieved context contains the information
    # needed to produce the expected answer.
    recall_metric = GEval(
        name="Contextual Recall",

        # Defines what the evaluator should judge.
        criteria=(
            "Determine whether the retrieval context contains the information "
            "needed to support the expected output."
        ),

        # Step-by-step instructions given to the evaluator.
        evaluation_steps=[
            # Identify the important claims that the expected answer should contain.
            "Break the expected output into its important factual claims.",

            # Check whether those claims can be found or supported by the retrieved context.
            "Check whether each important claim is present or supported by the retrieval context.",

            # Lower the score when important information is missing from retrieval.
            "Penalize the retrieval context when important information required for the expected output is missing.",

            # Wording differences should not affect the evaluation.
            "Do not penalize differences in wording or presentation.",

            # Give a high score when retrieval contains most or all required information.
            "Give a higher score when the retrieval context contains most or all information needed to produce the expected output."
        ],

        # Recall requires the expected answer and retrieved context.
        evaluation_params=[
            Params.EXPECTED_OUTPUT,
            Params.RETRIEVAL_CONTEXT
        ],

        # Minimum score required for the test case to pass.
        threshold=0.80,

        # LLM used to perform the evaluation.
        model=eval_model
    )


    # Contextual Precision
    # Checks whether the retrieved context is relevant to the user's question
    # and whether relevant information is prioritized over irrelevant information.
    precision_metric = GEval(
        name="Contextual Precision",

        # Defines what the evaluator should judge.
        criteria=(
            "Determine whether the retrieved context is relevant to answering "
            "the input question, with relevant information prioritized over irrelevant information."
        ),

        # Step-by-step instructions given to the evaluator.
        evaluation_steps=[
            # Identify which parts of the retrieved context are useful for the question.
            "Identify the information in the retrieval context that is relevant to the input question.",

            # Check whether unnecessary or unrelated information was retrieved.
            "Check whether the retrieval context contains unnecessary or unrelated information.",

            # Lower the score when a large portion of the retrieved context is irrelevant.
            "Penalize retrievals that contain a large amount of irrelevant information.",

            # Give more credit when useful information appears prominently.
            "Give more credit when relevant information is prioritized.",

            # Give a high score when most retrieved information is useful.
            "Give a higher score when most of the retrieved context is useful for answering the question."
        ],

        # Precision evaluates the question against the retrieved context.
        evaluation_params=[
            Params.INPUT,
            Params.RETRIEVAL_CONTEXT
        ],

        # Minimum score required for the test case to pass.
        threshold=0.75,

        # LLM used to perform the evaluation.
        model=eval_model
    )


    # Answer Relevancy
    # Checks whether the generated answer directly addresses the user's question
    # without including unnecessary or unrelated information.
    answer_relevancy_metric = GEval(
        name="Answer Relevancy",

        # Defines what the evaluator should judge.
        criteria=(
            "Determine whether the actual output directly addresses the input "
            "question and provides an appropriate response without unnecessary information."
        ),

        # Step-by-step instructions given to the evaluator.
        evaluation_steps=[
            # Check whether the answer directly responds to the question.
            "Check whether the actual output directly answers the input question.",

            # Check whether the information provided is relevant to the question.
            "Check whether the response contains information relevant to the question.",

            # Lower the score for unrelated or unnecessary information.
            "Penalize unnecessary, unrelated, or off-topic information.",

            # A short answer should not be penalized if it answers the question sufficiently.
            "Do not penalize concise answers when they adequately address the question.",

            # Give a high score when the answer is focused and directly relevant.
            "Give a higher score when the response is focused and directly relevant to the question."
        ],

        # Answer relevancy evaluates the question against the generated answer.
        evaluation_params=[
            Params.INPUT,
            Params.ACTUAL_OUTPUT
        ],

        # Minimum score required for the test case to pass.
        threshold=0.75,

        # LLM used to perform the evaluation.
        model=eval_model
    )


    # Store all evaluation metrics in a single list.
    # This list can then be passed to DeepEval's evaluation function.
    metrics = [
        faithfulness_metric,
        recall_metric,
        precision_metric,
        answer_relevancy_metric
    ]
    return [m for m in metrics if include_recall or m.name != "Contextual Recall"]


def load_dataset(path):
    path = str(path)
    df = pd.read_excel(path) if path.lower().endswith(".xlsx") else pd.read_csv(path)
    df.columns = df.columns.str.strip()
    required = ["question", "expected_answer", "relevant_context"]
    missing = set(required) - set(df.columns)
    if missing:
        raise ValueError(f"{path}: missing columns {sorted(missing)}")
    if df.empty or df[required].isna().any().any():
        raise ValueError(f"{path}: dataset is empty or has missing reference fields")
    if any(not str(v).strip() for v in df[required].to_numpy().flat):
        raise ValueError(f"{path}: reference fields must not be blank")
    return df


def test_case_generator(df, vectorstore, k=3, temperature=0.0,
                        top_p=1.0, max_tokens=512, model_name="gpt-4o-mini"):
    from rag_utils import rag
    cases = []
    for _, row in df.iterrows():
        answer, chunks = rag(
            row["question"], k=k, temperature=temperature, top_p=top_p,
            max_tokens=max_tokens, model_name=model_name, vectorstore=vectorstore,
        )
        cases.append(LLMTestCase(
            input=row["question"], actual_output=answer,
            expected_output=row["expected_answer"], retrieval_context=chunks,
            context=[c.strip() for c in row["relevant_context"].split("<>") if c.strip()],
        ))
    return cases


def create_evaluation_df(test_cases, results):
    if len(test_cases) != len(results.test_results):
        raise ValueError("Evaluation result count does not match test case count")
    rows = []
    remaining_results = list(results.test_results)
    for case in test_cases:
        matched = next((i for i, item in enumerate(remaining_results)
                        if getattr(item, 'input', None) == case.input
                        and getattr(item, 'actual_output', None) == case.actual_output), None)
        if matched is None:
            # Minimal offline fixtures have no identity fields. Production results must match.
            if all(not hasattr(item, 'input') for item in remaining_results):
                matched = 0
            else:
                raise ValueError('Cannot match evaluation result to its question and answer')
        result = remaining_results.pop(matched)
        scores = {name: None for name in WEIGHTS}
        reasons = {}
        for metric in result.metrics_data or []:
            name = re.sub(r"\s*\[GEval\]", "", metric.name).strip()
            if name in scores:
                scores[name] = None if getattr(metric, "error", None) else metric.score
                reasons[name] = getattr(metric, "error", None) or metric.reason
        decision = route_scores(scores)
        rows.append({"Question": case.input, "Answer": case.actual_output,
                     "Expected Answer": case.expected_output,
                     "Retrieved Context": case.retrieval_context,
                     **{f"{n} Score": s for n, s in scores.items()},
                     "Composite Score": decision["composite_score"],
                     "Type": decision["route"], "Routing Reason": decision["reason"],
                     "Judge Reasons": reasons})
    return pd.DataFrame(rows)


def summarize_results(frame):
    rows = []
    for name, threshold in THRESHOLDS.items():
        values = frame[f"{name} Score"]
        mean = values.mean()
        rows.append({"Metric": name, "Observed": mean, "Threshold": threshold,
                     "Pass": bool(values.notna().all() and mean >= threshold)})
    coverage = frame["Type"].eq("AUTO ANSWER").mean()
    rows.append({"Metric": "Queries Confidently Answered", "Observed": coverage,
                 "Threshold": 0.50, "Pass": bool(coverage >= 0.50)})
    return pd.DataFrame(rows)


def score_live(query, answer, chunks, reference_catalog=None):
    """Use an approved independent reference for exact catalog matches only.

    References are judge-only and are never supplied to the answer generator.
    Novel questions lack ground truth, so their required composite remains null.
    """
    if reference_catalog is None:
        catalog_path = Path(__file__).parent / "reference_catalog.json"
        reference_catalog = json.loads(catalog_path.read_text()) if catalog_path.exists() else []
    normalized = " ".join(query.split()).casefold()
    reference = next((row for row in reference_catalog
                      if " ".join(row["question"].split()).casefold() == normalized), None)
    scores = {name: None for name in WEIGHTS}
    reasons = {} if reference else {"Contextual Recall": "No approved independent reference answer for this live query."}
    case = LLMTestCase(input=query, actual_output=answer, retrieval_context=chunks,
                       expected_output=reference["expected_answer"] if reference else None)
    try:
        for metric in make_metrics(include_recall=reference is not None):
            try:
                metric.measure(case)
                value = metric.score
                if isinstance(value, (int, float)) and math.isfinite(value) and -1e-12 <= value <= 1 + 1e-12:
                    scores[metric.name] = min(1.0, max(0.0, value))
                reasons[metric.name] = metric.reason
            except Exception:
                reasons[metric.name] = "Judge scoring failed; manual lookup required."
    except Exception:
        reasons["Judge"] = "Judge initialization failed; manual lookup required."
    return {"scores": scores, "judge_reasons": reasons,
            "reference_available": reference is not None,
            "scoring_scope": "Approved reference question" if reference else "Novel question: reference unavailable",
            **route_scores(scores)}
