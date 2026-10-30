# Current completion status — 2026-10-29

Repository upload is complete: https://github.com/prakashvakacharla/AuroraStay.
User-supplied Codespaces verification passes backend health (189 vectors),
frontend health, retrieval (3 chunks), and answer generation (HTTP 200).
The deployed approved-reference answer has composite **95.77% / AUTO ANSWER**.
A separate browser run passed all four quality thresholds at **95.56%**.
These are user-supplied remote observations, not an independent remote rerun.

Frontend: https://shady-sorcery-967q4vq4xwgj3p9x5-8501.app.github.dev/
Backend: https://shady-sorcery-967q4vq4xwgj3p9x5-7860.app.github.dev/

The complete answer, three supporting excerpts and judge reasons are archived in
`outputs/codespaces_deployment_verification.json` in the full submission package.
The actual URLs were supplied by the user. Private URLs require authorized access
and a running Codespace. A live availability check is not implied by these links.

All five aggregate benchmark targets pass. Auto-answer coverage is 9/10 test
questions; 7/10 pass every individual metric. Novel questions still require manual
lookup without an independent recall reference. Human review of eight prepared
cases and a larger real-staff batch are rollout recommendations, not additional
notebook marks. Source-expander display confirmation remains outstanding.

The guide below is retained as a reproducible setup procedure. Existing users can
skip repository creation and upload. Do not rebuild or repeat paid evaluations
solely to generate the final report.

---

# AuroraStay: browser-based Codespaces deployment

The following is the original setup procedure; current completion evidence is above.

## Prerequisites you handle

1. A GitHub personal account with permission to create a private repository and use
   Codespaces. Check your included Codespaces usage and budget before starting;
   payment details may be needed if your included usage is exhausted.
2. The funded OpenAI API key already used for this project, with access to
   `gpt-4o-mini` and `gpt-4o`. Keep it in Codespaces secrets, not a source file.
3. Download **AuroraStay_Codespaces_Deployment.zip** from the delivered artifacts.
   It includes the trusted index, source, Compose configuration, dev container,
   startup/check scripts, and the staff-review workflow. It contains no API key.
4. For broader live validation, a hotel policy owner or knowledgeable staff reviewer
   must review the supplied worksheet. That approval cannot be replaced by an AI score.

You do not need Docker Desktop, GitHub CLI, or a personal access token on your Mac
for this browser route. The supplied dev container installs Docker inside Codespaces.

## 1. Create a private repository

