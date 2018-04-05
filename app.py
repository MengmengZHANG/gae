#!/usr/bin/env python
# -*- coding: utf-8 -*-
# import pdb; pdb.set_trace();
from flask import Flask, url_for, redirect, render_template, request, g, jsonify,json, send_from_directory
from google.appengine.ext import ndb
import datetime,collections
import requests, sys
import traceback
from pytz import timezone
import pytz
import logging
#import requests_toolbelt.adapters.appengine
from google.appengine.api import urlfetch

# https://cloud.google.com/appengine/docs/standard/python/issue-requests
# Use the App Engine Requests adapter. This makes sure that Requests uses
# URLFetch.
# requests_toolbelt.adapters.appengine.monkeypatch()
urlfetch.set_default_fetch_deadline(600)

reload(sys)  
sys.setdefaultencoding('utf8')

app = Flask(__name__)

#global variables
dateTimeFormat = '%Y-%m-%d %H:%M:%S'
dateFormat = '%Y-%m-%d'
dateTimeTzFormat = '%Y-%m-%d %H:%M:%S %Z%z'
beijingTz = timezone('Asia/Shanghai')
parisTz = timezone('Europe/Paris')

# Create user model.
# 2016-04-10 14:37:12
class Courier(ndb.Model):
    customer = ndb.StringProperty(indexed=False)
    destination = ndb.StringProperty(indexed=False)
    trackingNumber = ndb.StringProperty(indexed=False)
    slug = ndb.StringProperty(indexed=False)
    createdDate = ndb.DateTimeProperty(auto_now_add=True, indexed=True) #utc time
    arrived = ndb.BooleanProperty(default=False, indexed=True)

class Parameter(ndb.Model):
    name = ndb.StringProperty(indexed=True)
    value = ndb.StringProperty(indexed=False)

class Shipping(ndb.Model):
    index = ndb.IntegerProperty(indexed=True)
    trackingNumber = ndb.StringProperty(indexed=True)
    dateTime = ndb.DateTimeProperty(indexed=False) #utc time
    description =  ndb.StringProperty(indexed=False)

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
        if total == 0:
            return jsonify(offset=0,total=0,lastUpdate='0 second',records=[])
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
        lastUpate = None
        if lastUpdateParam is not None:
            dt = datetime.datetime.now() - datetime.datetime.strptime(lastUpdateParam.value, dateTimeFormat)
            lastUpdate = humanize_time(dt.total_seconds())
            # print "Last update (" + now.strftime("%Y-%m-%d %H:%M:%S") + " -> " + lastUpdateParam.value
            # print diffSeconds

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

            lastStatus = Shipping.query(Shipping.trackingNumber == courier.trackingNumber, Shipping.index ==0).get()
            now = datetime.datetime.now()
            if lastStatus is not None:
                print courier.trackingNumber
                print '\t' + str(now)
                print '\t' + str(lastStatus.dateTime)
                dt = ( now - lastStatus.dateTime).total_seconds()
                print '\tlastUpdate ' + str(dt) + ' seconds ago'
                lastStatusDateHumanReadable = humanize_time(dt)
                courierDic['lastStatusDate'] = lastStatusDateHumanReadable + ' ago'
                courierDic['lastStatus'] = lastStatus.description
            courierDic['createdDate'] = humanize_time((now -courier.createdDate).total_seconds()) + ' ago'
            objects_list.append(courierDic)
        result = jsonify(offset=offset,total=total,lastUpdate=lastUpdate,records=objects_list)
    except Exception,e:
        # traceback.print_exc()
        logging.error(traceback.format_exc())
    # return render_template('index.html',couriers=objects_list)
    return result

@app.route("/track/add")
def add():
    courier = Courier()
    courier.customer = request.args.get('customer');
    courier.destination = request.args.get('destination')
    courier.trackingNumber = request.args.get('trackingNumber')
    courier.slug = request.args.get('slug')
    # dateStr = request.args.get('date')
    # print dateStr
    # if dateStr is not None:
    #     print datetime.datetime.strptime(dateStr, dateTimeFormat)
    # 	courier.createdDate = datetime.datetime.strptime(dateStr, dateTimeFormat)
    #     print courier
    #     print courier.createdDate
    if courier.trackingNumber and courier.slug:
        courier.put()
        return redirect(url_for('track'))
    else:
        return "Information not completed!"

