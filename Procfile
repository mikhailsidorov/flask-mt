web: pip install -r app/requirements.txt;flask db upgrade; flask translate compile; cd app; gunicorn microblog:app;
worker: rq worker microblog-tasks
