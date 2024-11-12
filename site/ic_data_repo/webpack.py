"""JS/CSS Webpack bundles for Imperial Fair Data Repository."""

from invenio_assets.webpack import WebpackThemeBundle

theme = WebpackThemeBundle(
    __name__,
    "assets",
    default="semantic-ui",
    themes={
        "semantic-ui": dict(
            entry={
                "optional-role-creatibutors": "./js/ic_data_repo/OptionalRoleCreatibutors.js",  # noqa: E501
                "hidden-field": "./js/ic_data_repo/HiddenField.js",
            },
        ),
    },
)
