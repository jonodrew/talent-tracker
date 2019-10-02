from app import create_app
from app.models import Role, User, Candidate, Organisation, db
import click
from modules.seed import commit_data

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {
        "db": db,
        "User": User,
        "Role": Role,
        "Candidate": Candidate,
        "Organisation": Organisation,
    }


@app.cli.command()
@click.option(
    "--new-install", default=False, help="Build the database and seed it with data"
)
def seed(new_install):
    """
    If you pass it 'new install' it'll build the database for you. Otherwise it'll just seed it with data
    """
    if new_install:
        db.create_all()
    commit_data()
