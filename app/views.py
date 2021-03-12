from app import app, celery#, models, login_manager #, damien, predict
import config
from flask import render_template, request, redirect, abort, flash, jsonify, url_for
# from flask_login import login_user, login_required, current_user
import json, os
# from werkzeug.utils import secure_filename
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor


@app.route('/execute', methods=['POST'])
def index():
    data = request.get_json()
    # return request.data
    print(request)
    print(data)
    notebook_filename = data['notebook_filename']
    working_dir = data.get('working_directory')

    task = run_notebook.apply_async([notebook_filename, working_dir])
    return jsonify({'state': 'PENDING',}), 202, {'Location': url_for('taskstatus', task_id=task.id)}


@celery.task(bind=True)
def run_notebook(self, notebook_filename, working_dir):
    with open(os.path.join(config.NOTEBOOK_ROOT, notebook_filename)) as f:
        nb = nbformat.read(f, as_version=4)
        ep = ExecutePreprocessor(timeout=21600, kernel_name=nb['metadata']['kernelspec']['name'])

        self.update_state(state='PROGRESS', meta={'status': 'Notebook executing'})
        if working_dir:
            ep.preprocess(nb, {'metadata': {'path': working_dir}})
        else:
            ep.preprocess(nb, {'metadata': {'path': config.NOTEBOOK_ROOT}})

    return {'status': 'Task finished'}


@app.route('/status/<task_id>')
def taskstatus(task_id):
    task = run_notebook.AsyncResult(task_id)

    if task.state == 'PENDING':
        # job did not start yet
        response = {
            'state': task.state,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)


@app.route('/health')
def health_check():
    """
    Adding as part of status fail on load balancer in long-running task so that status always healthy.
    :return: Static JSON
    :rtype: Dictionary
    """
    return {'msg': 'Healthy'}