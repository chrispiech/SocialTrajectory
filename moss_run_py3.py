#!/usr/bin/python3

import os, sys, subprocess
import pymoss

use_sample = True
homedir = "/home/ubuntu/"
top_dir = "socialTrajectories"
CODE_DIR_NAME = "rawdata/dir3"
if use_sample: CODE_DIR_NAME = os.path.join("rawdata", "sampledata")
CODE_DIR = os.path.join(homedir, top_dir, CODE_DIR_NAME)
TARGET_DIR_NAME = "expanded_dir3"
if use_sample: TARGET_DIR_NAME = "expanded_sampledata"
TARGET_DIR = os.path.join(homedir, top_dir, TARGET_DIR_NAME)

FINAL_SUBMISSIONS_DIR_NAME = "final_submissions"
FINAL_SUBMISSIONS_DIR = os.path.join(TARGET_DIR, FINAL_SUBMISSIONS_DIR_NAME)
ONLINE_DIR_NAME = "online" # all known online versions
ONLINE_DIR = os.path.join(TARGET_DIR, ONLINE_DIR_NAME)

STARTER_DIR_NAME = "STARTER"

# Moss options
CURRENT_Q = "2012_1"
if use_sample: CURRENT_Q = "2013_1"
MOSS_OUTPUT_DIR = os.path.join(homedir, top_dir, "moss_output")
filetype = "java"

def call_cmd(cmd):
  return subprocess.Popen([cmd],stdout=subprocess.PIPE, shell=True).communicate()[0]

def multi_moss(TARGET_DIR, CURRENT_Q,
                FINAL_SUBMISSIONS_DIR_NAME,
                ONLINE_DIR_NAME,
                STARTER_DIR_NAME,
                MOSS_OUTPUT_DIR):
  # make temp dir in base_dir
  # for each dir in target_dir, add to temp
  # once directory is generated, move to moss_output_dir
  if not os.path.exists(os.path.join(MOSS_OUTPUT_DIR, CURRENT_Q)):
    os.makedirs(os.path.join(MOSS_OUTPUT_DIR, CURRENT_Q))

  cwd = os.getcwd()
  os.chdir(TARGET_DIR)
  print("in dir", TARGET_DIR)

  TEMP_DIR_NAME = "temp"
  quarters = [FINAL_SUBMISSIONS_DIR_NAME, ONLINE_DIR_NAME]
  for commit in os.listdir(CURRENT_Q):
    print("starting moss for commit", commit)
    commit_temp_dir = os.path.join(TEMP_DIR_NAME, commit)
    if not os.path.exists(commit_temp_dir):
      os.makedirs(commit_temp_dir)
    cp_cmd = "cp -r %s/* %s" % (os.path.join(CURRENT_Q, commit),
                                os.path.join(commit_temp_dir))
    call_cmd(cp_cmd)

    m = pymoss.Runner(filetype)
    try:
      m.add(STARTER_DIR_NAME, pymoss.util.STARTER)
      m.add_all(TEMP_DIR_NAME, prefix="")
      m.add_all(FINAL_SUBMISSIONS_DIR_NAME, pymoss.util.ARCHIVE)
      m.add_all(ONLINE_DIR_NAME, pymoss.util.ARCHIVE)

      m.run()
      h = pymoss.Html(m, "%s" % commit)
      moss_dir = (h.gen_all()).split('/')[-1]
      mv_cmd = "mv %s %s" % (os.path.join(cwd, moss_dir),
                             os.path.join(MOSS_OUTPUT_DIR, CURRENT_Q, commit))
      print("moving moss output to",
                    os.path.join(MOSS_OUTPUT_DIR, CURRENT_Q, commit))
      call_cmd(mv_cmd)
    finally: m.cleanup()

    rm_cmd = "rm -r %s" % (os.path.join(TARGET_DIR,commit_temp_dir))
    call_cmd(rm_cmd)

if __name__ == "__main__":
  pymoss.util.time("Running all moss", lambda:
                multi_moss(TARGET_DIR, CURRENT_Q,
                    FINAL_SUBMISSIONS_DIR_NAME, ONLINE_DIR_NAME,
                    STARTER_DIR_NAME,
                    MOSS_OUTPUT_DIR))
