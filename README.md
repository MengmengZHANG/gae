# afterships

https://console.cloud.google.com/appengine/versions?project=afterships&serviceId=default&versionssize=50

1) install gcloud and do initalization

https://cloud.google.com/appengine/docs/standard/python/download

https://cloud.google.com/sdk/docs/quickstart-windows

2) local dev and testing

https://cloud.google.com/appengine/docs/standard/python/quickstart

pip install -t lib -r requirements.txt

dev_appserver.py ./

2.5) for pycharm to recognize the 3rd party libraries

Add the two following path to settings->project settings-> Project Interpreter->config

C:\Users\username\AppData\Local\Google\Cloud SDK\google-cloud-sdk\platform\google_appengine

./lib

3) deploy to cloud

# This will deploy to the app engine but not updating the source hosting

gcloud app deploy

gcloud app browse

afterships.appspot.com

#TODO

Time zone problem when doing the diff


