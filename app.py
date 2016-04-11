#!/usr/bin/env python
# -*- coding: utf-8 -*-
# import pdb; pdb.set_trace();
from flask import Flask
from flask import Flask, url_for, redirect, render_template, request, g, jsonify,json
from google.appengine.ext import ndb
import datetime,collections

app = Flask(__name__)
dateFormat = '%Y-%m-%d %H:%M:%S'

# Create user model.
# 2016-04-10 14:37:12
class Courier(ndb.Model):
    customer = ndb.StringProperty(indexed=False)
    destination = ndb.StringProperty(indexed=False)
    trackingNumber = ndb.StringProperty(indexed=False)
    slug = ndb.StringProperty(indexed=False)
    createdDate = ndb.DateTimeProperty(auto_now_add=True, indexed=True)

@app.route("/")
def index():
    try:
        result =  render_template('index.html')
    except Exception,e: print str(e)
    return result

# from=YYYYMMDD
# to=YYYYMMDD
@app.route("/get")
def get():
    try:
        total = Courier.query().count()
        if request.args.get('limit') is not None:
            limit = int(request.args.get('limit'))
        else:
            limit = 10
        if request.args.get('offset') is not None:
            offset = int(request.args.get('offset'))
        else:
            offset = 0
        if (offset < 0) or (limit < 0):
            return "Please check you input."
        couriers = Courier.query().order(-Courier.createdDate).fetch(limit,offset=offset)
        # couriers = Courier.query().order(-Courier.createdDate)
        # .offset(idxFrom).limit(idxTo)
        objects_list = []
        # pdb.set_trace()
        for courier in couriers:
            courierDic = collections.OrderedDict()
            courierDic['key'] = courier.key.urlsafe()
            courierDic['customer'] = courier.customer
            courierDic['destination'] = courier.destination
            courierDic['trackingNumber'] = courier.trackingNumber
            courierDic['slug'] = courier.slug
            courierDic['createdDate'] = courier.createdDate.strftime(dateFormat)
            objects_list.append(courierDic)
        result = jsonify(offset=offset,total=total,records=objects_list)
    except Exception,e: print str(e)
    # return render_template('index.html',couriers=objects_list)
    return result

@app.route("/add")
def add():
    courier = Courier()
    courier.customer = request.args.get('customer');
    courier.destination = request.args.get('destination')
    courier.trackingNumber = request.args.get('trackingNumber')
    courier.slug = request.args.get('slug')
    dateStr = request.args.get('date')
    print dateStr
    if dateStr is not None:
      	print dateFormat
        print datetime.datetime.strptime(dateStr, dateFormat)
    	courier.createdDate = datetime.datetime.strptime(dateStr, dateFormat)
        print courier
        print courier.createdDate
    if courier.trackingNumber and courier.slug:
        courier.put()
        return redirect(url_for('index'))
    else:
        return "Information not completed!"

@app.route("/delete")
def delete():
    urlSafe = request.args.get('key')
    # print key
    courier = ndb.Key(urlsafe=urlSafe).get()
    if courier:
        courier.key.delete()
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080)
