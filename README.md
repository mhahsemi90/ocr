python -m venv venv
source venv/bin/activate
cd .\ocr_project\
python manage.py makemigrations
python manage.py migrate
python manage.py ocr_worker
python manage.py runserver
