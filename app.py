"""Date-wise Kandla Port dashboard. Native launch: python -m streamlit run app.py"""
from __future__ import annotations
from datetime import datetime
import json
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import streamlit as st
import streamlit.components.v1 as components

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from cloud_backend import (source_dir,DATA_DIR,discover_dates,discover_models,model_token,load_model,
    analyze_date,DEFAULT_CACHE,load_arrays,png_data,export_date,asset_path,preview_inspection)
from dashboard_view import scene_canvas
from cloud_render import render_layer

st.set_page_config(page_title='Kandla Port | Satellite Analytics',page_icon='🛰️',layout='wide',initial_sidebar_state='expanded')
st.markdown('''<style>
.stApp{background:#101923;color:#e0eaf1}section[data-testid="stSidebar"]{background:#142330;border-right:1px solid #2c4250}
.block-container{padding-top:2rem;max-width:1600px}h1{font-size:1.9rem!important;letter-spacing:.085em;font-weight:650!important}h2{font-size:1.2rem!important;letter-spacing:.04em;margin-top:1.4rem!important}h3{font-size:1.05rem!important}
[data-testid="stMetric"]{background:#172835;border:1px solid #2b4352;border-top:3px solid #43b6a7;border-radius:9px;padding:18px 16px;min-height:110px}[data-testid="stMetricLabel"]{color:#b7cbd6}[data-testid="stMetricValue"]{font-size:1.8rem}
.smallcap{color:#55c8b6;font-size:.8rem;letter-spacing:.2em;font-weight:650}.subtle{color:#9eb5c5;font-size:.95rem;line-height:1.6}.legend{display:flex;gap:20px;flex-wrap:wrap;padding:13px 0;color:#ccdae4;font-size:13px}.legend span:before{content:"";display:inline-block;width:13px;height:13px;margin-right:7px;background:var(--c);border-radius:2px;vertical-align:middle}.rule{border-top:1px solid #2c4352;margin:18px 0}.note{padding:13px 18px;border-left:3px solid #45b9a8;background:#182c36;color:#c0d7df}
</style>''',unsafe_allow_html=True)
st.markdown('<div class="smallcap">PLANETSCOPE · SCENE-ALIGNED ANALYSIS</div>',unsafe_allow_html=True)
st.title('KANDLA PORT | SATELLITE SHIP DETECTION & ANALYTICS')
st.markdown('<div class="subtle">Acquisition date → complete source-scene mosaics → unique-pixel analytics. Original SR features · quality-aware inference · traceable exports.</div>',unsafe_allow_html=True)


@st.cache_resource(max_entries=2,show_spinner='Loading selected model provenance…')
def cached_model(path,token):return load_model(Path(path))


@st.cache_data(max_entries=3,ttl=30,show_spinner=False)
def cached_dates(data,source,index_token):return discover_dates(Path(data),Path(source))


@st.cache_data(max_entries=6,show_spinner=False)
def cached_preview(path,size,stamp):return load_arrays(Path(path),size)


@st.cache_data(max_entries=8,show_spinner=False)
def cached_json(path,stamp):return json.loads(Path(path).read_text())


def read_json(path):
    p=Path(path);return cached_json(str(p),p.stat().st_mtime_ns)


def fmt(value,digits=3):return 'N/A' if value is None else f'{value:,.{digits}f}'


def show_download(label,path,mime,key):
    path=Path(path)
    if path.is_file():st.download_button(label,path.read_bytes(),file_name=path.name,mime=mime,key=key,use_container_width=True)


