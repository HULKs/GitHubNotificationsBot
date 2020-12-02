import click

@click.command()
def run(**arguments):
    print(arguments)

def main():
    run(auto_envvar_prefix='BOT')
