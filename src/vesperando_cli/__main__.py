import datetime
import colorlog
import logging
import json
import sys
import os

from vesperando_core import procedure, randomizer, packer, configs
from vesperando_core.conf.settings import Paths
import click

# Prepare Logger
## Set Color Handler
class CustomLogFormatter(colorlog.ColoredFormatter):

    def __init__(self, fmts: dict[int, str], **kwargs):
        super().__init__()

        if "fmt" in kwargs:
            raise ValueError("[ERROR] Use the \"fmts\" argument for defining formats instead of \"fmt\"")

        self.formats = {level: colorlog.ColoredFormatter(fmt, **kwargs) for level, fmt in fmts.items()}

    def format(self, record):
        formatter = self.formats.get(record.levelno, self.formats[0])
        return formatter.format(record)

log_formatter = CustomLogFormatter({
                                       logging.NOTSET: "%(log_color)s[%(levelname)s]\t%(name)s:%(message)s",
                                       logging.INFO: "%(log_color)s%(message)s"
                                   },
                                   log_colors={
                                       'DEBUG': 'cyan',
                                       'WARNING': 'yellow',
                                       'ERROR': 'red',
                                       'CRITICAL': 'red, bg_yellow',
                                   })

log_handler = colorlog.StreamHandler()
log_handler.setFormatter(log_formatter)

## Initialize Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(log_handler)

## Ensure logging directory exists
if not os.path.isdir(Paths.LOG_DIR):
    os.makedirs(Paths.LOG_DIR)

datetime_id = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")

@click.version_option("0.1.0", prog_name="vesperando-cli")

@click.group()
def cli():
    pass

@cli.command(help="Generate a new randomizer patch file")
@click.option("--options", "-o", type=click.Path(exists=True), help="Options file to use")
@click.option("--seed", type=click.INT, help="Seed to use")
@click.option("--name", "-n", type=click.STRING, help="Name to identify the patch")
@click.option("--spoiler", "-s", is_flag=True, help="Generate Spoiler Log")
@click.argument("targets", nargs=-1,
                type=click.Choice(["artes", "skills", "items", "shops", "chests", "search"],False))
def generate(options, name, seed, spoiler, targets):
    options_data = {}

    if options:
        try:
            options_data = json.load(open(options))
        except Exception as e:
            if e == IsADirectoryError:
                logger.error(f"\"{options}\" is a directory.")
            else:
                logger.error("Failed to load options file: {}".format(e))

            logger.warning("Ignoring options file.")

    if options_data and targets:
        logger.warning("An options file has been provided. "
                       "Targets argument will be ignored in favor of the options file.")

    app_randomizer = randomizer.BasicRandomizerProcedure(targets, identifier=name, seed=seed)

    logger.info("vesperando: Basic Randomizer")
    logger.info(f"Patch {app_randomizer.identifier}")
    logger.info(f"  \u2713 Using Targets: {targets if targets and not options_data else 'ALL'}")
    if options_data:
        logger.info(f"  \u2713 Using Options: {options_data}")
    logger.info("\n")

    app_randomizer.generate(targets, options_data, spoiler)

@cli.command(help="Patch the game with a randomizer patch file")
@click.option("--threads", "-t", type=int, default=8, help="Maximum number of threads to use")
@click.option("--clean", "-c", is_flag=True, help="Remove residue files generated during patching")
@click.option("--apply", "-a", is_flag=True, help="Apply the patch immediately after patching")
@click.argument('patch_file', type=click.Path(exists=True))
def patch(threads, clean, apply, patch_file):
    log_file: str = os.path.join(Paths.LOG_DIR, f"vesperando-patch.log_{datetime_id}.log")
    logging.basicConfig(filename=log_file)

    # Check if provided patch file is a valid patch file
    # Only check if it is a directory as click already handles path existence automatically
    if os.path.isdir(patch_file):
        logger.error(f"\"{patch_file}\" is a directory. Please provide a .vbrp patch file.")
        sys.exit(1)

    app = procedure.GamePatchProcedure(patch_file, threads, apply, clean)
    app.patch()

    sys.exit(0)

@cli.command(help="Generate a spoiler log from a randomizer patch file")
@click.argument("patch_file", type=click.Path(exists=True))
def spoil(patch_file):
    pass

@cli.command(help="Apply a generated patched output")
@click.argument("patch", type=click.Path(exists=True))
def apply(patched_output):
    pass

@cli.command(help="Restore the original game files")
def restore():
    game_dir: str = configs.Settings.get().get('paths', {}).get('game', '')
    packer.restore_backup(game_dir)

if __name__ == "__main__":
    cli()