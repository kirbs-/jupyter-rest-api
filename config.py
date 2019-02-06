import os
basedir = os.path.abspath(os.path.dirname(__file__))

# SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'database', 'app.db')
# SQLALCHEMY_DATABASE_URI = 'postgresql://kirby:grad2002@brains.lan/grumpy'
# SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'database', 'migrations')
OTP_SECRET = 'abc'
DEBUG = True

UPLOAD_FOLDER = '/Users/ckirby/PycharmProjects/tv_failure_recognition/app/static'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
NOTEBOOK_ROOT = '/Users/ckirby/Documents/iPython'