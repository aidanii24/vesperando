import datetime
import logging
import json
import time
import sys
import os

from vesperando_cli import LOGGER_NAME
from vesperando_core import procedure, randomizer, packer, spoil as spoiling, configs, utils
from vesperando_core.conf.settings import Paths, Extensions
import click

import cli_logging
import prompt


cli_logging.setup_logging(LOGGER_NAME)
logger = logging.getLogger(LOGGER_NAME)

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

    # Initialize Randomizer
    app_randomizer = randomizer.BasicRandomizerProcedure(targets, identifier=name, seed=seed)

    # Setup Log File Handling
    ## This is performed after initializing the randomizer to allow the log filename to match the patch id
    log_file: str = os.path.join(Paths.LOG_DIR, f"vesperando-generate_{app_randomizer.identifier}.log")
    cli_logging.set_file_handler(log_file, logger)

    logger.info("vesperando: Basic Randomizer")
    logger.info(f"Randomizer {app_randomizer.identifier}")
    logger.info(f"{"\u2713":<4} Using Targets: {targets if targets and not options_data else '[ALL]'}")
    if options_data:
        logger.info(f"{"\u2713":<4} Using Options: {options}")
    logger.info("")

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

    app_randomizer.generate(targets, options_data, spoiler)

@cli.command(help="Patch the game with a randomizer patch file")
@click.option("--threads", "-t", type=int, default=8, help="Maximum number of threads to use")
@click.option("--clean", "-c", is_flag=True, help="Remove residue files generated during patching")
@click.option("--apply-immediately", "-a", is_flag=True, help="Apply the patch immediately after patching")
@click.argument('patch_file', required=False, type=click.Path())
def patch(threads, clean, apply_immediately, patch_file=None):
    log_file: str = os.path.join(Paths.LOG_DIR, f"vesperando-patch_{datetime_id}.log")
    cli_logging.set_file_handler(log_file, logger)

    logger.info("vesperando: Patcher")

    file_path: str = patch_file
    if patch_file:
        # Check if provided patch file is a valid patch file
        # The patch has to be a file
        if os.path.isdir(file_path):
            logger.error(f"\"{file_path}\" is a directory. Please provide a .vbrp patch file.")
            sys.exit(1)
        # Assume provided directory might be in the PATCHES directory before aborting the patch generation
        elif not os.path.isfile(file_path):
            file_path = os.path.join(Paths.PATCHES, file_path)

            if not os.path.isfile(file_path):
                logger.error(f"\"{patch_file}\" does not exist. Please provide a valid patch file.")
                sys.exit(1)
    else:
        logger.info("")

        patches: list[str] = []
        for f in os.listdir(Paths.PATCHES):
            if os.path.isfile(os.path.join(Paths.PATCHES, f)) and Extensions.is_valid_patch(f):
                patches.append(f)

        if not patches:
            logger.error("Please provide a valid patch file.")
            sys.exit(1)

        logger.info("Select a patch file to be used for patching.")
        logger.info("Answer with the corresponding number, or 0 to abort the patch.")

        choices: list[int] = [_ for _ in range(len(patches))]
        for i, p in enumerate(patches):
            logger.info(f"[{i + 1}] {p}")

        logger.info("")
        logger.info("[0] Cancel")
        logger.info("")

        res: int = prompt.choice(choices, f"Patch: (0 - {len(patches)})")
        logger.info("")

        if res == 0:
            logger.info("Patch aborted.")
            sys.exit(0)

        file_path = os.path.join(Paths.PATCHES, (patches[res - 1]))

    app = procedure.GamePatchProcedure(file_path, threads, apply_immediately, clean)
    app.patch()

    sys.exit(0)

@cli.command(help="Generate a spoiler log from a randomizer patch file")
@click.argument("patch_file", type=click.Path(exists=True))
def spoil(patch_file):
    log_file: str = os.path.join(Paths.LOG_DIR, f"vesperando-spoil_{datetime_id}.log")
    cli_logging.set_file_handler(log_file, logger)

    logger.info("vesperando: Spoil")
    logger.info(f"Spoil {os.path.basename(patch_file)}")

    # Check if provided patch file is a valid patch file
    # Only check if it is a directory as click already handles path existence automatically
    if os.path.isdir(patch_file):
        logger.critical(f"\"{patch_file}\" is a directory. Please provide a .vbrp patch file.")
        sys.exit(1)

    file_data: dict = json.load(open(patch_file), object_hook=utils.keys_to_int)
    patch_data: dict = dict(item for item in [*file_data.items()][4:])
    report_output: str = os.path.join(os.path.dirname(patch_file), f"tovde-spoiler-{datetime_id}.ods")

    start_time = time.time()
    logger.info(f"\n> Generating Spoiler Sheet")

    spoiler = spoiling.PatchSpoiler()
    spoiler.write_spreadsheet(patch_data, report_output)

    end_time = time.time()
    logger.info(f"\nSpoiler Sheet Generated. Finished in {end_time - start_time:.2f} seconds.")
    logger.info(f"Spoiler Sheet: {os.path.abspath(report_output)}")

@cli.command(help="Apply a generated patched output")
@click.argument("patch_name", type=click.Path(file_okay=True))
def apply(patch_name):
    log_file: str = os.path.join(Paths.LOG_DIR, f"vesperando-apply_{datetime_id}.log")
    cli_logging.set_file_handler(log_file, logger)

    logger.info("vesperando: Apply")

    is_patch_file: bool = False
    patched_path: str = patch_name
    try:
        if os.path.isfile(patch_name) and Extensions.is_valid_patch(patched_path):
            is_patch_file = True

            data = json.load(open(patch_name), object_hook=utils.keys_to_int)
            identifier = f"{data['player']}-{data['created']}"

            patched_path = os.path.join(Paths.OUTPUT, identifier)
    except json.JSONDecodeError as e:
        logger.info("")
        logger.error(f"{patch_name} contains a valid vesperando patch file extension, "
                     f"but could not be parsed as such.\n{e}")
        logger.warning("Discarding attempt to use patch name with a valid vesperando file extension "
                       "as a vesperando patch file.")

    # Assume provided directory might be in the OUTPUT directory before aborting the patch application
    if not os.path.isdir(patched_path):
        patched_path = os.path.join(Paths.OUTPUT, patched_path)

    if not os.path.isdir(patched_path):
        logger.info("")
        logger.error("No ready patch output matches the provided patch name.")
        if is_patch_file:
            logger.warning("Please generate the patch for this patch file first before applying it.")
        sys.exit(1)

    logger.info(f"Apply {os.path.basename(patched_path)}")
    logger.info("")

    try:
        game_dir: str = configs.Settings.get().get('paths', {}).get('game', '')
        packer.apply_patch(patched_path, game_dir)
    except Exception as e:
        logger.error(f"Failed to apply patched files.\n{e}")
        sys.exit(1)

    logger.info(f"Successfully applied patch {os.path.basename(patched_path)}.")

@cli.command(help="Restore the original game files")
def restore():
    log_file: str = os.path.join(Paths.LOG_DIR, f"vesperando-restore_{datetime_id}.log")
    cli_logging.set_file_handler(log_file, logger)

    logger.info("vesperando: Restore")
    logger.info("")

    try:
        game_dir: str = configs.Settings.get().get('paths', {}).get('game', '')

        packer.restore_backup(game_dir)
    except Exception as e:
        logger.error(f"Failed to restore game files.\n{e}")
        sys.exit(1)

    logger.info("Successfully restored original game files.")


if __name__ == "__main__":
    cli()