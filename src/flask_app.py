from flask import Flask  # render_template
import logging
import os
from dotenv import load_dotenv

from application.flask_router import FlaskRouter
from application.bootstrap.bootstrap import bus

load_dotenv()


def create_app(test_config: dict = None) -> Flask:
    # create and configure the app
    app = Flask(__name__)

    # app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True
    app.json.compact = True

    if test_config is not None:
        app.config.from_mapping(test_config)

    @app.route("/healthcheck")
    def healthcheck():
        return "Everything is golden!"

    # Register Controllers
    router = FlaskRouter(app, bus)
    router.register_routes()
    # controller.clickup_webhook_handler()

    return app


AUTH = os.getenv("AUTH", "False").lower() in ("true", "1")
ENDPOINT = os.environ["ENDPOINT"]
app = create_app()

logger = logging.getLogger("gunicorn.error")

if __name__ == "__main__":
    app.logger.handlers = logger.handlers
    # Level set by gunicorn
    app.logger.setLevel(logger.level)
