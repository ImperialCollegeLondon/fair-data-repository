"""Additional views."""

from flask import Blueprint
from jinja2 import ChoiceLoader


#
# Registration
#
def create_blueprint(app):
    """Register blueprint routes on app."""
    blueprint = Blueprint(
        "ic_data_repo",
        __name__,
        template_folder="./templates",
    )

    app.jinja_loader = ChoiceLoader(
        [
            blueprint.jinja_loader,
            app.jinja_loader,
        ]
    )

    # Add URL rules
    return blueprint
