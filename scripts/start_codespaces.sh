#!/usr/bin/env bash
set -euo pipefail
task_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$task_root"
if ! command -v docker >/dev/null 2>&1; then
  echo 'Docker is unavailable. In Codespaces, rebuild the container using the supplied .devcontainer configuration.' >&2
  exit 1
fi
if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo 'OPENAI_API_KEY is missing. Add it to Codespaces secrets for this repository, then stop/restart the Codespace.' >&2
  exit 1
fi
if [[ ! -s backend_files/faiss_index/index.faiss || ! -s backend_files/faiss_index/index.pkl ]]; then
  echo 'The trusted FAISS index is missing. Extract the complete deployment ZIP, including backend_files/faiss_index.' >&2
  exit 1
fi
docker info >/dev/null
docker compose version
docker compose config --quiet
docker compose up --build --detach --wait --wait-timeout 900
python3 scripts/verify_deployment.py
echo 'Open forwarded port 8501 in the Codespaces Ports panel. Keep both ports Private for this internal POC.'
echo 'Optional real generation check: python3 scripts/verify_deployment.py --include-generation'
echo 'Stop services when finished: docker compose down'
