"""Audit the entire self-contained Linux deployment. Default: standard library only.
--runtime additionally loads the saved model, renders previews and tests Streamlit.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
import math
from pathlib import Path
import pickletools
import re
import struct
import sys
import zipfile
import zlib

ROOT=Path(__file__).resolve().parent
ALLOWED={'rgb','classes','probability','valid','covered'}
PRIVATE=re.compile(r'(?:[A-Za-z]:[\\/]|/mnt/|/home/|/Users/|semantic_masks[\\/]|multispectral[\\/])')


def check(condition,message):
    if not condition:raise AssertionError(message)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))


def npy(data):
    check(data[:6]==b'\x93NUMPY','Invalid NPY header')
    n=2 if data[6:8]==b'\x01\x00' else 4
    h=int.from_bytes(data[8:8+n],'little');off=8+n+h;meta=ast.literal_eval(data[8+n:off].decode('latin1'))
    check(not meta['fortran_order'],'Unexpected column-major preview')
    return meta,data[off:]


def preview_audit(path):
    with zipfile.ZipFile(path) as archive:
        check(set(archive.namelist())=={x+'.npy' for x in ALLOWED},'Private or missing arrays in public preview')
        arrays={name:npy(archive.read(name+'.npy')) for name in ALLOWED}
    shape=arrays['valid'][0]['shape'];h,w=shape
    check(arrays['rgb'][0]['shape']==(h,w,3),'RGB/class grid mismatch')
    check(arrays['rgb'][0]['descr']=='|u1','RGB dtype changed')
    check(arrays['classes'][0]['descr']=='|u1','Class dtype changed')
    check(arrays['probability'][0]['descr'] in ('<f4','=f4'),'Probability dtype changed')
    for name in ('valid','covered'):check(arrays[name][0]['descr']=='|b1',f'{name} not boolean')
    for name in ('classes','probability','covered'):check(arrays[name][0]['shape']==shape,'Layer grid mismatch')
    pixels=h*w
    check(len(arrays['rgb'][1])==pixels*3,'RGB payload size mismatch')
    classes,valid,covered=arrays['classes'][1],arrays['valid'][1],arrays['covered'][1]
    check(len(classes)==len(valid)==len(covered)==pixels,'Preview payload length mismatch')
    check(len(arrays['probability'][1])==pixels*4,'Probability payload length mismatch')
    for i,(p,) in enumerate(struct.iter_unpack('<f',arrays['probability'][1])):
        check(valid[i] in (0,1) and covered[i] in (0,1),'Invalid mask value')
        if valid[i]:
            check(covered[i]==1 and classes[i] in (1,2,3),'Validity/class coverage mismatch')
            check(math.isfinite(p) and 0<=p<=1,'Probability out of range')
        else:check(classes[i]==0 and p==-9999,'Invalid-pixel NoData contract changed')
    return shape


def audit():
    manifest=read('data/demo_manifest.json');public=read('PUBLIC_MANIFEST.json')
    files={p.relative_to(ROOT).as_posix():p for p in ROOT.rglob('*') if p.is_file()
           and '.git' not in p.relative_to(ROOT).parts and '__pycache__' not in p.relative_to(ROOT).parts}
    check(set(files)==set(public['files'])|{'PUBLIC_MANIFEST.json'},'Bundle contains missing or unreviewed files')
    for relative,item in public['files'].items():
        check(files[relative].stat().st_size==item['bytes'] and sha(files[relative])==item['sha256'],f'Asset changed: {relative}')
        check(item['bytes']<100*1024*1024,'File exceeds ordinary GitHub limit')
    for p in ROOT.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'),filename=str(p))
    metadata=read('models/report.json');proof=read('models/byte_preservation.json')
    model=ROOT/manifest['model'];check(sha(model)==metadata['public_artifact_sha256']==proof['public_artifact_sha256'],'Model hash mismatch')
    raw=zlib.decompress(model.read_bytes());boundary=proof['estimator_prefix_bytes']
    check(hashlib.sha256(raw[:boundary]).hexdigest()==proof['estimator_prefix_sha256'],'Fitted estimator bytes changed')
    ops=list(pickletools.genops(raw[boundary:]));check(ops[-1][0].name=='STOP','Invalid model metadata framing')
    for _,arg,_ in ops:
        if isinstance(arg,str):
            check(not PRIVATE.search(arg),'Private model metadata remains')
            check(not re.match(r'^20\d{6}(?:_|$)',arg),'Private date/tile inventory remains in model metadata')
    expected=['coastal_blue','blue','green_i','green','yellow','red','red_edge','nir','NDVI','NDWI','NDRE','GNDVI']
    check(metadata['features']==expected,'Selected model is not expected RF-2 feature order')
    for path in files.values():
        if path.suffix in ('.json','.csv'):
            check(not PRIVATE.search(path.read_text(encoding='utf-8')),f'Local/private path in public text: {path.name}')
    from cloud_backend import discover_dates,discover_models,analyze_date,asset_path
    dates=discover_dates();check(set(dates)==set(manifest['dates']),'Discovery mismatch')
    check(len(discover_models())==1,'Unexpected model exposed')
    scene_count=0
    for date,item in manifest['dates'].items():
        bundle=read(item['bundle']);check(bundle['split']=='val' and bundle['preview_only'],'Reserved/non-preview bundle exposed')
        check(analyze_date(date)==(ROOT/item['bundle']).parent,'Date requires original data')
        for scene in bundle['scenes']:
            scene_count+=1;check(scene['split']=='val' and not scene['labels_public'],'Private labels exposed')
            check(scene['model_sha256']==metadata['source_artifact_sha256'],'Stats are from a different estimator')
            shape=preview_audit(asset_path(scene['cache_path'])/'preview_1024.npz')
            check(shape==(scene['preview_geometry']['height'],scene['preview_geometry']['width']),'Preview geometry mismatch')
            s=scene['statistics'];check(sum(s['class_pixels'].values())==s['quality_valid_pixels'],'Class counts do not sum to valid denominator')
            check(s['source_pixels']==scene['geometry']['height']*scene['geometry']['width'],'Source raster area mismatch')
            check(s['covered_pixels']+s['uncovered_pixels']==s['source_pixels'],'Coverage denominator mismatch')
            check(s['quality_valid_pixels']+s['covered_invalid_pixels']==s['covered_pixels'],'Quality accounting mismatch')
            check(sum(s['probability']['histogram_counts'])==s['quality_valid_pixels'],'Probability histogram support mismatch')
            check(abs(s['ship_area_m2']-s['class_pixels']['ship']*s['pixel_area_m2'])<1e-5,'Ship area formula mismatch')
            m=scene['validation_metrics'];check(sum(map(sum,m['confusion_matrix']))==m['scored_unique_pixels'],'Confusion support mismatch')
            check((ROOT/item['bundle']).with_name('date_statistics.csv').is_file(),'Date CSV missing')
    check('KANDLA_TUNING_RUN' not in (ROOT/'app.py').read_text(encoding='utf-8'),'Local environment dependency remains')
    return dict(status='passed',dates=list(dates),scenes=scene_count,files=len(files),total_bytes=sum(p.stat().st_size for p in files.values()),
                runtime='not executed; use --runtime with installed Python 3.12 requirements')


def runtime_audit():
    import joblib
    import numpy as np
    import sklearn
    from cloud_backend import load_arrays,export_date
    from cloud_render import render_layer
    from streamlit.testing.v1 import AppTest
    metadata=read('models/report.json')
    check(sklearn.__version__==metadata['sklearn_version'],'Wrong scikit-learn version for saved forest')
    artifact=joblib.load(ROOT/'models/selected_model.joblib');model=artifact['model']
    check(model.n_features_in_==len(metadata['features']),'Fitted feature width mismatch')
    check(model.classes_.tolist()==[1,2,3],'Model semantic class mapping mismatch')
    check(model.get_params()==metadata['model_hyperparameters'],'Model parameters changed')
    check(artifact['metadata']['features']==metadata['features'],'Embedded feature order differs')
    probability=model.predict_proba(np.zeros((2,12),np.float32))
    check(probability.shape==(2,3) and np.allclose(probability.sum(1),1),'Saved model cannot predict probabilities')
    for date,item in read('data/demo_manifest.json')['dates'].items():
        bundle=read(item['bundle'])
        for scene in bundle['scenes']:
            for layer in ('Original RGB','Predicted semantic classes','RGB + prediction overlay','Ship probability heatmap'):
                rendered=render_layer(load_arrays(ROOT/scene['cache_path']),layer)
                check(rendered.shape[-1]==4,'Preview layer rendering failed')
        out=export_date((ROOT/item['bundle']).parent);check((out/'report.html').is_file(),'HTML report export failed')
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=90).run()
    check(not app.exception,f'Streamlit initial load error: {app.exception}')
    next(button for button in app.button if button.label=='Load cached date analysis').click().run(timeout=90)
    check(not app.exception,f'Streamlit date view error: {app.exception}')
    next(button for button in app.button if button.label=='Prepare preview downloads & date report').click().run(timeout=90)
    check(not app.exception,f'Streamlit download view error: {app.exception}')
    return 'passed: model, render, HTML/CSV/PNG exports, Streamlit initial/date/download views'


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--runtime',action='store_true');args=parser.parse_args()
    report=audit()
    if args.runtime:report['runtime']=runtime_audit()
    print(json.dumps(report,indent=2))
