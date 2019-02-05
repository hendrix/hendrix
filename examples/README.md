## to run the examples

* Have pipenv installed

* cd into root hendrix folder (same folder as Pipfile and Pipfile.lock)

 ```
 cd <folder containing hendrix>/hendrix  
 ```


* Use pipenv to install all required dependencies for development: 

 ```
 pipenv sync --dev 
 ```

* Export PYTHONPATH folder so the projects can see the hendrix source
 
 ```
 export PYTHONPATH=<folder containing hendrix>/hendrix  
 ```

* Load the virtual environment

```
 pipenv shell   
 ```

* cd to one of the demo projects (django_hx_chatserver used as example)

```
 cd <folder containing hendrix>/examples/django_hx_chatserver/example_app
 ```

* create django database

```
 python manage.py migrate --noinput --run-syncdb
 ```

* collect django static files
```
 python manage.py collectstatic
 ```

* run the application
```
 python run.py
 ```

* navigate a browser to http://localhost:7575 (use two tabs for django_hx_chatserver)
