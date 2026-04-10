#!/usr/bin/env python3
import subprocess, os, sys

repo = "F:/Coding/JiXia-Academy"
os.chdir(repo)

env = os.environ.copy()

def run(args):
    r = subprocess.run(args, capture_output=True, text=True, cwd=repo, env=env)
    if r.stdout: print(r.stdout, end="")
    if r.stderr: print(r.stderr, end="", file=sys.stderr)
    return r.returncode

print("=== staging ===")
rc = run(["git", "add", "src/engine/main.py", "docs/"])
print(f"add rc={rc}")

print("=== committing ===")
rc = run(["git", "commit", "-m", "feat: add main.py example entry point, engine MVP complete"])
print(f"commit rc={rc}")

print("=== log ===")
run(["git", "log", "--oneline", "-1"])
