#!/usr/bin/python3

import os, sys, subprocess
import pymoss

baseline = True # running only final submissions against each other
use_sample = False
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

def baseline(TARGET_DIR, CURRENT_Q,
                FINAL_SUBMISSIONS_DIR_NAME,
                ONLINE_DIR_NAME,
                STARTER_DIR_NAME,
                MOSS_OUTPUT_DIR):
  current_q = 'baseline'
  if not os.path.exists(os.path.join(MOSS_OUTPUT_DIR, current_q)):
    os.makedirs(os.path.join(MOSS_OUTPUT_DIR, current_q))

  cwd = os.getcwd()
  os.chdir(TARGET_DIR)
  print("in dir", TARGET_DIR)
  m = pymoss.Runner(filetype)
  m.add(STARTER_DIR_NAME, pymoss.util.STARTER)
  m.add_all(ONLINE_DIR_NAME, pymoss.util.ARCHIVE)
  m.add_all(current_q)

  m.run(npairs=500)
  h = pymoss.Html(m, "%s" % current_q)
  moss_dir = (h.gen_all()).split('/')[-1]
  commit_moss_dir = os.path.join(MOSS_OUTPUT_DIR, current_q)
  mv_cmd = "mv %s %s" % (os.path.join(cwd, moss_dir), commit_moss_dir)
  print("moving moss output:", mv_cmd)
  call_cmd(mv_cmd)

"""
Select commit pairs, not per user.
"""
def select_pairs(TARGET_DIR, CURRENT_Q,
                FINAL_SUBMISSIONS_DIR_NAME,
                ONLINE_DIR_NAME,
                STARTER_DIR_NAME,
                MOSS_OUTPUT_DIR):
  current_q = 'all_pairs'
  # make temp dir in base_dir
  # for each dir in target_dir, add to temp
  # once directory is generated, move to moss_output_dir
  if not os.path.exists(os.path.join(MOSS_OUTPUT_DIR, current_q)):
    os.makedirs(os.path.join(MOSS_OUTPUT_DIR, current_q))

  cwd = os.getcwd()
  os.chdir(TARGET_DIR)
  print("in dir", TARGET_DIR)

  TEMP_DIR_NAME = "temp"
  count = 500
  for commit in os.listdir(current_q):
    print("starting moss for commit", commit)
    all_files = ''.join(os.listdir(os.path.join(current_q, commit)))
    if filetype not in all_files:
      print("skipping dir %s (no %s files)" % (commit, filetype))
      continue
    commit_temp_dir = os.path.join(TEMP_DIR_NAME, commit)

    commit_moss_dir = os.path.join(MOSS_OUTPUT_DIR, current_q, commit)
    if os.path.exists(commit_moss_dir):
      print("commit already processed")
      continue
    if not os.path.exists(commit_temp_dir):
      os.makedirs(commit_temp_dir)
    cp_cmd = "cp -r %s/* %s" % (os.path.join(current_q, commit),
                                os.path.join(commit_temp_dir))
    call_cmd(cp_cmd)

    m = pymoss.Runner(filetype, threshold=1000)
    try:
      m.add(STARTER_DIR_NAME, pymoss.util.STARTER)
      m.add_all(TEMP_DIR_NAME, prefix="")
      m.add_all(current_q, pymoss.util.ARCHIVE)

      m.run(npairs=100)
      h = pymoss.Html(m, "%s" % commit)
      moss_dir = (h.gen_all()).split('/')[-1]
      mv_cmd = "mv %s %s" % (os.path.join(cwd, moss_dir), commit_moss_dir)
      print("moving moss output to", commit_moss_dir)
      call_cmd(mv_cmd)
    finally: m.cleanup()

    rm_cmd = "rm -r %s" % (os.path.join(TARGET_DIR,commit_temp_dir))
    call_cmd(rm_cmd)
    count -= 1
    if count == 0: break

