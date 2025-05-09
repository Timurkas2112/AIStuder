from .create_and_edit_routes import creator
from .log_routes import log
from .view_routes import viewer
# Добавляй другие blueprints по мере надобности

def register_blueprints(app):
    app.register_blueprint(creator)
    app.register_blueprint(log)
    app.register_blueprint(viewer)