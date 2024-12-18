@echo off

echo #1. update models.py
REM python manage.py inspectdb > fotd/models.py

echo #2. create migrations for model changes
python manage.py makemigrations fotd
python manage.py makemigrations tracker
python manage.py makemigrations link

echo #3. apply changes to db
python manage.py migrate
pause

echo # run tests
python manage.py test fotd
python manage.py test tracker
python manage.py test link

echo # start the app
python manage.py runserver
