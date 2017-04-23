# afterships

This branch is used for hosting source of GAE project - afterships.

pip install -t lib -r requirements.txt

dev_appserver.py ./


# This will deploy to the app engine but not updating the source hosting

appcfg.py -A afterships -V 2  update ./


afterships.appspot.com

#From gcloud console:

dev_appserver.py ./

gcloud preview app deploy ./app.yaml --version 1

#TODO

Time zone problem when doing the diff


