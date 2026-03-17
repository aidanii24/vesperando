import datetime
import logging
import json
import sys
import os

from vesperando_core import procedure, randomizer, packer, configs
from vesperando_core.conf.settings import Paths
import click

import cli_logging


cli_logging.setup_logging(__name__)
logger = logging.getLogger(__name__)

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
    log_file: str = os.path.join(Paths.LOG_DIR, f"vesperando-generate_{datetime_id}.log")
    logger.addHandler(logging.FileHandler(log_file))

    logger.info("vesperando: Basic Randomizer")

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

    logger.info(f"Patch {app_randomizer.identifier}")
    logger.info(f"  \u2713 Using Targets: {targets if targets and not options_data else 'ALL'}")
    if options_data:
        logger.info(f"  \u2713 Using Options: {options_data}")
    logger.info("\n")

    app_randomizer.generate(targets, options_data, spoiler)

@cli.command(help="Patch the game with a randomizer patch file")
@click.option("--threads", "-t", type=int, default=8, help="Maximum number of threads to use")
@click.option("--clean", "-c", is_flag=True, help="Remove residue files generated during patching")
@click.option("--apply-immediately", "-a", is_flag=True, help="Apply the patch immediately after patching")
@click.argument('patch_file', type=click.Path(exists=True))
def patch(threads, clean, apply_immediately, patch_file):
    log_file: str = os.path.join(Paths.LOG_DIR, f"vesperando-patch_{datetime_id}.log")
    logger.addHandler(logging.FileHandler(log_file))

    # Check if provided patch file is a valid patch file
    # Only check if it is a directory as click already handles path existence automatically
    if os.path.isdir(patch_file):
        logger.error(f"\"{patch_file}\" is a directory. Please provide a .vbrp patch file.")
        sys.exit(1)

    app = procedure.GamePatchProcedure(patch_file, threads, apply_immediately, clean)
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