#!/Users/ckirby/.virtualenvs/tv_failure_recognition/bin/python
from app import app

if __name__ == 'main':
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(debug=True)