Open [GitHub new repository](https://github.com/new). Name it `aurora-stay-qna`
(or another name you prefer), choose **Private**, select **Add a README**, and
create it. Use a new repository so these instructions do not overwrite existing work.

## 2. Add Codespaces secrets

Open [your Codespaces settings](https://github.com/settings/codespaces).
Under **Codespaces secrets**, choose **New secret** and create:

| Name | Value |
| --- | --- |
| `OPENAI_API_KEY` | Your funded API key |
| `OPENAI_API_BASE` | `https://api.openai.com/v1` |

For each secret, grant **Repository access** to the private repository from step 1.
These must be **Codespaces secrets**; GitHub Actions secrets are a different store.
Do not paste the API key into this chat, a commit, the README, or a terminal command.

If you add/change secrets after starting a Codespace, stop and restart it so the
environment receives them. [GitHub secret instructions](https://docs.github.com/en/codespaces/managing-your-codespaces/managing-your-account-specific-secrets-for-github-codespaces)

## 3. Create the Codespace

In your repository, choose **Code → Codespaces → Create codespace**. Use advanced
options to select a **4-core / 8 GB** machine when available; this is recommended
for dependency/image builds. Check which account pays before confirming.
Wait for the browser editor to open.
[GitHub creation instructions](https://docs.github.com/en/codespaces/developing-in-a-codespace/creating-a-codespace-for-a-repository)

## 4. Upload and extract the prepared package

Drag `AuroraStay_Codespaces_Deployment.zip` into the Codespaces Explorer area,
or use its Upload action. Open a terminal at the repository root and run:

```bash
unzip -n AuroraStay_Codespaces_Deployment.zip
```

The ZIP stores files at its root. You should see `compose.yaml`, `backend_files/`,
`frontend_files/`, `scripts/`, and the hidden `.devcontainer/` directory. Do not
upload your full local workspace, `.venv`, `.cache`, `.openai-test.json`, or `config.json`.

Save the deployment files to the repository:

```bash
git add .devcontainer backend_files frontend_files scripts validation compose.yaml DEPLOYMENT_GUIDE.md LIVE_VALIDATION.md .gitignore
git add -f backend_files/faiss_index/index.faiss backend_files/faiss_index/index.pkl
git commit -m "Add AuroraStay deployment and validation workflow"
git push
```

The prepared ZIP includes approved development references used only for judging.
The raw PDF collection, held-out test references, local credentials, staff names,
and pending review worksheet are not required for deployment and are not uploaded
by these commands. The reference catalog and index include policy information;
keep the repository private.

## 5. Rebuild the development container

Open the Command Palette (**Cmd/Ctrl + Shift + P**) and run
**Codespaces: Rebuild Container**. This applies `.devcontainer/devcontainer.json`,
including Docker-in-Docker and forwarding for ports 7860 and 8501.
Wait until the rebuilt editor is ready. It may download substantial dependencies
the first time. If GitHub indicates the current machine is too small, change to
the recommended machine type before rebuilding.

## 6. Build and start the app

In the terminal at the repository root:

```bash
bash scripts/start_codespaces.sh
```

This checks the secret and trusted index, validates Compose, builds both images,
waits for backend/frontend health checks, and records HTTP/retrieval checks in
`outputs/deployment_verification.json`. It does not print the API key.
The first backend image build downloads and caches the embedding model; runtime
uses that cached model in offline mode.

Run the paid end-to-end answer check once:

```bash
python3 scripts/verify_deployment.py --include-generation
```

Success includes `checks_passed: true`, an actual answer/source payload, and a
four-metric composite for an approved reference question. An HTTP 200 alone does
not prove every generated answer is correct.

If a check fails, inspect the services:

```bash
docker compose ps
docker compose logs --tail=100 backend frontend
```

Missing secret: grant repository access to the Codespaces secret and stop/restart
the Codespace. Credit error: check API billing. Model download/build error: inspect
the backend build log and retry after network access is restored. The Mac did not run Docker; subsequent user-supplied Codespaces verification
passed. Use these checks when redeploying.

## 7. Verify the forwarded browser URLs

Open the **Ports** tab. Keep **7860** and **8501** **Private** for this internal POC.
Open port **8501** in your signed-in browser and ask:

> What time can I check in at ASH-CHI Loop, and when do I need to be out?

Select **Answer + Relevant Chunks** and confirm that the answer, quality scores,
route and sources appear. Open port **7860** and verify its health JSON.
Copy both actual forwarded URLs from the Ports panel; do not invent them.

A private forwarded URL requires GitHub authentication. A 401/404 from a separate
unauthenticated notebook/client may be a port-authentication issue, not an app failure.
Do not make a paid, unauthenticated API public merely to bypass that check. If an
assessor explicitly requires public access, agree on an appropriate access method
before changing visibility. [GitHub forwarding instructions](https://docs.github.com/en/codespaces/developing-in-a-codespace/forwarding-ports-in-your-codespace)

The verification script records `forwarded_browser_urls_verified: false` because
it cannot assert that you opened the private URLs. Retain your browser evidence
and share the actual URLs plus `outputs/deployment_verification.json` when complete.
Do not include any credentials. The report can then record real external deployment
evidence instead of only local checks.

## 8. Complete staff validation and stop unused services

Follow `LIVE_VALIDATION.md` for the separate staff-review step. Novel questions
still route to manual lookup until an independent reference is approved.

When finished testing:

```bash
docker compose down
```

Then open [your Codespaces page](https://github.com/codespaces), stop the Codespace,
and delete it when no longer needed. Stopping the app containers does not stop
Codespaces compute, and stopped Codespaces still retain storage.

## What to return after these steps

- Repository URL and actual forwarded frontend/backend URLs.
- `outputs/deployment_verification.json` from the Codespace.
- A note that both private browser URLs and the UI were checked.
- The completed staff worksheet, when a policy owner has reviewed it.

Deployment output and URLs have now been supplied; human sign-off and
source-expander confirmation remain pending. The 90% benchmark coverage is unchanged.
