import subprocess


print("> Installing vesperando_core")
subprocess.call(["python", "-m", "pip", "install" "core/"])

print("> Installing vesperando_cli")
subprocess.call(["python", "-m", "pip", "install", "cli/[build]"])
