from app import app, celery#, models, login_manager #, damien, predict
import config
from flask import render_template, request, redirect, abort, flash, jsonify, url_for
# from flask_login import login_user, login_required, current_user
import json, os
# from werkzeug.utils import secure_filename
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
import subprocess
import logging
import platform
import re


def escape_ansi(line):
    line = bytes(line, 'utf-8').decode("unicode_escape")
    ansi_escape =re.compile(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]')
    return ansi_escape.sub('', line).splitlines()


class TrackableExecutePreprocessor(ExecutePreprocessor):

    def __init__(self, **kw):
        self.task = kw.get('task')
        self.tmp_meta = kw.get('meta')
        ExecutePreprocessor.__init__(self, **kw)

    def preprocess_cell(self, cell, resources, index):
        cell, self.resources = super().preprocess_cell(cell, resources, index)
        logging.debug(f'Cell: {cell}')
        logging.info(type(cell))
        logging.debug(self.tmp_meta)
        logging.info(cell.outputs)
        if cell.outputs:
            logging.info(type(cell.outputs[0]))
        if self.tmp_meta['cell_results']:
            logging.info('has content')
            self.tmp_meta['cell_results'] += [out.text for out in cell.outputs]
        else:
            logging.info('called first')
            self.tmp_meta['cell_results'] = [out.text for out in cell.outputs]
        self.tmp_meta['index'] = index

        self.task.update_state(state='PROGRESS', meta=self.tmp_meta)

def run(cmd):
    """
    Executes the provided command and captures all response messages.

    Returns:
        JSON parsed response if available; otherwise raw responseself.

    """
    try:
        logging.debug(' '.join(cmd))
        if platform.system() == 'Darwin':
            res = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        elif platform.system() == 'Linux':
            res = subprocess.check_output(' '.join(cmd), stderr=subprocess.STDOUT, shell=True)
        else:
            res = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
        try:
            return json.loads(res)
        except:
            return res
    except subprocess.CalledProcessError as e:
        logging.debug('Execption running command!')
        logging.debug(e.output.decode())
        return escape_ansi(e.output.decode())


def install_requirements(self, environ_name, requirements_filename):
    self.update_state(state="INSTALLING_DEPENDENCIES", meta={'dependency_status': f'Activating pyenv environment {environ_name}'})
    cmd = ['pyenv', 'local', environ_name]
    logging.debug(f"Activation command result: {run(cmd)}")
    self.update_state(state="INSTALLING_DEPENDENCIES", meta={'dependency_status': f'Executing pip install from file {requirements_filename}'})

    cmd = ['$(pyenv which pip)', 'install', '-r', requirements_filename]
    res = run(cmd)
    self.update_state(state="DEPENDENCIES_INSTALLED", meta={'dependency_status': res})
    logging.debug(f"pip install result: {res}")

    return res


@app.route('/execute', methods=['POST'])
def index():
    data = request.get_json()
    # return request.data
    print(request)
    print(data)
    notebook_filename = data['notebook_filename']
    working_dir = data.get('working_directory')
    requirements_filename = data.get('requirements_filename')

    task = run_notebook.apply_async([notebook_filename, working_dir, requirements_filename])
    return jsonify({'state': 'PENDING',}), 202, {'Location': url_for('taskstatus', task_id=task.id)}


@celery.task(bind=True)
def run_notebook(self, notebook_filename, working_dir, requirements_filename):
    if not working_dir:
        working_dir = config.NOTEBOOK_ROOT

    with open(os.path.join(working_dir, notebook_filename)) as f:
        nb = nbformat.read(f, as_version=4)
        meta =  {'cell_results': list(), 'cell_cnt': len(nb.cells)}
        res = 'n/a'

        # install dependencies if present
        if requirements_filename:
            res = install_requirements(self, nb['metadata']['kernelspec']['display_name'], os.path.join(working_dir, requirements_filename))

        meta['status'] = 'Notebook executing'
        meta['dependency_status'] = res

        self.update_state(state='PROGRESS', meta=meta)
        ep = TrackableExecutePreprocessor(task=self, meta=meta, timeout=172800, kernel_name=nb['metadata']['kernelspec']['name'])
        try:
            if working_dir:
                nb_result = ep.preprocess(nb, {'metadata': {'path': working_dir}})
            else:
                nb_result = ep.preprocess(nb, {'metadata': {'path': config.NOTEBOOK_ROOT}})
            logging.info(nb_result)
            return {'status': 'Task finished', 'dependency_status': meta['dependency_status'], 'cell_results': meta['cell_results'], 'result': nb_result, 'cell_cnt': len(nb.cells), 'index': len(nb.cells)}
        except Exception as e:
            logging.info(f'Notebook exception: {e}')
            return {'status': 'FAILURE', 'dependency_status': meta['dependency_status'], 'cell_results': meta['cell_results'], 'result': escape_ansi(str(e)), 'cell_cnt': len(nb.cells)}

@app.route('/status/<task_id>')
def taskstatus(task_id):
    task = run_notebook.AsyncResult(task_id)

    if task.state == 'PENDING':
        # job did not start yet
        response = {
            'state': task.state,
            'status': 'Pending...'
        }
    elif task.state == 'SUCCESS' and task.status.get('status') == 'FAILURE':
        response = {
            'state': 'FAILURE',
            'status': task.info.get('result'),  # this is the exception raised
            'dependecy_status': task.info.get('dependency_status', ''),
            'cell_results': str(task.info.get('cell_results', '')),
            'index': str(task.info.get('index', '')),
            'cell_cnt': str(task.info.get('cell_cnt', ''))
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'status': task.info.get('status', ''),
            'dependecy_status': task.info.get('dependency_status', ''),
            'cell_results': str(task.info.get('cell_results', '')),
            # 'index': str(task.info.get('index', '')),
            'cell_cnt': str(task.info.get('cell_cnt', ''))
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'status': task.info.get('result'),  # this is the exception raised
            'dependecy_status': task.info.get('dependency_status', ''),
            'cell_results': str(task.info.get('cell_results', '')),
            'index': str(task.info.get('index', '')),
            'cell_cnt': str(task.info.get('cell_cnt', ''))
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