"""
Compares all commits of one user to all commits of the other user.
"""
def max_pairs_users(TARGET_DIR, CURRENT_Q,
                FINAL_SUBMISSIONS_DIR_NAME,
                ONLINE_DIR_NAME,
                STARTER_DIR_NAME,
                MOSS_OUTPUT_DIR):
  current_q = 'max_pairs_users'
  # make temp dir in base_dir
  # for each dir in target_dir, add to temp
  # once directory is generated, move to moss_output_dir
  if not os.path.exists(os.path.join(MOSS_OUTPUT_DIR, current_q)):
    os.makedirs(os.path.join(MOSS_OUTPUT_DIR, current_q))

  uname_pairs = []
  with open(os.path.join(homedir, top_dir, "proc_output/%s/probs" % CURRENT_Q, current_q)) as f:
    lines = f.readlines()
    uname_pairs = [line.split('\t')[:2] for line in lines]

  cwd = os.getcwd()
  os.chdir(TARGET_DIR)
  print("in dir", TARGET_DIR)

  TEMP_DIR_NAME = "temp"
  count = 500
  commit_moss_dir = os.path.join(MOSS_OUTPUT_DIR, CURRENT_Q)
  for uname_i, uname_j in uname_pairs:
    find_cmd_i = "find %s/%s -maxdepth 1 -name '%s*' -print" % (TARGET_DIR, CURRENT_Q, uname_i)
    commits_i = [line.split('/')[-1] for line in call_cmd(find_cmd_i).decode().split('\n')[:-1]]
    find_cmd_j = "find %s/%s -maxdepth 1 -name '%s*' -print" % (TARGET_DIR, CURRENT_Q, uname_j)
    commits_j = [line.split('/')[-1] for line in call_cmd(find_cmd_j).decode().split('\n')[:-1]]
    print(uname_i)
    print(commits_i)
    print(uname_j)
    print(commits_j)
    
    break
    print("starting moss for commit", commit)
    all_files = ''.join(os.listdir(os.path.join(current_q, commit)))
    if filetype not in all_files:
      print("skipping dir %s (no %s files)" % (commit, filetype))
      continue
    commit_temp_dir = os.path.join(TEMP_DIR_NAME, commit)

    commit_moss_dir = os.path.join(MOSS_OUTPUT_DIR, current_q, commit)
    if os.path.exists(commit_moss_dir):
      print("commit already processed")
      continue
    if not os.path.exists(commit_temp_dir):
      os.makedirs(commit_temp_dir)
    cp_cmd = "cp -r %s/* %s" % (os.path.join(current_q, commit),
                                os.path.join(commit_temp_dir))
    call_cmd(cp_cmd)

    m = pymoss.Runner(filetype, threshold=1000)
    try:
      m.add(STARTER_DIR_NAME, pymoss.util.STARTER)
      m.add_all(TEMP_DIR_NAME, prefix="")
      m.add_all(current_q, pymoss.util.ARCHIVE)

      m.run(npairs=100)
      h = pymoss.Html(m, "%s" % commit)
      moss_dir = (h.gen_all()).split('/')[-1]
      mv_cmd = "mv %s %s" % (os.path.join(cwd, moss_dir), commit_moss_dir)
      print("moving moss output to", commit_moss_dir)
      call_cmd(mv_cmd)
    finally: m.cleanup()

    rm_cmd = "rm -r %s" % (os.path.join(TARGET_DIR,commit_temp_dir))
    call_cmd(rm_cmd)
    count -= 1
    if count == 0: break

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

  # make final dir that only has current q, just for 2012_1 analysis
  final_current_q_dir = ''
  final_current_q_dir = '%s_%s' % (FINAL_SUBMISSIONS_DIR_NAME, CURRENT_Q)
  print("Making current_q-only final submission dir.")
  if not os.path.exists(os.path.join(final_current_q_dir)):
    os.makedirs(os.path.join(final_current_q_dir))
    year, q = CURRENT_Q.split('_')
    current_q_str = '%s%02d' % (year, int(q))
    print(current_q_str)
    final_current_q_subs = filter(lambda d: d[:6] == current_q_str,
                            os.listdir(FINAL_SUBMISSIONS_DIR))
    for final_sub in final_current_q_subs:
      ln_cmd = 'ln -s %s %s' % (os.path.join(FINAL_SUBMISSIONS_DIR, final_sub),
                                os.path.join(final_current_q_dir, final_sub))
      call_cmd(ln_cmd)

  TEMP_DIR_NAME = "temp"
  count = 500
  for commit in os.listdir(CURRENT_Q):
    print("starting moss for commit", commit)
    all_files = ''.join(os.listdir(os.path.join(CURRENT_Q, commit)))
    if filetype not in all_files:
      print("skipping dir %s (no %s files)" % (commit, filetype))
      continue
    commit_temp_dir = os.path.join(TEMP_DIR_NAME, commit)

    commit_moss_dir = os.path.join(MOSS_OUTPUT_DIR, CURRENT_Q, commit)
    if os.path.exists(commit_moss_dir):
      print("commit already processed")
      continue
    if not os.path.exists(commit_temp_dir):
      os.makedirs(commit_temp_dir)
    cp_cmd = "cp -r %s/* %s" % (os.path.join(CURRENT_Q, commit),
                                os.path.join(commit_temp_dir))
    call_cmd(cp_cmd)

    # make basically no threshold
    m = pymoss.Runner(filetype, threshold=10 ** 9)
    try:
      m.add(STARTER_DIR_NAME, pymoss.util.STARTER)
      m.add_all(TEMP_DIR_NAME, prefix="")
      if final_current_q_dir:
        m.add_all(final_current_q_dir, pymoss.util.ARCHIVE)
      else:
        m.add_all(FINAL_SUBMISSIONS_DIR_NAME, pymoss.util.ARCHIVE)
      m.add_all(ONLINE_DIR_NAME, pymoss.util.ARCHIVE)

      m.run()
      h = pymoss.Html(m, "%s" % commit)
      moss_dir = (h.gen_all()).split('/')[-1]
      mv_cmd = "mv %s %s" % (os.path.join(cwd, moss_dir), commit_moss_dir)
      print("moving moss output to", commit_moss_dir)
      call_cmd(mv_cmd)
    finally: m.cleanup()

    rm_cmd = "rm -r %s" % (os.path.join(TARGET_DIR,commit_temp_dir))
    call_cmd(rm_cmd)
    count -= 1
    if count == 0: break