@app.route("/track/delete")
def delete():
    urlSafe = request.args.get('key')
    print urlSafe
    courier = ndb.Key(urlsafe=urlSafe).get()
    if courier:
        print "found" + urlSafe
        courier.key.delete()
        return redirect(url_for('track'))
        # return 'OK'

@app.route("/track/update")
def updateShipping():

    lastUpdateParam = Parameter.query(Parameter.name == 'lastUpdate').get();
    lastUpate = None
    #if lastUpdateParam is not None:
    #    now = datetime.datetime.now()
    #    dt = now - datetime.datetime.strptime(lastUpdateParam.value, dateTimeFormat)
    #    diffSeconds = dt.total_seconds()
    #    if diffSeconds < 60:
    #        return "request too frequently, please wait for at least 1 minute"


    courriers = Courier.query().order(-Courier.createdDate).fetch(50)
    for courrier in courriers:
        if courrier.arrived == True:
            continue
        trackingNumber = courrier.trackingNumber
        print trackingNumber
        url = "http://m.kuaidi100.com/query?type=" + courrier.slug + "&postid=" + trackingNumber
        # response = requests.get(url)
        # json = response.json()
        result = urlfetch.fetch(url).content
        jsonResult = json.loads(result)
        if jsonResult['status'] != "200":
            continue
        shippings = Shipping.query(Shipping.trackingNumber == trackingNumber).fetch()
        for shipping in shippings:
            shipping.key.delete()
        
        i = 0
        for leg in jsonResult['data']:
            shipping = Shipping()   
            shipping.index = i
            shipping.trackingNumber = trackingNumber
            naive = datetime.datetime.strptime(leg['time'], dateTimeFormat) #beijing time in native datetime
            shipping.dateTime =  naive.replace(tzinfo=beijingTz).astimezone(pytz.utc).replace(tzinfo=None) #no daylight saving problem, no need localize method
            shipping.description = leg['context']
            shipping.put()
            if "投递并签收" in shipping.description:
                courrier.arrived = True
                courrier.put()
            i -= 1
    
    lastUpdate = Parameter.query(Parameter.name == "lastUpdate").get();
    if lastUpdate is None:
        lastUpdate = Parameter()
        lastUpdate.name = "lastUpdate"
    lastUpdate.value = datetime.datetime.now().strftime(dateTimeFormat) #utc time
    lastUpdate.put()
    return "ok"

def humanize_time(amount, units = 'seconds'):    

    def process_time(amount, units):

        INTERVALS = [   1, 60, 
                        60*60, 
                        60*60*24, 
                        60*60*24*7, 
                        60*60*24*7*4, 
                        60*60*24*7*4*12, 
                        60*60*24*7*4*12*100,
                        60*60*24*7*4*12*100*10]
        NAMES = [('second', 'seconds'),
                 ('minute', 'minutes'),
                 ('hour', 'hours'),
                 ('day', 'days'),
                 ('week', 'weeks'),
                 ('month', 'months'),
                 ('year', 'years'),
                 ('century', 'centuries'),
                 ('millennium', 'millennia')]

        result = []

        unit = map(lambda a: a[1], NAMES).index(units)
        # Convert to seconds
        amount = amount * INTERVALS[unit]

        for i in range(len(NAMES)-1, -1, -1):
            a = amount // INTERVALS[i]
            if a > 0: 
                result.append( (a, NAMES[i][1 % a]) )
                amount -= a * INTERVALS[i]

        return result
    if amount <0:
        return amount + " " + units
    rd = process_time(int(amount), units)
    cont = 0
    for u in rd:
        if u[0] > 0:
            cont += 1

    # buf = ''
    # i = 0
    # for u in rd:
    #     if u[0] > 0:
    #         buf += "%d %s" % (u[0], u[1])
    #         cont -= 1

    #     if i < (len(rd)-1):
    #         if cont > 1:
    #             buf += ", "
    #         else:
    #             buf += " and "

    #     i += 1
    buf = "%d %s" % (rd[0][0], rd[0][1]) 
    return buf
    

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080)


