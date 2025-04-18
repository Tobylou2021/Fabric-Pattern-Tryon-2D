# -*- coding:utf-8 -*-
import os
from PIL import Image

def processImage(filesoure, destsoure, name,prefix):
    '''
    filesoure是存放待转换图片的目录
    destsoure是存在输出转换后图片的目录
    name是文件名
    imgtype是文件类型
    '''

    im = Image.open(filesoure + name)
    #缩放比例
    rate =max(im.size[0]/320.0 if im.size[0] > 30 else 0, im.size[1]/568.0 if im.size[1] > 568 else 0)
    if rate:
        im.thumbnail((im.size[0]/rate, im.size[1]/rate))
    im.save(destsoure + '%s.png' % prefix)

def alter(disPath,outPath):
    #切换到源目录，遍历源目录下所有图片
    s = os.listdir(disPath)
    for i in s:
        #检查后缀
        postfix = os.path.splitext(i)[1]
        ##前缀
        prefix = os.path.splitext(i)[0]
        processImage(disPath, outPath, i,prefix)
    return "finish"

print  alter('dist/','out/')