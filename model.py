# coding: utf-8

# Product: Perform signature on photos and resize optimized for Instagram
# Author: marksard
# Version: 3
# Require Device: iPhone series
# Require App: pythonista 3

# 1. Input you sign at text0, 1, 2 in Watermark class.
# 2. Install youe favorite fonts at /Fonts/ folder, and then update font_style in Watermark class.
# 3. Run view.py
# as optional: You can change other property in Watermark class with try and error :)

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from PIL import Image, ImageDraw, ImageFont
from PIL.ExifTags import TAGS
import photos
import console
import matplotlib.pyplot as plt
import os


class Watermark(object):
    text0 = '@YourName'       # sign 1
    text1 = ' Your Name'      # sign 2
    text2 = ' You: %b. %d %Y' # sign with date
    index = 0
    format = 0
    font_size = 32
    # for PC debug.
    # font_style = 'Fonts/YourFavoriteFonts.ttf'
    font_style = os.path.dirname(__file__) + '/Fonts/YourFavoriteFonts.ttf'
    opacity = 200
    color = (255, 255, 255)
    inner_offset = (3, 2, 3, 2)
    position_width = 2
    position_height = 2


class Model(object):
    def __get_image(self):
        try:
            asset = photos.pick_asset()
            if asset is not None:
                return asset.get_image(), asset.creation_date
            else:
                print('no asset')
        except:
            print('exception: get_image')
            return None, None
        return None, None

    def __get_exif(self, image_object):
        try:
            exif = image_object._getexif()
        except AttributeError:
            return {}

        exif_table = {}
        for tag_id, value in exif.items():
            tag = TAGS.get(tag_id, tag_id)
            exif_table[tag] = value

        return exif_table

    def __fit_to_instagram(self, image_object):
        org_width, org_height = image_object.size
        if org_width >= org_height:
            image_object.thumbnail((1080, 1080), Image.ANTIALIAS)
        else:
            aspect = Decimal((1.0 * org_height / org_width) / 1.25)
            aspect = Decimal(
                aspect.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))
            image_object.thumbnail((1350 * aspect, 1350 * aspect),
                                   Image.ANTIALIAS)
            thumb_width, thumb_height = image_object.size
            offset_height = Decimal((thumb_height - 1350) / 2).quantize(
                Decimal('0'), ROUND_HALF_UP)
            box = (0, offset_height, thumb_width, thumb_height - offset_height)
            image_object = image_object.crop(box)
        return image_object

    def __fit_to_instagram_square_mount(self, image_object):
        image_object.thumbnail((1020, 1020), Image.ANTIALIAS)
        sb_width, sb_height = image_object.size
        mount_background = Image.new(
            'RGBA', (1080, 1080), (255, 255, 255, 255))
        mount_lefttop = (int(540 - (sb_width / 2)),
                         int(540 - (sb_height / 2)) - 10)
        mount_background.paste(image_object, mount_lefttop)

        image_object = mount_background
        return image_object, (mount_lefttop[0] + sb_width, mount_lefttop[1] + sb_height)

    def __get_watermark(self, image_object, watermark, file_date):
        if watermark.index == 1:
            exif_table = self.__get_exif(image_object)
            exif_date_string = exif_table.get("DateTimeOriginal")

            if exif_date_string is None:
                ret = console.alert(
                    'exif error',
                    'It selected image is not EXIF. Would you select original image file? (if cancel, use file creation date.)',
                    'OK',
                    'Cancel',
                    hide_cancel_button=True)
                if ret == 1:
                    image, file_date = photos.pick_asset().get_image()
                    #image = self.__get_image()
                    exif_table = self.__get_exif(image)
                    exif_date_string = exif_table.get("DateTimeOriginal")

            if exif_date_string is not None:
                exif_date = datetime.strptime(exif_date_string,
                                              '%Y:%m:%d %H:%M:%S')
                exif_date_reformat = exif_date.strftime(watermark.text2)
                return exif_date_reformat
            return file_date.strftime(watermark.text2)
        if watermark.index == 2:
            return watermark.text1
        else:
            return watermark.text0

    def __get_watermark_position(self, image_width, image_height, text_width,
                                 text_height, watermark):
        x = 0
        y = 0
        if watermark.position_width == 0:
            x = x + watermark.inner_offset[0]
        elif watermark.position_width == 1:
            x = (image_width / 2) - (
                text_width /
                2) + watermark.inner_offset[0] - watermark.inner_offset[2]
        elif watermark.position_width == 2:
            x = image_width - text_width - watermark.inner_offset[2]

        if watermark.position_height == 0:
            y = y + watermark.inner_offset[1]
        elif watermark.position_height == 1:
            y = (image_height / 2) - (
                text_height /
                2) + watermark.inner_offset[1] - watermark.inner_offset[2]
        elif watermark.position_height == 2:
            y = image_height - text_height - watermark.inner_offset[3]

        return (int(x), int(y))

    def __get_watermark_color(self, image_object, position, text_width,
                              text_height):
        hist_image = image_object.crop(
            (position[0], position[1], position[0] + text_width,
             position[1] + text_height)).convert('RGB')
        hist_image.show()
        hist_rgb = hist_image.histogram()
        hist_y = []
        count = text_width * text_height
        cont_low_level = []
        startpos = 0
        startpos_after_count = 0

        detect_high = 10
        for r in range(256):
            g = r + 256
            b = g + 256
            # RGB to Y
            y = int(((0.299 * hist_rgb[r]) + (0.587 * hist_rgb[g]) +
                     (0.114 * hist_rgb[b])) / count * 10000)
            hist_y.append(y)
            if 0 <= y and detect_high >= y:
                if startpos_after_count == 0:
                    startpos = r
                startpos_after_count = startpos_after_count + 1

            if startpos_after_count > 10 and (r >= 255 or detect_high < y):
                cont_low_level.append((startpos, r))
                startpos_after_count = 0
            elif detect_high < y:
                startpos_after_count = 0

        optimisation_color = 255
        if len(cont_low_level) > 0:
            col_widths = [v[1] - v[0] for i, v in enumerate(cont_low_level)]
            col_index = [
                i for i, v in enumerate(col_widths) if v == max(col_widths)
            ]
            print(cont_low_level)
            ll = cont_low_level[col_index[0]]
            col_width = ll[1] - ll[0]
            startpos = ll[0]
            optimisation_color = startpos + int(col_width / 2)
            print(optimisation_color)

        horizon = range(256)
        plt.cla()
        plt.xlim([0, 255])
        plt.ylim([0, max(hist_y)])
        plt.vlines(
            [optimisation_color],
            0,
            max(hist_y),
            colors="k",
            linestyle="dashed",
            label="")
        plt.plot(horizon, hist_y)
        plt.show()

        return plt, optimisation_color

    def resize_and_watermark(self, watermark):
        # Open a source file.
        source_origin, source_file_date = self.__get_image()

        # for PC debug.
        # source_file_date = datetime.today()
        # source_origin = Image.open('../images/IMG_3511.jpg')

        if source_origin is None:
            return None, None, None

        # Get a creation time.
        watermark_text = self.__get_watermark(source_origin, watermark,
                                              source_file_date)
        print(watermark_text)

        # Fit to instagram.
        mount_rightbottom = (0, 0)
        if watermark.format == 1:
            source_background, mount_rightbottom = self.__fit_to_instagram_square_mount(
                source_origin.convert(
                    'RGBA'))  # counvert source_origin from RGB to ARGB.
        else:
            source_background = self.__fit_to_instagram(
                source_origin.convert(
                    'RGBA'))  # counvert source_origin from RGB to ARGB.

        # Generate a watermark image.
        watermark_image = Image.new('RGBA', source_background.size,
                                    (255, 255, 255, 0))
        watermark_image_draw_object = ImageDraw.Draw(watermark_image)

        # Get a font
        font = ImageFont.truetype(
            font=watermark.font_style, size=watermark.font_size)
        # Get a text size
        text_width, text_height = watermark_image_draw_object.textsize(
            watermark_text, font=font)

        # Get a position
        position = (0, 0)
        if watermark.format == 1 and mount_rightbottom is not None:
            position = (mount_rightbottom[0] - text_width - 5,
                        mount_rightbottom[1])
        else:
            position = self.__get_watermark_position(source_background.width,
                                                     source_background.height, text_width,
                                                     text_height, watermark)

        # Get the color different from the color of the rear image
        plt, optimisation_color = self.__get_watermark_color(
            source_background, position, text_width, text_height)
        watermark.color = (optimisation_color, optimisation_color,
                           optimisation_color)

        # Draw a text
        watermark_image_draw_object.text(
            position,
            watermark_text,
            font=font,
            fill=watermark.color + (watermark.opacity, ))

        # Composite a images.
        out = Image.alpha_composite(source_background,
                                    watermark_image).convert('RGB')

        # Save a image file.
        photos.save_image(out)

        # for PC debug.
        # out.show()
        # out.save("../output/out.jpg")

        sign = out.crop((position[0], position[1], position[0] + text_width,
                         position[1] + text_height))

        return out, sign, plt


if __name__ == '__main__':
    watermark = Watermark()
    model = Model()
    model.resize_and_watermark(watermark)