if __name__ == "__main__":
  pymoss.util.time("Running all moss", lambda:
                multi_moss(TARGET_DIR, CURRENT_Q,
                    FINAL_SUBMISSIONS_DIR_NAME, ONLINE_DIR_NAME,
                    STARTER_DIR_NAME,
                    MOSS_OUTPUT_DIR))
  # pymoss.util.time("Running baseline", lambda:
  #               baseline(TARGET_DIR, CURRENT_Q,
  #                   FINAL_SUBMISSIONS_DIR_NAME, ONLINE_DIR_NAME,
  #                   STARTER_DIR_NAME,
  #                   MOSS_OUTPUT_DIR))
  # pymoss.util.time("Running select pairs", lambda:
  #               select_pairs(TARGET_DIR, CURRENT_Q,
  #                   FINAL_SUBMISSIONS_DIR_NAME, ONLINE_DIR_NAME,
  #                   STARTER_DIR_NAME,
  #                   MOSS_OUTPUT_DIR))
  # pymoss.util.time("Running select pairs", lambda:
  #               max_pairs_users(TARGET_DIR, CURRENT_Q,
  #                   FINAL_SUBMISSIONS_DIR_NAME, ONLINE_DIR_NAME,
  #                   STARTER_DIR_NAME,
  #                   MOSS_OUTPUT_DIR))