def main():
    data=DATA_DIR;source=source_dir();cache=DEFAULT_CACHE
    token=(('public_demo',(data/'demo_manifest.json').stat().st_mtime_ns),)
    dates=cached_dates(str(data),str(source),token)
    choices=discover_models(ROOT)
    if not dates:st.warning('No packaged demo dates found; check data/demo_manifest.json and run smoke_test.py.');st.stop()
    if not choices:st.warning('No compatible saved RF-2/RF-4 model/report pair found. Existing models are not retrained by this dashboard.');st.stop()
    with st.sidebar:
        st.markdown('### ACQUISITION WORKSPACE')
        st.info('Public precomputed demo · real preview mosaics only. No source imagery or pixel annotations are bundled.')
        date_ids=sorted(dates);preferred='20260531'
        default=date_ids.index(preferred) if preferred in date_ids else next((i for i,d in enumerate(date_ids) if dates[d]['split']=='val'),0)
        def date_label(d):
            bundle=dates[d];return f"{datetime.strptime(d,'%Y%m%d'):%d %b %Y} · {'Validation' if bundle['split']=='val' else 'Train'} · {len(bundle['scenes'])} scene(s)"
        date=st.selectbox('Acquisition date',date_ids,index=default,format_func=date_label)
        available_scenes=dates[date]['scenes'];scene_ids=dates[date]['scene_ids']
        scene_id=st.selectbox('Source scene / footprint',scene_ids) if len(scene_ids)>1 else scene_ids[0]
        if len(scene_ids)==1:st.caption(scene_id)
        else:st.info('Separate spatial footprints. Each scene is mosaicked independently; counts are not pooled across scenes.')
        model_names=list(choices);model_names.sort(key=lambda x:'Tuned selected' not in x)
        name=st.selectbox('Saved model · compatible features only',model_names)
        model_path=choices[name]['path'];mtoken=model_token(model_path)
        metadata=choices[name]['metadata'];mode=metadata['arguments']['features']
        st.caption(f"{mode} · {len(metadata['features'])} ordered features")
        with st.expander('Model and protocol'):
            st.json(dict(path=model_path,features=metadata['features'],parameters=metadata.get('model_hyperparameters'),sampling=metadata.get('sampling'),training_fingerprint=metadata.get('dataset_fingerprint')))
            st.caption('Saved full-resolution aggregate statistics. Figures are lower-resolution previews. No live inference or private annotation layers. Reserved test data are excluded.')
        layers=['Original RGB','Predicted semantic classes','RGB + prediction overlay','Ship probability heatmap']
        selected_scene=next(s for s in available_scenes if s['scene_id']==scene_id)
        if selected_scene['has_validation_annotations']:layers+=['CVAT ground truth','Validation error map']
        layer=st.selectbox('Analysis layer',layers,index=2)
        opacity=st.slider('Overlay opacity',0.,1.,.45,.05)
        threshold=st.slider('Ship probability display threshold',0.,1.,0.,.01)
        st.caption('Display threshold does not alter predicted classes, area, or validation scores.')
        run=st.button('Load cached date analysis',type='primary',use_container_width=True)
        st.caption(f"Recorded analysis used {sum(s['source_tile_count'] for s in available_scenes)} indexed tiles. The included mosaics are aligned previews of that completed analysis.")
    state_key=(date,model_path,mtoken,token)
    if run:
        progress=st.progress(0.,text='Loading packaged real date analysis…')
        model,verified_metadata=cached_model(model_path,mtoken)
        try:
            output=analyze_date(date,data,source,model_path,cache,model,verified_metadata,
                progress=lambda fraction,message:progress.progress(min(1.,fraction),text=message))
            st.session_state['date_analysis']=(state_key,str(output));progress.progress(1.,text='Cached scene analysis loaded · preview-only public data')
        finally:progress.empty()
    current=st.session_state.get('date_analysis')
    if not current or current[0]!=state_key:
        st.markdown('<div class="rule"></div><div class="note">Choose an acquisition date and saved model, then select <b>Load cached date analysis</b>. Cached predictions are reused. No training or live inference is performed.</div>',unsafe_allow_html=True)
        st.dataframe(pd.DataFrame([dict(scene=s['scene_id'],split=s['split'],indexed_tiles=s['source_tile_count'],available_tiles=s['available_tile_count'],missing_tiles=s['missing_tile_count']) for s in available_scenes]),hide_index=True,use_container_width=True)
        return
    bundle_path=Path(current[1]);bundle=read_json(bundle_path/'date_bundle.json')
    report=next(r for r in bundle['scenes'] if r['scene_id']==scene_id);stats=report['statistics'];metrics=report['validation_metrics']
    preview_path=asset_path(report['cache_path']);arrays=cached_preview(str(preview_path),1024,(preview_path/'analysis.json').stat().st_mtime_ns)
    st.info('REAL PRECOMPUTED DEMO · preview mosaics are 1024 × 293 display samples. All KPIs and validation metrics are recorded from the original full-resolution unique scene pixels; no new analysis is claimed.')
    st.markdown('## A · ACQUISITION OVERVIEW')
    st.caption(f"{date_label(date)} · Showing source scene {scene_id}. All pixel KPIs below refer to this scene, not a sum of overlapping scene footprints.")
    for col,label,value in zip(st.columns(4),('Analyzed scenes on date','Unique quality-valid pixels','Predicted Ship pixels','Ship coverage · % of valid'),
        (str(bundle['analyzed_scenes']),f"{stats['quality_valid_pixels']:,}",f"{stats['class_pixels']['ship']:,}",fmt(stats['class_percent_of_unique_valid']['ship'])+'%')):
        col.metric(label,value)
    if metrics:
        for col,key in zip(st.columns(3),('precision','recall','f1')):col.metric('Validation Ship '+key.upper(),fmt(metrics['ship'][key],4))
        st.caption(f"Scored on {metrics['scored_unique_pixels']:,} unique, quality-valid, annotated scene pixels. Unannotated pixels are excluded, not assigned to background.")
    if report['missing_tile_count']:st.warning(f"{report['missing_tile_count']} missing tile files. Gaps are transparent and excluded from predictions; coverage is {stats['covered_percent_of_source']:.2f}%.")
    if report['prediction_disagreements']:st.warning(f"Overlapping predictions disagree at {report['prediction_disagreements']:,} overlap observations; deterministic first-tile ownership applied.")
    if stats['annotation_conflict_pixels']:st.warning(f"Conflicting non-Ignore annotations excluded: {stats['annotation_conflict_pixels']:,} unique pixels.")
    st.markdown('## B · FULL SOURCE-SCENE MOSAIC')
    if layer in ('CVAT ground truth','Validation error map') and not stats['annotated_footprint_pixels']:
        st.info('No imported validation annotation exists for this scene. This layer is transparent.')
    rgba=render_layer(arrays,layer,opacity,threshold);g=report['geometry']
    components.html(scene_canvas(png_data(rgba),g['width'],g['height'],g['transform'],g['crs']),height=790,scrolling=False)
    st.markdown('<div class="legend"><span style="--c:#fa3253">Ship</span><span style="--c:#3d3df5">Water</span><span style="--c:#0ae411">Other</span><span style="--c:#000">Ignore</span><span style="--c:#be50cd">Invalid · purple checker</span><span style="--c:#556575">Uncovered · transparent</span></div>',unsafe_allow_html=True)
    if layer=='Validation error map':st.caption('Green: correct Ship · Magenta: missed Ship · Orange: Water→Ship · Gold: Other→Ship · Cyan: Water/Other confusion · Gray: correct background. Only eligible annotation pixels are visible.')
    if layer=='Ship probability heatmap':
        from cloud_render import color_scale
        st.image(color_scale(),caption='Fixed 0–1 raw P(Ship) scale. Below-threshold valid pixels are light gray.')
    with st.expander('Expandable static scene preview'):
        st.image(rgba,caption=layer,use_container_width=True)
    st.caption(f"Original source geometry {g['width']:,} × {g['height']:,} pixels · {g['crs']} · PREVIEW ONLY · original grid and source-sample mapping are preserved in metadata. Full-resolution rasters remain local and are not included here.")
    with st.expander('Inspect an included preview sample'):
        hh,ww=arrays['valid'].shape
        a,b=st.columns(2);row=int(a.number_input('Preview row',0,hh-1,0));col=int(b.number_input('Preview column',0,ww-1,0))
        st.json(preview_inspection(preview_path,row,col))
    st.markdown('## C · ANALYSIS & CALCULATIONS')
    left,right=st.columns(2)
    rows=[dict(Class=label,Unique_pixels=count,Percent_of_quality_valid=stats['class_percent_of_unique_valid'][label]) for label,count in stats['class_pixels'].items()]
    left.dataframe(pd.DataFrame(rows),hide_index=True,use_container_width=True)
    left.bar_chart(pd.DataFrame(rows).set_index('Class')['Unique_pixels'],color='#49bcad')
    left.markdown(f"**Predicted Ship surface area:** {fmt(stats['ship_area_m2'],1)} m²")
    left.caption(f"{stats['class_pixels']['ship']:,} Ship pixels × {fmt(stats['pixel_area_m2'],3)} m²/pixel. Pixel area = absolute affine determinant × CRS unit conversion². This is classified surface area, not vessel count.")
    coverage=pd.DataFrame({'Pixels':[stats['quality_valid_pixels'],stats['covered_invalid_pixels'],stats['uncovered_pixels']]},index=['Analyzed quality-valid','Covered but invalid','Uncovered'])
    right.bar_chart(coverage,color='#6f9db7');right.dataframe(coverage,use_container_width=True)
    right.caption(f"Tile coverage: {stats['covered_percent_of_source']:.2f}% of source pixels. Quality-valid analyzed coverage: {stats['analyzed_valid_percent_of_source']:.2f}%. Source quality-valid pixels outside tile coverage: {stats['uncovered_quality_valid_pixels']:,}.")
    p=stats['probability'];centers=[(a+b)/2 for a,b in zip(p['histogram_edges'][:-1],p['histogram_edges'][1:])]
    st.markdown('### Ship probability · unique quality-valid pixels')
    st.bar_chart(pd.DataFrame({'Pixel count':p['histogram_counts']},index=pd.Index(centers,name='P(Ship) bin midpoint')),color='#48b9aa')
    st.caption(f"Min {fmt(p['min'],4)} · Median {fmt(p['median'],4)} · Mean {fmt(p['mean'],4)} · Max {fmt(p['max'],4)}. Raw probabilities are not calibrated confidence.")
    if metrics:
        st.markdown('### Validation · annotated coverage only')
        a,b=st.columns([1,2]);a.dataframe(pd.DataFrame(metrics['confusion_matrix'],index=['Truth Ship','Truth Water','Truth Other'],columns=['Pred Ship','Pred Water','Pred Other']),use_container_width=True)
        b.dataframe(pd.DataFrame(metrics['classes']).T[['support','precision','recall','f1','iou','true_positive','false_positive','false_negative']],use_container_width=True)
        st.write(f"Water→Ship false positives: **{metrics['water_to_ship_false_positives']:,}** · Other→Ship false positives: **{metrics['other_to_ship_false_positives']:,}**")
        st.caption('Undefined denominators are N/A. These validation scenes may have been used for model selection; no independent test accuracy is claimed.')
    else:st.info('No validation score is calculated for training scenes or scenes without eligible annotations.')
    st.markdown('### Per-scene date breakdown · separate footprints')
    st.dataframe(pd.DataFrame([dict(Scene=r['scene_id'],Split=r['split'],Unique_valid_pixels=r['statistics']['quality_valid_pixels'],Ship_pixels=r['statistics']['class_pixels']['ship'],Coverage_percent=r['statistics']['covered_percent_of_source'],Validation_scored_pixels=r['validation_metrics']['scored_unique_pixels'] if r['validation_metrics'] else None) for r in bundle['scenes']]),hide_index=True,use_container_width=True)
    st.markdown('## D · TRACEABLE DOWNLOADS')
    style_key=(str(bundle_path),opacity,threshold)
    if st.button('Prepare preview downloads & date report'):
        with st.spinner('Preparing included preview PNGs and cached-statistics HTML report…'):
            export=export_date(bundle_path,opacity,threshold);st.session_state['date_export']=(style_key,str(export))
    prepared=st.session_state.get('date_export')
    if prepared and prepared[0]==style_key:
        exports=Path(prepared[1]);folder=exports/scene_id
        with st.sidebar:
            st.markdown('### DOWNLOAD DATE REPORT')
            show_download('Date report · HTML',exports/'report.html','text/html','side_html')
            show_download('Date statistics · CSV',exports/'date_statistics.csv','text/csv','side_csv')
        cols=st.columns(3)
        for i,(label,file,mime) in enumerate([('Scene RGB preview PNG','rgb.png','image/png'),('Class preview PNG','classification.png','image/png'),('Overlay preview PNG','overlay.png','image/png'),('Ship probability preview PNG','ship_probability.png','image/png'),('Source grid / sample mapping','source_geometry.json','application/json'),('Recorded analysis JSON','analysis.json','application/json')]):
            with cols[i%3]:show_download(label,folder/file,mime,'download_'+file)
        show_download('Download self-contained date report',exports/'report.html','text/html','main_html')
    else:st.caption('Prepare downloads once for the current opacity/threshold. Only previews are distributed here; source-resolution rasters and private masks stay in the local project. Display settings never rerun inference.')
    with st.expander('Scientific limitations & provenance'):
        st.write('Port structures, wakes and bright water can cause false positives. Small ships may be missed. Predicted Ship pixels and area are not individual vessel counts. No verified vessel-count estimate is shown. Separate scene footprints are never pooled; historical tile-summed validation reports are not directly comparable to these deduplicated metrics. Reserved test scenes and labels are excluded.')
        st.json(dict(model_sha256=report['model_sha256'],input_fingerprint=report['input_fingerprint'],overlap_policy=report['overlap_policy'],geometry=g,source_tiles=report['source_tile_count'],processed_tiles=report['processed_tile_count']))

try:main()
except Exception as exc:
    st.error(f'Unable to complete this local scene analysis: {exc}')
    st.info('Check the packaged data files and the deployment smoke test; this public demo does not need original SR/UDM2 imagery. No model training or reserved test evaluation is performed.')
