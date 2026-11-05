# Kandla Port — Community Cloud deployment bundle

This is a self-contained, public **precomputed demonstration** of the existing date-wise dashboard. The original research app, trained models, masks and results remain unchanged in the parent project. The dashboard's layout, date/scene workflow, scientific charts, layers and map viewer are retained; the data adapter uses only the files in this directory.

## Included real demonstration dates

- **31 May 2026** (`20260531`) — `20260531_063100_24_2504_3B`.
- **3 June 2026** (`20260603`) — `20260603_063613_80_250a_3B`.

Both are validation scenes already analyzed locally with the selected tuned RF-2. Each included RGB/classes/probability/quality/coverage preview is **1024 × 293**, sampled from the real complete scene mosaic. Source geometry and the exact source-sample mapping are included. All counts, areas, probability summaries and validation metrics come from the recorded **full-resolution unique-pixel analysis**, never from counting these lower-resolution previews. See [AVAILABLE_DATES.md](AVAILABLE_DATES.md).

No raw SR/UDM2 scenes, training masks, validation pixel masks, reserved test masks, private tile inventories, Windows paths or credentials are distributed. Ground-truth and error raster layers are intentionally unavailable in this public bundle; aggregate validation metrics remain visible. Downloads are explicitly preview PNGs, original-grid metadata, aggregate CSV/JSON and a self-contained HTML report. Full-resolution GeoTIFFs remain in the local research project.

The selected forest is included at `models/selected_model.joblib`. Its learned estimator serialization is byte-for-byte preserved. Only inert metadata strings containing local paths and private date/tile inventories were replaced with equal-byte-length redactions, keeping pickle framing and all estimator/NumPy bytes unchanged. `models/byte_preservation.json` records the original artifact hash and preserved estimator-prefix hash. The original model was not edited. Public JSON metadata is a deliberately reduced contract, not the original private report. No fitting, retuning or new model selection occurred.

The cloud app displays recorded predictions and does not deserialize the forest on startup. This avoids unnecessary cloud RAM use and makes the demo independent of source imagery. `smoke_test.py --runtime` separately verifies the packaged model can load with its recorded sklearn version and checks the live Streamlit date/download workflow. Joblib files must be trusted; do not replace this asset with arbitrary uploads.

## Local Python 3.12 smoke test

From the **parent project directory**, native Windows PowerShell:

```powershell
py -3.12 -m venv .venv-cloud
if ($LASTEXITCODE -ne 0) { throw "Install Python 3.12 before continuing" }
$Py = ".\.venv-cloud\Scripts\python.exe"
& $Py -m pip install -r .\deployment\requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed" }
& $Py .\deployment\smoke_test.py --runtime
if ($LASTEXITCODE -ne 0) { throw "Deployment runtime smoke test failed" }
& $Py -m streamlit run .\deployment\app.py
```

After publishing this folder as a standalone repository, equivalent Linux commands are:

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python smoke_test.py --runtime
python -m streamlit run app.py
```

The standard-library audit `python smoke_test.py` works without installed numerical packages. It verifies every asset hash, all preview layers/dtypes/ranges/NoData, relative paths, model-state byte preservation, metadata redaction, dates, geometry, areas and validation confusion support. `--runtime` additionally tests actual model deserialization, PNG/HTML/CSV export and Streamlit initial/date/download views. No test ever fits a model.

## GitHub upload — publish ONLY this directory

Create an **empty** GitHub repository named `kandla-port-streamlit-demo` (no generated README or license). Then run from the parent project directory. Replace only the username variable. Do not run `git add .` in the research project's root and do not push its existing history.

```powershell
$GitHubUser = "YOUR_GITHUB_USERNAME"
$Repo = "kandla-port-streamlit-demo"
Set-Location .\deployment

python .\smoke_test.py
if ($LASTEXITCODE -ne 0) { throw "Bundle audit failed" }

