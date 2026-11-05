"""Read-only packaged data adapter for the EXISTING date-wise dashboard.
No source-scene discovery, private annotations, model fitting, or live inference.
"""
from __future__ import annotations
import base64
import csv
from html import escape
import io
import json
from pathlib import Path
import tempfile
import threading
import hashlib

ROOT=Path(__file__).resolve().parent
DATA_DIR=ROOT/'data'
DEFAULT_CACHE=Path(tempfile.gettempdir())/'kandla_public_exports'
_EXPORT_LOCK=threading.Lock()


def asset_path(value):
    path=Path(value)
    if path.is_absolute():
        resolved=path.resolve()
    else:resolved=(ROOT/path).resolve()
    if not resolved.is_relative_to(ROOT):raise ValueError('Asset outside packaged public demo')
    return resolved


def source_dir():return DATA_DIR  # Packaged preview data, never the original scene folder.


def load_json(path):return json.loads(asset_path(path).read_text(encoding='utf-8'))


def discover_dates(data=None,source=None):
    manifest=load_json('data/demo_manifest.json');result={}
    for date,item in manifest['dates'].items():
        bundle=load_json(item['bundle']);scenes=[]
        for r in bundle['scenes']:
            scenes.append(dict(scene_id=r['scene_id'],split=r['split'],source_tile_count=r['source_tile_count'],
                available_tile_count=r['processed_tile_count'],missing_tile_ids=[],has_validation_annotations=False,
                processed_tile_count=r['processed_tile_count'],missing_tile_count=r['missing_tile_count']))
        result[date]=dict(acquisition_date=date,scene_ids=bundle['scene_ids'],split='val',scenes=scenes)
    return result


def discover_models(project=None,tuning_run=None):
    meta=load_json('models/report.json')
    return {meta['name']:dict(path='models/selected_model.joblib',metadata=meta)}


def model_token(path):
    p=asset_path(path);report=asset_path('models/report.json')
    return tuple((str(item.relative_to(ROOT)),item.stat().st_size,item.stat().st_mtime_ns) for item in (p,report))


def load_model(path):
    # Cloud displays recorded predictions; loading a forest for every visit wastes RAM.
    # Full estimator deserialization/feature checks are available in smoke_test.py --runtime.
    asset_path(path)
    return None,load_json('models/report.json')


def analyze_date(date,data=None,source=None,model_path=None,cache=None,model=None,metadata=None,progress=None):
    catalog=load_json('data/demo_manifest.json')['dates']
    if date not in catalog:raise ValueError('Date not included in the public demo')
    path=asset_path(catalog[date]['bundle']).parent
    if progress:progress(1.,'Loaded real cached full-scene statistics and aligned preview mosaics')
    return path


def load_arrays(path,preview=1024):
    import numpy as np
    folder=asset_path(path)
    if preview!=1024:raise ValueError('Only the documented public 1024-pixel preview is included')
    with np.load(folder/'preview_1024.npz',allow_pickle=False) as archive:
        return {name:archive[name] for name in archive.files}


def png_data(array):
    from PIL import Image
    stream=io.BytesIO();Image.fromarray(array).save(stream,format='PNG');return stream.getvalue()


def preview_inspection(path,row,col):
    report=load_json(asset_path(path)/'analysis.json');arrays=load_arrays(path)
    h,w=arrays['valid'].shape;H,W=report['geometry']['height'],report['geometry']['width']
    # Exact original source sample represented by the selected PREVIEW pixel.
    return dict(preview_row=row,preview_col=col,source_sample_row=int(row*H/h),source_sample_col=int(col*W/w),
        covered=bool(arrays['covered'][row,col]),valid=bool(arrays['valid'][row,col]),
        semantic_class=int(arrays['classes'][row,col]),ship_probability=float(arrays['probability'][row,col]),
        scope='Display sample only; not an arbitrary full-resolution source pixel query')


def export_date(bundle_path,opacity=.45,threshold=0.):
    with _EXPORT_LOCK:
        return _export_date(bundle_path,opacity,threshold)


