# Deployment verification status

The bundle is built from two existing real cached date analyses, not synthetic imagery. The original working app and research assets were not modified. The public copy preserves the existing dashboard layout, rendering and date/scene workflow, with a read-only packaged-data adapter.

## Checks executed in Codex

- **PASSED** standard-library deployment integrity/privacy smoke audit (26 bundled files, approximately 10.9 MB): verifies every listed model/data/code file, preview array grids/dtypes/probability ranges/NoData, source geometry/area/confusion support, date discovery, relative asset references, metadata redaction and estimator-prefix byte preservation.
- **PASSED** Python syntax checks for all five deployment entrypoints/helpers.
- **PASSED** date discovery/backend loading from `/tmp`, with no original source folder or Windows environment variables.
- **PASSED** Git allowlist checks in an isolated temporary repository: all public assets remain trackable, while six virtual-environment/secret/raw-scene/test-mask/training examples are excluded.

## Runtime checks not executed here

Linux Python lacks NumPy/joblib/Streamlit. Attempts to install numerical dependencies could not obtain packages from this environment's package index. Native Windows Python previously fails to launch through WSL. Therefore no claim is made that model deserialization, Streamlit browser rendering or Community Cloud deployment was executed here.

Run `python smoke_test.py --runtime` in the documented Python 3.12 environment before publishing. This loads the packaged model with matching sklearn, tests prediction API/feature compatibility, renders every preview layer, generates downloads, and uses Streamlit's AppTest to exercise initial/date/download views. It does not fit a model or access private/test data.

No files have been uploaded and no cloud application has been created by Codex.
