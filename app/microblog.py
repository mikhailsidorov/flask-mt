import os
import rpdb

if os.environ.get('FLASK_DEBUG') == '1':
    rpdb.Rpdb(addr='0.0.0.0').set_trace()

from app import create_app, db, cli
from app.models import User, Post, Message, Notification, Task


app = create_app()
cli.register(app)


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post, 'Message': Message, 'Notification': Notification, 'Task': Task}


if __name__ == '__main__':
    app.run()
