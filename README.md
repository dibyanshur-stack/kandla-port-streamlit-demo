# Kandla Port — Community Cloud deployment bundle

This is a self-contained, public **precomputed demonstration** of the existing date-wise dashboard. The original research app, trained models, masks and results remain unchanged in the parent project. The dashboard's layout, date/scene workflow, scientific charts, layers and map viewer are retained; the data adapter uses only the files in this directory.

## Included real demonstration dates

- **20260531** — `20260531_063100_24_2504_3B`.
- **20260603** — `20260603_063613_80_250a_3B`.
- **20260604** — `20260604_062718_84_251e_3B`.

These are validation scenes already analyzed locally with the selected tuned RF-2. Each included RGB/classes/probability/quality/coverage preview has a maximum dimension of **1024 pixels**, sampled from the real complete scene mosaic. Source geometry and the exact source-sample mapping are included. All counts, areas, probability summaries and validation metrics come from the recorded **full-resolution unique-pixel analysis**, never from counting these lower-resolution previews. See [AVAILABLE_DATES.md](AVAILABLE_DATES.md).

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

## Update the existing GitHub repository

The existing remote is `https://github.com/dibyanshur-stack/kandla-port-streamlit-demo.git`, branch `main`, app entrypoint `app.py`. Keep the existing repository and Streamlit app.

From the parent research project, run the complete exporter with the existing research environment. It discovers validation scenes from the immutable manifest/index, reuses verified selected-model caches and computes missing scenes with RF-2. It builds a candidate, runs the privacy/integrity smoke audit, then updates this bundle. It never fits a model or reads reserved test label contents.

```powershell
$Py = (Resolve-Path .\.venv\Scripts\python.exe).Path
& $Py .\scripts\export_validation_deployment.py
if ($LASTEXITCODE -ne 0) { throw "Validation export incomplete; review the reported scenes" }
& $Py .\deployment\smoke_test.py --runtime
if ($LASTEXITCODE -ne 0) { throw "Runtime smoke test failed" }

Push-Location .\deployment
try {
    $Remote = git remote get-url origin
    if ($LASTEXITCODE -ne 0 -or $Remote -ne "https://github.com/dibyanshur-stack/kandla-port-streamlit-demo.git") { throw "Unexpected existing remote" }
    $Branch = git branch --show-current
    if ($Branch -ne "main") { throw "Expected existing main branch" }
    git add -- data AVAILABLE_DATES.md TEST_STATUS.md PUBLIC_MANIFEST.json README.md smoke_test.py
    if ($LASTEXITCODE -ne 0) { throw "Staging failed" }
    git diff --cached --stat
    git commit -m "Extend validation date previews using selected tuned RF-2"
    if ($LASTEXITCODE -ne 0) { throw "Commit failed or no changes to commit" }
    git push origin main
    if ($LASTEXITCODE -ne 0) { throw "Push failed; inspect remote changes before retrying" }
} finally { Pop-Location }
```

If dependencies are missing, install `deployment/requirements.txt` and `rasterio>=1.3,<2` into the existing Python 3.12 research environment first. Do not change the saved model's sklearn version. The export report is saved locally at `results/validation_deployment_export.json`, outside the public repository. `--cached-only` is an explicitly partial recovery option and exits with status 2 if available scenes still need inference.

See [AVAILABLE_DATES.md](AVAILABLE_DATES.md) for the current exact inventory and pending dates. Any available scenes reported as pending need the complete exporter to finish inference in native Windows Python. The included bundle passes its standard-library smoke audit.

The deployment allowlist excludes raw imagery, masks, credentials, environments and research results. Only compressed previews and aggregate statistics are committed. No repository initialization or new app creation is needed.

## Existing Streamlit Community Cloud app

Pushing the bundle to the existing repository updates the existing app through its GitHub connection. Keep its current configuration. The settings below describe the required environment; no new app is needed.

1. Sign in at [share.streamlit.io](https://share.streamlit.io/) with the GitHub account that can access the new repository.
2. Verify the existing app uses `kandla-port-streamlit-demo`, branch **main**, and main file **app.py**.
3. In **Advanced settings**, explicitly choose **Python 3.12**. The bundled `.python-version` documents the local target; the Cloud UI selection controls the actual runtime.
4. Allow the existing app to rebuild after the push. `requirements.txt` is at the repository root alongside `app.py`; no `packages.txt`, Windows environment variable, source-scene mount, API key or secrets are required.
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
