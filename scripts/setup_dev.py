import subprocess


print("> Installing vesperando_core")
subprocess.call(["python", "-m", "pip", "install", "-e", "core/"])

print("> Installing vesperando_cli")
subprocess.call(["python", "-m", "pip", "install", "-e", "cli/[build]"])