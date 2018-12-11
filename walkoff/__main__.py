from .cli.cli import cli, add_commands


def main():
    add_commands()
    cli(obj={})


if __name__ == '__main__':
    main()
