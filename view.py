# Product: Perform signature on photos and resize optimized for Instagram
# Author: marksard
# Version: 3
# Require Device: iPhone series
# Require App: pythonista 3

import ui
from model import Model, Watermark
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import matplotlib.pyplot as plt

watermark = Watermark()
model = Model()

v = ui.load_view()

def __pil_to_ui(img):
    b = BytesIO()
    img.save(b, 'png')
    data = b.getvalue()
    b.close()
    return ui.Image.from_data(data)


@ui.in_background
def btn_select_image_tapped(sender):
    #global watermark
    #global model
    v.close()
    v.wait_modal()
    
    image, sign, plot = model.resize_and_watermark(watermark)
    
    v.present()
    if image is None:
        return

    parent = sender.superview
    image_view = parent['imgResultView']
    image_view.content_mode = ui.CONTENT_SCALE_ASPECT_FIT
    image_view.image = __pil_to_ui(image)

    sign_view = parent['imgSignView']
    sign_view.content_mode = ui.CONTENT_SCALE_ASPECT_FIT
    sign_view.image = __pil_to_ui(sign)

    b = BytesIO()
    plot.savefig(b)
    img = ui.Image.from_data(b.getvalue())

    hist_view = parent['imgHistView']
    #hist_view.content_mode = ui.CONTENT_SCALE_ASPECT_FIT
    hist_view.image = img


def seg_format_change(sender):
    # global watermark
    watermark.format = sender.selected_index
    parent = sender.superview
    if watermark.format == 1:
        parent['segHorizontal'].enabled = False
        parent['segVertical'].enabled = False
    else:
        parent['segHorizontal'].enabled = True
        parent['segVertical'].enabled = True


def seg_select_name_change(sender):
    # global watermark
    watermark.index = sender.selected_index


def seg_horizontal_change(sender):
    # global watermark
    watermark.position_width = sender.selected_index


def seg_vertical_change(sender):
    # global watermark
    watermark.position_height = sender.selected_index


__seg_f = v['segFormat']
__seg_f.action = seg_format_change
__seg_f.selected_index = watermark.format

__seg_n = v['segSelectName']
__seg_n.action = seg_select_name_change
__seg_n.segments = watermark.btn_text
__seg_n.selected_index = watermark.index

__seg_h = v['segHorizontal']
__seg_h.action = seg_horizontal_change
__seg_h.selected_index = watermark.position_width

__seg_v = v['segVertical']
__seg_v.action = seg_vertical_change
__seg_v.selected_index = watermark.position_height

__btn_img = v['btnSelectImage']
__btn_img.action = btn_select_image_tapped

v.present('full_screen', hide_title_bar=True)
#v.send_to_bacck()
#v.wait_modal()
