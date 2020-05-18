#!/bin/bash

# python manage.py sqlclear app_name | python manage.py dbshell
./manage.py migrate ws zero
./manage.py makemigrations
./manage.py migrate
# ./manage.py createsuperuser
