release: python manage.py migrate --noinput
web: gunicorn landuse_project.wsgi --log-file -
worker: python manage.py run_balance_worker --sleep 0.2
