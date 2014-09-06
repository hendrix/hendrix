virtualenv .
echo "export PYTHONPATH=$PYTHON_PATH:`pwd`/example_app" >> bin/activate
echo "export DJANGO_SETTINGS_MODULE=example_app.settings" >> bin/activate
source bin/activate
pip install -r requirements.txt
cd example_app
./manage.py syncdb --noinput
