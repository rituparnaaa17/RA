import os
from jinja2 import Environment, FileSystemLoader

# Works whether run from backend/ dir or project root with backend.main:app
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")

_env = Environment(loader=FileSystemLoader(os.path.abspath(TEMPLATES_DIR)))


def render_report(template_name: str, context: dict) -> str:
    """Render a Jinja2 template with the given context, returning HTML string."""
    tmpl = _env.get_template(template_name)
    return tmpl.render(**context)
