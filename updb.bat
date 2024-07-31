@echo off
echo #1. pls update models.py first
pause

echo #2. create migrations for model changes
python manage.py makemigrations fotd
python manage.py makemigrations tracker

echo #3. apply changes to db
python manage.py migrate
pause

echo # start the app
python manage.py runserver
