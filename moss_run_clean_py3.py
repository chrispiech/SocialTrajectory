#!/usr/bin/python6

import os, sys, subprocess
import pymoss
import shutil

def load_path():
  with open('file_path.csv', 'r') as f:
    top_dir = f.readline().strip().split(',')[0]
  return top_dir
top_dir = load_path()

baseline = True # running only final submissions against each other
use_sample = False
use_all_quarters = True
#TARGET_DIR_NAME = "expanded_dir3"
TARGET_DIR_NAME = "expanded_mass"
TARGET_DIR = os.path.join(top_dir, TARGET_DIR_NAME)

FINAL_SUBMISSIONS_DIR_NAME = "final_submissions"
FINAL_SUBMISSIONS_DIR = os.path.join(TARGET_DIR, FINAL_SUBMISSIONS_DIR_NAME)
LECTURE_DIR_NAME = "lecture"
LECTURE_DIR = os.path.join(TARGET_DIR, LECTURE_DIR_NAME)
ONLINE_DIR_NAME = "online" # all known online versions
ONLINE_DIR = os.path.join(TARGET_DIR, ONLINE_DIR_NAME)
NOONLINE_DIR_NAME = "noonline"
STARTER_DIR_NAME = "STARTER"

MOSS_DIR_NAME = "moss_mass_clean"
MOSS_OUTPUT_DIR = os.path.join(top_dir, MOSS_DIR_NAME)
filetype = "java"

def call_cmd(cmd):
  return subprocess.Popen([cmd],stdout=subprocess.PIPE, shell=True).communicate()[0]

def baseline(TARGET_DIR, CURRENT_Q,
                FINAL_SUBMISSIONS_DIR_NAME,
                ONLINE_DIR_NAME,
                STARTER_DIR_NAME,
                MOSS_OUTPUT_DIR):
  current_q = 'baseline'
  if not os.path.exists(os.path.join(MOSS_OUTPUT_DIR, current_q)):
    os.makedirs(os.path.join(MOSS_OUTPUT_DIR, current_q))
  #current_q = 'final_submissions' # for holdout and mass; all quarters!

  OUTPUT_TEMP_DIR_NAME = "baseline_temp"

  cwd = os.getcwd()
  os.chdir(TARGET_DIR)
  print("in dir", TARGET_DIR)
  m = pymoss.Runner(filetype)
  m.add(STARTER_DIR_NAME, pymoss.util.STARTER)
  m.add_all(ONLINE_DIR_NAME, pymoss.util.ARCHIVE)
  m.add_all(current_q)
  num_dirs = len(os.listdir(os.path.join(TARGET_DIR, current_q)))
  num_dirs_ceil = (num_dirs/100+1)*100

  m.run(npairs=num_dirs_ceil)
  h = pymoss.Html(m, "%s" % current_q)
  moss_dir = (h.gen_all(OUTPUT_TEMP_DIR_NAME)).split('/')[-1]
  commit_moss_dir = os.path.join(MOSS_OUTPUT_DIR, current_q)
  mv_cmd = "mv %s %s" % (os.path.join(cwd, moss_dir), commit_moss_dir)
  print("moving moss output:", mv_cmd)
  call_cmd(mv_cmd)

def multi_moss(TARGET_DIR, CURRENT_Q,
                FINAL_SUBMISSIONS_DIR_NAME,
                MOSS_OUTPUT_DIR):
  # make temp dir in base_dir
  # for each dir in target_dir, add to temp
  # once directory is generated, move to moss_output_dir
  if not os.path.exists(os.path.join(MOSS_OUTPUT_DIR, CURRENT_Q)):
    os.makedirs(os.path.join(MOSS_OUTPUT_DIR, CURRENT_Q))

  cwd = os.getcwd()
  os.chdir(TARGET_DIR)
  print("in dir", TARGET_DIR)

  final_current_q_dir = ''
  count = -1 # run all of them
  commit_tot = len(os.listdir(CURRENT_Q))
  commit_count = 0
  print("num commits", commit_tot, CURRENT_Q)
  uname = '2014010069'
  for i, commit in enumerate(os.listdir(CURRENT_Q)):
    if uname not in commit: continue
    print("{}/{}: starting moss for commit {}".format(
      i, commit_tot, commit))
    java_files = filter(lambda fname: filetype in fname,
                os.listdir(os.path.join(CURRENT_Q, commit)))
    if not java_files:
      print("skipping dir %s (no %s files)" % (commit, filetype))
      continue

    commit_moss_dir = os.path.join(MOSS_OUTPUT_DIR, CURRENT_Q, commit)
    if os.path.exists(commit_moss_dir):
      print("commit already processed")
      continue
    temp_dir = "temp_%s" % commit
    output_temp_dir = "output_%s" % commit
    if os.path.exists(temp_dir):
      shutil.rmtree(temp_dir)
    if os.path.exists(output_temp_dir):
      shutil.rmtree(output_temp_dir)
    os.mkdir(temp_dir)
    for java_f in java_files:
      f_prefix = java_f.split('.')[0]
      java_moss_dir = os.path.join(temp_dir,
                            '%s_%s' % (commit, f_prefix))
      os.mkdir(java_moss_dir)
      cp_cmd = "cp %s %s/." % (os.path.join(CURRENT_Q, commit, java_f),
                                java_moss_dir)
      call_cmd(cp_cmd)

    # make basically no threshold
    m = pymoss.Runner(filetype, threshold=10 ** 9)
    try:
      m.add(STARTER_DIR_NAME, pymoss.util.STARTER)
      m.add_all(temp_dir, prefix="")
      if final_current_q_dir:
        m.add_all(final_current_q_dir, pymoss.util.ARCHIVE)
      else:
        m.add_all(FINAL_SUBMISSIONS_DIR_NAME, pymoss.util.ARCHIVE)
      m.add_all(ONLINE_DIR_NAME, pymoss.util.ARCHIVE)

      m.run(npairs=5)
      h = pymoss.Html(m, "%s" % commit)
      moss_dir = (h.gen_all(output_temp_dir)).split('/')[-1]
      mv_cmd = "mv %s %s" % (os.path.join(cwd, moss_dir), commit_moss_dir)
      print("moving moss output to", commit_moss_dir)
      call_cmd(mv_cmd)
    finally: m.cleanup()

    rm_cmd = "rm -r %s/*" % (os.path.join(TARGET_DIR,temp_dir))
    call_cmd(rm_cmd)
    count -= 1
    if count == 0: break
  os.chdir(cwd)
 
if __name__ == "__main__":
  CURRENT_Q = "2014_1"

  print(os.listdir(TARGET_DIR))
  for year_q_dirname in os.listdir(TARGET_DIR):
    try:
      year, q = year_q_dirname.split('_')
      int(year), int(q)
    except: continue

  for year_q_dirname in ["2014_1"]:
    pymoss.util.time("Running all moss", lambda:
                  multi_moss(TARGET_DIR, year_q_dirname,
                      FINAL_SUBMISSIONS_DIR_NAME,
                      MOSS_OUTPUT_DIR))
    year_q_dirname = '2014_1'
