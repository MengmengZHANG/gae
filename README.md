# afterships

This branch is used for hosting source of GAE project - afterships.

pip install -t lib -r requirements.txt

dev_appserver.py gae/


# This will deploy to the app engine but not updating the source hosting

appcfg.py -A afterships -V 1  update gae/


afterships.appspot.com


