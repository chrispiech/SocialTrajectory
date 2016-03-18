import os, sys, subprocess
import shutil
import numpy as np
import matplotlib as mpl
mpl.use('Agg') # to enable non ssh -X
import matplotlib.pyplot as plt

homedir = "/home/ubuntu/"
top_dir = "socialTrajectories"

def call_cmd(cmd):
  return subprocess.Popen([cmd],stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()

# assignment code format.
FILETYPE = 'java'
"""
Checks if the directory contains any java files.
If it contains no java files, return False.
"""
def moss_okay(commit_dir, filetype=FILETYPE):
  file_exts = [f.split('.')[-1] for f in os.listdir(commit_dir)]
  if not filetype in file_exts:
    return False
  return True
