import logging
import click
import os


logger = logging.getLogger(os.environ.get('LOGGER_NAME', "vesperando"))

def choice(choices: list, text: str = "") -> int:
    ans = click.prompt(text, show_choices=False)
    if ans.isdigit() and int(ans) in choices:
        return int(ans)
    else:
        logger.error(f"Please choose a number between 0 and {len(choices)}.")
        return choice(choices, text)