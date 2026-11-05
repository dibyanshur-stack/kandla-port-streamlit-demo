# Public data scope

This package contains two **real, derived display previews** of completed Kandla Port source-scene mosaics, their cached predicted labels/probabilities/validity/coverage and aggregate full-resolution statistics. It does not contain original PlanetScope SR/UDM2 scenes, raw satellite archives, training/validation annotation rasters, the reserved 15 test masks, test metrics, private tile inventories or credentials.

Pixel annotation layers have been removed, including `truth`, `annotated`, `conflicts` and `source_valid` arrays. Aggregate validation metrics are retained as recorded; unannotated pixels were not treated as background. The public preview model is the same learned estimator used for these analyses. Inert model metadata strings containing local paths/identifiers are redacted without changing estimator bytes.

Preview pixels are nearest source samples on a shared 1024 × 293 display grid. Their mapping to original rows/columns and the unchanged original CRS/affine/grid are recorded. Do not claim these previews have the native 3 m resolution or derive new scene counts by counting preview pixels. No interpolated/upsampled GeoTIFF is offered as native-resolution output.

No new source-imagery redistribution license is granted by this bundle. The full private research dataset and original imagery licenses are not distributed or changed.

No retraining, new inference, test evaluation, verified vessel count or independent test accuracy is claimed. Raw RF probabilities are uncalibrated. Pixel area is not individual-vessel count; structures and wakes can cause false positives and small ships can be missed.
