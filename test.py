# -*- coding:utf-8 -*-
from PIL import Image,ImageChops,ImageColor,ImageFilter
import os
import StringIO
from flask import Response, Flask
import random

def test():
    # 获取传递值

    modelPath = 'static/models/1666'
    patternPath = 'static/images/14.png'
    zoom_num=50

    im_ori = Image.open(modelPath + 'a.png')
    im_mask1 = Image.open(modelPath + 'c.png')
    im_mask2 = Image.open(modelPath + 'd.png')
    im_pattern = Image.open(patternPath)

    w1, h1 = im_ori.size
    w2, h2 = im_pattern.size

    # 花型缩放
    if zoom_num == 100:
        bg = im_pattern.resize((w2, h2), Image.ANTIALIAS)
    else:
        w2 = w2 * zoom_num / 100
        h2 = h2 * zoom_num / 100
        bg = im_pattern.resize((w2, h2), Image.ANTIALIAS)

    # The width and height of the background tile
    bg_w, bg_h = bg.size

    # Creates a new empty image, RGB mode, and size 1000 by 1000
    new_im = Image.new('RGBA', (w1, h1), (255, 255, 255))

    # The width and height of the new image
    w, h = new_im.size

    # Iterate through a grid, to place the background tile
    for i in xrange(0, w, bg_w):
        for j in xrange(0, h, bg_h):
            # Change brightness of the images, just to emphasise they are unique copies
            bg = Image.eval(bg, lambda x: x + (i + j) / 1000)

            # paste the image at location i, j:
            new_im.paste(bg, (i, j))

    new_im.save('temp/demo.png')

    # 平铺后的花型存入new_im
    # 开始扭曲
    # 图形扭曲参数
    '''
    params = [1 - float(random.randint(1, 2)) / 100,
              0,
              0,
              0,
              1 - float(random.randint(1, 10)) / 100,
              float(random.randint(1, 2)) / 500,
              0.001,
              float(random.randint(1, 2)) / 500
              ]
    new_im = new_im.transform((w, h), Image.PERSPECTIVE, params)  # 创建扭曲

    new_im = new_im.filter(ImageFilter.EDGE_ENHANCE_MORE)  # 滤镜
    '''
    # 开始合并

    target = Image.new('RGB', (w1, h1), (255, 255, 255, 0))
    target.paste(im_ori, (0, 0))

    im1 = ImageChops.multiply(im_mask1, new_im)
    im2 = ImageChops.multiply(im_mask2, new_im.rotate(20))

    a = im1.split()[3]
    # a = a.point(lambda i: i > 0 and 204)
    target.paste(im1, (0, 0), mask=a)
    b = im2.split()[3]
    target.paste(im2, (0, 0), mask=b)


    target.save("temp/last.png")



test()