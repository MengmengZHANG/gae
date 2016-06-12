#!/usr/bin/env python
# -*- coding: utf-8 -*-
# import pdb; pdb.set_trace();
from flask import Flask, url_for, redirect, render_template, request, g, jsonify,json, send_from_directory
from google.appengine.ext import ndb
import datetime,collections
import requests, sys

reload(sys)  
sys.setdefaultencoding('utf8')

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
    arrived = ndb.BooleanProperty(default=False, indexed=True)

class Parameter(ndb.Model):
    name = ndb.StringProperty(indexed=True)
    value = ndb.StringProperty(indexed=False)

class Shipping(ndb.Model):
    trackingNumber = ndb.StringProperty(indexed=True)
    dateTime = ndb.DateTimeProperty(indexed=True)
    description =  ndb.StringProperty(indexed=True)

@app.route('/static/<path:path>')
def send_js(path):
    return send_from_directory('static', path)


@app.route("/")
@app.route("/track")
def track():
    try:
        result =  render_template('track.html')
    except Exception,e: print str(e)
    return result


@app.route("/order")
def order():
    try:
        result =  render_template('order.html')
    except Exception,e: print str(e)
    return result

# from=YYYYMMDD
# to=YYYYMMDD
@app.route("/track/get")
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
        lastUpdateParam = Parameter.query(Parameter.name == 'lastUpdate').get();
        lastUpdate = None if lastUpdateParam is None else lastUpdateParam.value;

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
            courierDic['arrived'] = courier.arrived

            lastStatus = Shipping.query(Shipping.trackingNumber == courier.trackingNumber).order(-Shipping.dateTime).get()
            if lastStatus is not None:
                courierDic['lastStatus'] = lastStatus.description
            courierDic['createdDate'] = courier.createdDate.strftime(dateFormat)
            objects_list.append(courierDic)
        result = jsonify(offset=offset,total=total,lastUpdate=lastUpdate,records=objects_list)
    except Exception,e: print str(e)
    # return render_template('index.html',couriers=objects_list)
    return result

@app.route("/track/add")
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
        return redirect(url_for('track'))
    else:
        return "Information not completed!"

@app.route("/track/delete")
def delete():
    urlSafe = request.args.get('key')
    # print key
    courier = ndb.Key(urlsafe=urlSafe).get()
    if courier:
        courier.key.delete()
        return redirect(url_for('track'))

@app.route("/track/update")
def shipping():
    courriers = Courier.query(Courier.arrived == False).fetch();
    for courrier in courriers:
        trackingNumber = courrier.trackingNumber
        url = "http://m.kuaidi100.com/query?type=ems&postid=" + trackingNumber    
        response = requests.get(url)
        json = response.json()
        shippings = Shipping.query(Shipping.trackingNumber == trackingNumber).fetch()
        for shipping in shippings:
            shipping.key.delete()

        for leg in json['data']:
            shipping = Shipping()   
            shipping.trackingNumber = trackingNumber
            shipping.dateTime =  datetime.datetime.strptime(leg['time'], dateFormat)
            shipping.description = leg['context']
            shipping.put()
            if "联纺营业部安排投递" in shipping.description:
                courrier.arrived = True
                courrier.put()
    
    lastUpdate = Parameter.query(Parameter.name == "lastUpdate").get();
    if lastUpdate is None:
        lastUpdate = Parameter()
        lastUpdate.name = "lastUpdate"
    lastUpdate.value = datetime.datetime.now().strftime(dateFormat)
    lastUpdate.put()
    return "ok"

    

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080)


