# jupyter-rest-api
Simple reverse proxy to execute Jupyter notebooks on a remove host.

## requirements
- redis server
1. `pip install celery`
2. `pip install redis`

## Usage
1. `nohup celery worker -A app.celery --loglevel=info &`
2. `export FLASK_APP=run.py`
3. `nohup flask run &`


### Execute a notebook
POST JSON request to localhost:5000/execute

Requires notebook_filename.

Optional working_dir.

Returns 202 if task is successfully scheduled on celery. 
Location response header specifies the url to poll for task updates.

400 response codes indicate errors executing a notebook.

500 response codes indicate errors within the Flask API.