from cli import db
from click.testing import CliRunner
import pytest

# def test_db()


# import click

# @click.command()
# @click.argument('name')
# def hello(name):
#    click.echo('Hello %s!' % name)

from click.testing import CliRunner
# from hello import hello

def test_db():
  runner = CliRunner()
  result = runner.invoke(db, args='show_tables')
  assert result.exit_code == 0
  assert 'dbtools' in result.output
#   assert result.output == 'Peter!\n'