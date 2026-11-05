"""The existing dashboard's render calculations, without raw-data dependencies."""
import numpy as np
from PIL import Image,ImageDraw,ImageFont
COLORS=np.array([[0,0,0],[250,50,83],[61,61,245],[10,228,17]],dtype=np.uint8)
COLOR_ANCHORS=np.array([[68,1,84],[59,82,139],[33,145,140],[94,201,98],[253,231,37]],dtype=np.float32)
def probability_colors(probability):
    values = np.asarray(probability,dtype=np.float32)
    if not np.isfinite(values).all() or np.any(values < 0) or np.any(values > 1):
        raise ValueError('Color scale accepts finite probabilities in [0,1] only')
    scaled = values*4; lower = np.minimum(scaled.astype(int),3); fraction = scaled-lower
    colors = (1-fraction[...,None])*COLOR_ANCHORS[lower]+fraction[...,None]*COLOR_ANCHORS[lower+1]
    return np.rint(colors).astype(np.uint8)

def font(size=16):
    try:
        return ImageFont.truetype('DejaVuSans.ttf',size)
    except OSError:
        return ImageFont.load_default()

def color_scale(width=600):
    image=Image.new('RGB',(width,86),'white');draw=ImageDraw.Draw(image)
    draw.text((12,4),'Raw model P(Ship): common fixed scale 0 to 1',font=font(15),fill='black')
    ramp=probability_colors(np.linspace(0,1,width-32,dtype=np.float32)[None,:])
    image.paste(Image.fromarray(ramp).resize((width-32,20),Image.Resampling.NEAREST),(16,30))
    for value in (0,0.25,0.5,0.75,1):
        x=16+int(value*(width-33));draw.line((x,50,x,55),fill='black')
        draw.text((max(4,min(x-12,width-40)),58),f'{value:g}',font=font(13),fill='black')
    return image

def render_layer(arrays,layer='RGB + prediction overlay',opacity=.45,threshold=0.):
    if layer in ('CVAT ground truth','Validation error map'):
        raise ValueError('Pixel annotation layers are private and not included in the public demo')
    if not 0<=opacity<=1 or not 0<=threshold<=1:raise ValueError('Opacity/threshold outside [0,1]')
    valid,covered=arrays['valid'],arrays['covered'];rgb=arrays['rgb'];classes=arrays['classes']
    alpha=np.where(covered,255,0).astype(np.uint8);color=rgb.copy()
    if layer=='Predicted semantic classes':color=COLORS[classes].copy()
    elif layer=='RGB + prediction overlay':color=np.rint((1-opacity)*rgb+opacity*COLORS[classes]).astype(np.uint8)
    elif layer=='Ship probability heatmap':
        color[:]=[210,218,226];active=valid & (arrays['probability']>=threshold)
        color[active]=probability_colors(arrays['probability'][active])
    elif layer in ('CVAT ground truth','Validation error map'):
        known=arrays['annotated'] & (arrays['truth']>0) & ~arrays['conflicts'] & valid
        visible=known if layer=='Validation error map' else arrays['annotated'] & valid & ~arrays['conflicts']
        alpha=np.where(visible,255,0).astype(np.uint8)
        color=COLORS[arrays['truth']].copy()
        if layer=='Validation error map':
            color[:]=[120,140,155];truth=arrays['truth']
            color[known & (truth==1)&(classes==1)]=[0,210,125]
            color[known & (truth==1)&(classes!=1)]=[230,50,210]
            color[known & (truth==2)&(classes==1)]=[255,100,45]
            color[known & (truth==3)&(classes==1)]=[255,185,45]
            color[known & (truth!=1)&(classes!=1)&(truth!=classes)]=[0,170,240]
    elif layer!='Original RGB':raise ValueError('Unknown dashboard layer')
    if layer not in ('CVAT ground truth','Validation error map'):
        rr,cc=np.indices(valid.shape);checker=(rr//8+cc//8)%2
        invalid=covered&~valid
        color[invalid & (checker==0)]=[80,40,100];color[invalid & (checker==1)]=[190,80,205]
    return np.dstack([color,alpha])
