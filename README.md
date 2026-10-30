# AuroraStay

Internal hotel-policy RAG proof of concept with a Flask API, Streamlit UI, trusted
FAISS policy index, and Codespaces deployment configuration.

## Deploy in Codespaces

1. Read [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md).
2. Add OPENAI_API_KEY and OPENAI_API_BASE as Codespaces secrets for this repository.
3. Create a Codespace using the included .devcontainer configuration.
4. Run bash scripts/start_codespaces.sh.
5. Run python3 scripts/verify_deployment.py --include-generation.
6. Open forwarded port 8501. Keep the ports private for this internal POC.

The API key is never committed. Paid model calls are used for answers and scoring.
The two trusted FAISS index files are included so the deployment does not require
reprocessing the original PDFs. Only load the index supplied by this project.

## Validation status

The final ten-query held-out benchmark passed all five targets: faithfulness
0.987, recall 0.902, precision 0.784, relevancy 0.894, and 9/10 auto-answer routes.
This small benchmark is not a claim of 90% open-ended live coverage.
Approved reference questions receive four-metric scoring; novel questions still
require manual lookup when an independent recall reference is absent.

Local UI, HTTP, generation and scoring checks passed. The user subsequently
supplied passing Codespaces health, retrieval and answer verification (95.77%
composite), plus browser scores (95.56%). See [COMPLETION_STATUS.md](COMPLETION_STATUS.md)
for actual URLs, evidence provenance and remaining review. Staff sign-off and
browser source-expander confirmation remain pending; see [LIVE_VALIDATION.md](LIVE_VALIDATION.md).
