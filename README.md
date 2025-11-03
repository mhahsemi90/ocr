python -m venv venv
source venv/bin/activate
cd .\ocr_project\
python manage.py makemigrations
python manage.py migrate
python manage.py create_default_user
python manage.py ocr_worker
python manage.py runserver

offline install:\
source venv/bin/activate
cd .\ocr_project\
pip freeze > requirements.txt
pip wheel -r requirements.txt -w offline_wheels
python create_offline_package.py
python install.py
python manage.py create_default_user
python manage.py ocr_worker
python manage.py runserver