# -*- coding:utf-8 -*-
from flask import Flask,jsonify,request,Response
from flask_sqlalchemy import SQLAlchemy
import pymysql
import math
from datetime import datetime
from PIL import Image,ImageChops,ImageFilter
import numpy as np
import uuid
import os
import time
import random
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO
from gevent import monkey
from gevent import pywsgi

monkey.patch_all()

app = Flask(__name__)

# 配置连接mysql数据库
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://sql_47_99_169_10:WPjh26BsehXAPEyD@127.0.0.1:3306/sql_47_99_169_10"
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['JSON_AS_ASCII'] = False

db = SQLAlchemy(app)

serverPath='https://puzi.thyme.ink'
modelsId=["1799","1797","1666","1715","1801","1716","1717","1781","1791","1792","1794","1795","1796","1798","1800"]

class patternBook(db.Model):
    __tablename__ = 'pattern_info'
    pattern_id = db.Column(db.Integer, autoincrement = True,primary_key=True)
    pattern_no = db.Column(db.String(50), nullable = False)
    pattern_desc=db.Column(db.String(50))
    pattern_class=db.Column(db.String(50))
    pattern_url=db.Column(db.String(200),nullable=False)
    pattern_status=db.Column(db.Integer,default=1,nullable=False)
    indate=db.Column(db.TIMESTAMP, nullable=False, default=datetime.now)

    def to_json(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        return dict

    def toJson(self):
        return {
            "id":str(self.pattern_id),
            'height':0,
            "pic":serverPath+'/static/images/'+self.pattern_url
        }
    def toJsonok(self):
        return {
            "id":str(self.pattern_id),
            'desc':str(self.pattern_no),
            "imgUrl":serverPath+'/static/images/'+self.pattern_url
        }

    def __repr__(self):
        return "<patternBook %r>" % (self.pattern_no)

#db.drop_all() # 先删除再创建
# 创建数据表
db.create_all()
@app.route("/collection",methods=["POST"])
def collection():
    if request.method == 'POST':
        list = request.form.getlist("list")
        #print type(list)
        #print list
        if (len(list) == 0):
           return jsonify(code=204, status=4, message='err', data={})
        else:
            ##query = session.query(User).filter(User.id.in_([2, 3, 4, 5]))
            mylist = ["2", "3", "4", "5"]
            # print type(mylist)
            query = db.session.query(patternBook)
            query = query.filter(patternBook.pattern_id.in_(mylist))
            query = query.order_by(patternBook.pattern_id.desc()).all()
            #print query

            return jsonify(code=200, status=0, message='success', data={})



@app.route('/info/<int:id>/')
def info(id):

    query = db.session.query(patternBook)
    query=query.filter(patternBook.pattern_id == id).all()
    #print type(query)
    list=query
    #print list
    if(len(list)==0):
        return jsonify(code=204, status=4, message='err', data={})
    else:
        result=[]
        for n in list:
            result.append(n.to_json())
        #print  result
        #print type(result[0])
        #for key in result[0]:
        #    print key, result[0][key]
        #print type(str(result[0]['pattern_no']))#该id对应的花型号

        ##开始拼接demoUrls
        arr = []
        for each in ["1799","1797"]:
           arr.append(serverPath+"/test?model_id=" + each + "&pattern_no=" + str(result[0]['pattern_no']) + "&zoom=50")
        #arr.append("/img?model_id=1799&pattern_no=" + str(result[0]['pattern_no']) + "&zoom=50")
        #print arr
        ##拼接完毕
        ##开始存入result
        result[0]["imgUrls"] = arr
       # print result

        return jsonify(code=200, status=0, message='success', data=result)

@app.route('/pagesize/<int:id>/')
def homeok(id):
    page_index=id
    page_size=7

    sum=db.session.query(patternBook).count()
    x=math.ceil(float(sum)/page_size)
    if page_index>x or page_index<=0:
        return jsonify(code=204, status=4, message='err', data={})

    query=db.session.query(patternBook)
    query=query.order_by(patternBook.pattern_id.desc())
    query=query.limit(page_size).offset((page_index-1)*page_size)
   # query=query.paginate(int(page_index), int(page_size), False)
    patternList=query


    result = []
    for n in patternList:
        result.append(n.toJsonok())

    #print 'type data:',type(result)

    return jsonify(code=200, status=0, message='success', data=result)



@app.route('/page/<int:id>/')
def home(id):
    page_index=id
    page_size=7

    sum=db.session.query(patternBook).count()
    x=math.ceil(float(sum)/page_size)
    if page_index>x or page_index<=0:
        return jsonify(code=204, status=4, message='err', data={})

    query=db.session.query(patternBook)
    query=query.order_by(patternBook.pattern_id.desc())
    query=query.limit(page_size).offset((page_index-1)*page_size)
    patternList=query


    result = []
    for n in patternList:
        result.append(n.toJson())

    return jsonify(code=200, status=0, message='success', data=result)

#---图片处理程序开始---
def quad_as_rect(quad):
    if quad[0] != quad[2]: return False
    if quad[1] != quad[7]: return False
    if quad[4] != quad[6]: return False
    if quad[3] != quad[5]: return False
    return True

def quad_to_rect(quad):
    assert(len(quad) == 8)
    assert(quad_as_rect(quad))
    return (quad[0], quad[1], quad[4], quad[3])

def rect_to_quad(rect):
    assert(len(rect) == 4)
    return (rect[0], rect[1], rect[0], rect[3], rect[2], rect[3], rect[2], rect[1])

def shape_to_rect(shape):
    assert(len(shape) == 2)
    return (0, 0, shape[0], shape[1])

def griddify(rect, w_div, h_div):
    w = rect[2] - rect[0]
    h = rect[3] - rect[1]
    x_step = w / float(w_div)
    y_step = h / float(h_div)
    y = rect[1]
    grid_vertex_matrix = []
    for _ in range(h_div + 1):
        grid_vertex_matrix.append([])
        x = rect[0]
        for _ in range(w_div + 1):
            grid_vertex_matrix[-1].append([int(x), int(y)])
            x += x_step
        y += y_step
    grid = np.array(grid_vertex_matrix)
    return grid

def distort_grid(org_grid, max_shift):
    new_grid = np.copy(org_grid)
    x_min = np.min(new_grid[:, :, 0])
    y_min = np.min(new_grid[:, :, 1])
    x_max = np.max(new_grid[:, :, 0])
    y_max = np.max(new_grid[:, :, 1])
    new_grid += np.random.randint(- max_shift, max_shift + 1, new_grid.shape)
    new_grid[:, :, 0] = np.maximum(x_min, new_grid[:, :, 0])
    new_grid[:, :, 1] = np.maximum(y_min, new_grid[:, :, 1])
    new_grid[:, :, 0] = np.minimum(x_max, new_grid[:, :, 0])
    new_grid[:, :, 1] = np.minimum(y_max, new_grid[:, :, 1])
    return new_grid

def grid_to_mesh(src_grid, dst_grid):
    assert(src_grid.shape == dst_grid.shape)
    mesh = []
    for i in range(src_grid.shape[0] - 1):
        for j in range(src_grid.shape[1] - 1):
            src_quad = [src_grid[i    , j    , 0], src_grid[i    , j    , 1],
                        src_grid[i + 1, j    , 0], src_grid[i + 1, j    , 1],
                        src_grid[i + 1, j + 1, 0], src_grid[i + 1, j + 1, 1],
                        src_grid[i    , j + 1, 0], src_grid[i    , j + 1, 1]]
            dst_quad = [dst_grid[i    , j    , 0], dst_grid[i    , j    , 1],
                        dst_grid[i + 1, j    , 0], dst_grid[i + 1, j    , 1],
                        dst_grid[i + 1, j + 1, 0], dst_grid[i + 1, j + 1, 1],
                        dst_grid[i    , j + 1, 0], dst_grid[i    , j + 1, 1]]
            dst_rect = quad_to_rect(dst_quad)
            mesh.append([dst_rect, src_quad])
    return mesh

def render(image):

    dst_grid = griddify(shape_to_rect(image.size), 4, 4)
    src_grid = distort_grid(dst_grid, 50) #修改扭曲参数
    mesh = grid_to_mesh(src_grid, dst_grid)
    return image.transform(image.size, Image.MESH,mesh, Image.BILINEAR)

def repeat_hx(bg,w1,h1):

    # The width and height of the background tile
    bg_w, bg_h = bg.size

    # Creates a new empty image, RGB mode, and size 1000 by 1000
    new_im = Image.new('RGBA', (w1, h1),(255, 255, 255))

    # The width and height of the new imageƒ
    w, h = new_im.size

    # Iterate through a grid, to place the background tile
    for i in xrange(0, w, bg_w):
        for j in xrange(0, h, bg_h):
            # Change brightness of the images, just to emphasise they are unique copies
            bg = Image.eval(bg, lambda x: x + (i + j) / 1000)

            # paste the image at location i, j:
            new_im.paste(bg, (i, j))

    uuid_tmp = uuid.uuid4()
    tmp_file_name = 'temp/tmprepeat_%s.png' % uuid_tmp
    new_im.save(tmp_file_name)
    return new_im



def mix(model_id,pattern_no,zoom_num):
    ori_im = Image.open('static/models/' + model_id + 'a.png')
    # mask_im=Image.open('images/'+str(folder)+'/'+str(model_id)+'b.png')
    mask1_im = Image.open('static/models/'  + model_id + 'c.png')
    mask2_im = Image.open('static/models/'  + model_id + 'd.png')
    pattern = Image.open('static/images/' + pattern_no+ '.png')

    w1, h1 = ori_im.size
    w2, h2 = pattern.size

    w2 = w2 * zoom_num / 100
    h2 = h2 * zoom_num / 100

    bg = pattern.resize((w2, h2), Image.ANTIALIAS)
    pattern_im = repeat_hx(bg, w1, h1)  # 平铺
    pattern_im = render(pattern_im)  # 扭曲

    target = Image.new('RGB', (w1, h1), (255, 255, 255, 0))
    target.paste(ori_im, (0, 0))

    im1 = ImageChops.multiply(mask1_im, pattern_im)
    im2 = ImageChops.multiply(mask2_im, pattern_im.rotate(20))

    a = im1.split()[3]
    # a = a.point(lambda i: i > 0 and 204)
    target.paste(im1, (0, 0), mask=a)
    b = im2.split()[3]
    target.paste(im2, (0, 0), mask=b)

    uuid_str1 = uuid.uuid4()
    tmp_file_name1 = 'temp/tmptarget_%s.jpg' % uuid_str1
    target.save(tmp_file_name1)
    return tmp_file_name1


@app.route("/img",methods=['post','get'])
def index():

    if request.method == 'GET':
       model_id=str(request.args.get('model_id'))
       pattern_no=str(request.args.get('pattern_no'))
       zoom_num=int(request.args.get("zoom"))


       if str(model_id) not in modelsId or zoom_num<20 or zoom_num>200:
          return "默认404图片"
       else:
          name= mix(model_id, pattern_no, zoom_num)
          image = file(name)
          resp = Response(image, mimetype="image/jpeg")
          return resp


'''
重写图片处理程序，关键是花型缩放部分
'''
@app.route("/test",methods=['get'])
def test():

    #获取传递值
    if request.method=='GET':
        model_id = str(request.args.get('model_id'))
        pattern_no = str(request.args.get('pattern_no'))
        zoom_num = int(request.args.get("zoom"))

        modelPath='static/models/'+model_id
        patternPath='static/images/'+pattern_no+'.png'

        #判断是否存在
        if model_id not in modelsId or zoom_num<30 or zoom_num>250:
            return "模特图片不存在或者缩放超范围"
        elif not os.path.exists(patternPath):
            return "花型图片不存在"
        else:
            #开始处理图片
            im_ori = Image.open(modelPath + 'a.png')
            im_mask1=Image.open(modelPath + 'c.png')
            im_mask2 = Image.open(modelPath + 'd.png')
            im_pattern=Image.open(patternPath)

            w1, h1 = im_ori.size
            w2, h2 = im_pattern.size

            # 花型缩放
            if zoom_num==100:
                bg = im_pattern.resize((w2, h2), Image.ANTIALIAS)
            else:
                w2 = w2 * zoom_num / 100
                h2 = h2 * zoom_num / 100
                bg = im_pattern.resize((w2, h2), Image.ANTIALIAS)

            # The width and height of the background tile
            bg_w, bg_h = bg.size

            # Creates a new empty image, RGB mode,
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

            #平铺后的花型存入new_im
            #开始扭曲


            #开始合并

            target = Image.new('RGB', (w1, h1), (255, 255, 255, 0))
            target.paste(im_ori, (0, 0))

            im1 = ImageChops.multiply(im_mask1, new_im)
            im2 = ImageChops.multiply(im_mask2, new_im.rotate(20))

            a = im1.split()[3]
            #a = a.point(lambda i: i > 0 and 204)
            target.paste(im1, (0, 0), mask=a)
            b = im2.split()[3]
            target.paste(im2, (0, 0), mask=b)

            buf = StringIO.StringIO()
            target.save(buf, 'JPEG', quality=70)
            buf_str = buf.getvalue()
            response = app.make_response(buf_str)
            response.headers['Content-Type'] = 'image/jpeg'
            return response
            target.close()
            im1.close()
            im2.close()
            new_im.close()
            im_ori.close()
            im_mask1.close()
            im_mask2.close()
            im_pattern.close()


            #uuid_str1 = uuid.uuid4()
            #tmp_file_name1 = 'temp/tmptarget_%s.jpg' % uuid_str1

            #target.save(tmp_file_name1)

            #image = file(tmp_file_name1)
            # resp = Response(image, mimetype="image/jpeg")
            # return resp

@app.route('/')
def hello_world():
    return '新测试'


if __name__ == '__main__':


    app.run(
        #host='0.0.0.0',
        #port=9000
     )