def _export_date(bundle_path,opacity=.45,threshold=0.):
    from cloud_render import render_layer
    bundle=load_json(asset_path(bundle_path)/'date_bundle.json')
    token=hashlib.sha256(json.dumps([bundle['input_fingerprint'],opacity,threshold,'public-preview-v1']).encode()).hexdigest()[:20]
    out=DEFAULT_CACHE/token
    if (out/'report.html').is_file():return out
    out.mkdir(parents=True,exist_ok=True)
    figures=[]
    for report in bundle['scenes']:
        folder=out/report['scene_id'];folder.mkdir(exist_ok=True);arrays=load_arrays(report['cache_path'])
        layers={'Original RGB':'rgb.png','Predicted semantic classes':'classification.png',
            'RGB + prediction overlay':'overlay.png','Ship probability heatmap':'ship_probability.png'}
        for layer,name in layers.items():
            rgba=render_layer(arrays,layer,opacity,threshold);(folder/name).write_bytes(png_data(rgba))
            if layer in ('RGB + prediction overlay','Ship probability heatmap'):
                data=base64.b64encode(png_data(rgba)).decode()
                figures.append(f'<figure><img src="data:image/png;base64,{data}" alt="{escape(layer)}"><figcaption>{escape(report["scene_id"])} · {escape(layer)} · PREVIEW ONLY</figcaption></figure>')
        (folder/'source_geometry.json').write_text(json.dumps(dict(source_geometry=report['geometry'],preview_geometry=report['preview_geometry'],
            preview_only=True,metrics_scope=report['metrics_scope'],model_sha256=report['model_sha256']),indent=2))
        (folder/'analysis.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    (out/'date_statistics.csv').write_bytes((asset_path(bundle_path)/'date_statistics.csv').read_bytes())
    sections=[]
    for r in bundle['scenes']:
        s=r['statistics'];m=r['validation_metrics'];ship=m['ship'] if m else {}
        rows=''.join(f'<tr><td>{name.title()}</td><td>{n:,}</td><td>{s["class_percent_of_unique_valid"][name]:.3f}%</td></tr>' for name,n in s['class_pixels'].items())
        sections.append(f'<section><h2>{escape(r["scene_id"])}</h2><table><tr><th>Class</th><th>Unique source pixels</th><th>% of valid analyzed pixels</th></tr>{rows}</table><p>Coverage {s["covered_percent_of_source"]:.3f}%. Ship surface area {s["ship_area_m2"]:,.1f} m² = {s["class_pixels"]["ship"]:,} pixels × {s["pixel_area_m2"]} m²/pixel. Source CRS {escape(r["geometry"]["crs"])}.</p><h3>Cached validation statistics</h3><pre>{escape(json.dumps(dict(ship=ship,confusion_matrix=m["confusion_matrix"] if m else None,scored_unique_pixels=m["scored_unique_pixels"] if m else None),indent=2))}</pre><h3>Provenance</h3><pre>{escape(json.dumps(dict(model_sha256=r["model_sha256"],input_fingerprint=r["input_fingerprint"],geometry=r["geometry"],preview_geometry=r["preview_geometry"],overlap_policy=r["overlap_policy"]),indent=2))}</pre></section>')
    html=f'''<!doctype html><html lang="en"><meta charset="utf-8"><title>Kandla Port · {bundle['acquisition_date']}</title><style>body{{background:#101923;color:#dde7ed;font:16px system-ui;margin:32px auto;max-width:1100px;padding:24px}}h1,h2{{color:#54c8b6}}section{{background:#172835;padding:24px;margin:22px 0;border-radius:10px}}table{{width:100%;border-collapse:collapse}}td,th{{padding:12px;border-bottom:1px solid #456}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}figure{{display:inline-block;vertical-align:top;max-width:45%;margin:12px}}img{{max-width:100%;max-height:650px;background:#243440}}.note{{padding:16px;border-left:4px solid #54c8b6;background:#172835}}</style><h1>KANDLA PORT | SATELLITE ANALYTICS</h1><h2>{bundle['acquisition_date']}</h2><p class="note">PUBLIC PRECOMPUTED DEMO — REAL PREVIEWS ONLY. Images are aligned display samples from complete source scenes. All counts and metrics below are recorded full-resolution unique-pixel statistics, not measurements from these previews. Raw scenes and annotation masks are not distributed. Threshold/opacity change figures only; no inference, retraining or test evaluation occurs.</p>{''.join(figures)}{''.join(sections)}<p>Ship pixels and classified surface area are not individual vessel counts. Validation was used for tuning and is not independent test performance. Reserved test data are excluded.</p></html>'''
    temp=out/'report.html.tmp';temp.write_text(html,encoding='utf-8');temp.replace(out/'report.html')
    return out
