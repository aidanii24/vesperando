from vesperando_core import procedure, randomizer
import click


@click.version_option("0.1.0", prog_name="vesperando-cli")

@click.group()
def cli():
    pass

@cli.command(help="Generate a new randomizer patch file")
@click.option("--options", "-o", type=click.Path(exists=True), help="Options file to use")
@click.option("--seed", "-s", type=click.INT)
@click.option("--spoil", "-p", is_flag=True, help="Generate Spoiler Log")
@click.option("--interactive", "-i", is_flag=True)
@click.argument("targets", nargs=-1,
                type=click.Choice(["artes", "skills", "items", "shops", "chests", "search"],False))
def generate(options, name, seed, spoiler, targets):
    template = randomizer.InputTemplate(targets, seed=seed)

@cli.command(help="Patch the game with a randomizer patch file")
@click.option("--threads", "-t", type=int, default=8, help="Maximum number of threads to use")
@click.option("--clean", "-c", is_flag=True, help="Remove residue files generated during patching")
@click.option("--apply", "-a", is_flag=True, help="Apply the patch immediately after patching")
@click.argument('patch_file', type=click.Path(exists=True))
def patch(threads, clean, apply, patch_file):
    patch_procedure = procedure.GamePatchProcedure(patch_file, threads, apply, clean)

@cli.command(help="Generate a spoiler log from a randomizer patch file")
@click.argument("patch_file", type=click.Path(exists=True))
def spoil(patch_file):
    pass

@cli.command(help="Apply a generated patched output")
@click.option("--interactive", "-i", is_flag=True)
@click.argument("patch", type=click.Path(exists=True))
def apply(interactive, patched_output):
    pass

@cli.command(help="Restore the original game files")
def restore():
    pass

if __name__ == "__main__":
    cli()