git init -b main
git add .
git status --short
git diff --cached --stat
# Only this deployment's allowlisted files should be staged.
git commit -m "Deploy cached date-wise Kandla Port satellite dashboard"
git remote add origin "https://github.com/$GitHubUser/$Repo.git"
git push -u origin main
```

If `python` is not on PATH, use the Python 3.12 environment created above: `& ..\.venv-cloud\Scripts\python.exe .\smoke_test.py`. Authenticate to GitHub using Git Credential Manager/browser sign-in; do not put credentials in remote URLs or source files.

This is a **new independent Git repository inside `deployment/`**. It does not inherit private project history. `.gitignore` is a strict allowlist: extra files, virtual environments, secrets, caches, raw scenes, masks and training artifacts are excluded. The included model is under 10 MB, and every bundled file is below GitHub's ordinary 100 MiB hard limit; Git LFS is unnecessary for this bundle. [GitHub file-size documentation](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github).

For an already initialized deployment repository, use `git add .`, `git commit -m "Update public demo assets"` and `git push`; do not repeat `git remote add origin`.

## Streamlit Community Cloud

1. Sign in at [share.streamlit.io](https://share.streamlit.io/) with the GitHub account that can access the new repository.
2. Select **Create app**, choose `kandla-port-streamlit-demo`, branch **main**, and main file **app.py**.
3. In **Advanced settings**, explicitly choose **Python 3.12**. The bundled `.python-version` documents the local target; the Cloud UI selection controls the actual runtime.
4. Deploy. `requirements.txt` is at the repository root alongside `app.py`; no `packages.txt`, Windows environment variable, source-scene mount, API key or secrets are required.
5. Open the app, select a date and click **Load cached date analysis**. Change layers/opacity/threshold, inspect the charts, then click **Prepare preview downloads & date report**.

This follows the official [deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy) and [dependency/file organization guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization). Runtime requirements are pinned to the existing saved-model environment and support Python 3.12; sklearn is pinned to 1.9.1 to match the estimator. [Official sklearn package](https://pypi.org/project/scikit-learn/1.9.1/).

## Troubleshooting

- **Original Windows/source path errors:** you deployed the research root app instead of this bundle. Publish the contents of `deployment/` as the repository root and choose `app.py`. No `KANDLA_TUNING_RUN` or `KANDLA_SOURCE_DIR` is needed.
- **No dates / missing NPZ or model:** run the smoke test, then `git ls-files data models`. Ensure the allowlisted assets were committed, not just the Python files. Linux paths are case-sensitive.
- **Missing module / incompatible wheel:** confirm Python 3.12 and the exact root `requirements.txt` in Cloud logs. Do not downgrade sklearn to bypass pickle compatibility. Cloud Python-version changes may require deleting/redeploying the app, per the [official Python upgrade guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app/upgrade-python).
- **Model hash/version smoke failure:** restore the audited bundle assets; do not edit/retrain the estimator. The model is not required for precomputed display startup but must pass the runtime smoke test before claiming load compatibility.
- **No ground-truth/error map or GeoTIFF button:** intentional public-data minimization. Only aggregate validation metrics and lower-resolution preview imagery are included. Local full-resolution analysis remains in the original project.
- **RAM / cold start:** only the selected preview is cached; no original scenes are loaded and the forest is not deserialized for display. Downloads are generated in an ephemeral temporary directory and regenerate after restart.
- **Fullscreen blocked:** use zoom/pan or the expandable static preview. Some browser iframe policies restrict fullscreen.
- **Numeric counts differ from visible preview pixels:** expected. Counts/metrics refer to cached full-resolution unique source pixels, not the sampled public preview. The provenance and original source geometry are included in JSON downloads.

## Scope and verification

This packaging operation has not deployed or uploaded anything. The standard-library integrity/privacy audit was run in Codex; Linux numerical dependencies and native Windows launch remain unavailable here, so the model/runtime/Streamlit smoke test is provided for Python 3.12 execution. See [TEST_STATUS.md](TEST_STATUS.md). No public cloud launch is claimed complete.
