from general_stats import *
from git_tool import *
from moss_tool import *
from moss_stats import *
from gephi_tool import *
from anonymize import *
from tokenize_tool import *
from prob_tool import *
from diff_tool import *
import random

use_sample = False
CODE_DIR_NAME = os.path.join("rawdata", "dir3")
#CODE_DIR_NAME = os.path.join("rawdata", "dir_mass")
if use_sample: CODE_DIR_NAME = os.path.join("sampledata")
CODE_DIR = os.path.join(homedir, top_dir, CODE_DIR_NAME)

# for making a holdout set
EXPT_DIR = os.path.join("rawdata", "dir_mass")
HOLDOUT_DIR = os.path.join("rawdata", "dir_holdout")

COMMIT_DIR_NAME = "expanded_dir3"
if use_sample: COMMIT_DIR_NAME = "expanded_sampledata"
COMMIT_DIR = os.path.join(homedir, top_dir, COMMIT_DIR_NAME)
FINAL_SUBMISSIONS_DIR_NAME = "final_submissions"
FINAL_SUBMISSIONS_DIR = os.path.join(COMMIT_DIR, FINAL_SUBMISSIONS_DIR_NAME)
ONLINE_DIR_NAME = "online" # all known online versions
ONLINE_DIR = os.path.join(COMMIT_DIR, ONLINE_DIR_NAME)

# output after processing all commits
OUTPUT_DIR_NAME = "proc_output"
OUTPUT_DIR = os.path.join(homedir, top_dir, OUTPUT_DIR_NAME)

MOSS_OUTPUT_TOP_DIR = "moss_output"

"""
Expands all commits.

"""
def run(code_dir, target_dir, final_submissions_dir, output_dir):
  #reset_all_to_master(code_dir)
  #check_timestamps(code_dir)
  #get_unique_unames(code_dir)

  #expand_all_commits(code_dir, target_dir)
  # check_all_commits(target_dir, "2012_1")
  #copy_all_final(code_dir, final_submissions_dir)
  pass

def graph_nonmoss(code_dir, output_dir):
  #all_timestamps(code_dir, output_dir)
  #plot_times(output_dir)
  pass

def diff(code_dir, output_dir):
  #all_diffs(code_dir, output_dir)
  process_diffs(code_dir, output_dir, '2012_1')

def moss(moss_dir, output_dir, final_submissions_dir):
  #moss_process(moss_dir, 'baseline', output_dir, final_submissions_dir)
  #make_moss_graphs(output_dir, 'baseline')
  #return
  for year_q_dirname in os.listdir(output_dir):
    try:
      year, q = year_q_dirname.split('_')
      int(year), int(q)
    except: continue
    print "Processing moss output for dir %s" % (year_q_dirname)
    if use_sample:
      if year_q_dirname == "2012_1": print "ignoring 2012"; continue
    #moss_process(moss_dir, year_q_dirname, output_dir, final_submissions_dir)
    make_moss_graphs(output_dir, year_q_dirname)
    #create_gephi(output_dir, year_q_dirname)

def gephi(moss_dir, output_dir):
  for year_q_dirname in os.listdir(output_dir):
    try:
      year, q = year_q_dirname.split('_')
      int(year), int(q)
    except: continue
    print "Making gephi csv for dir %s" % (year_q_dirname)
    if use_sample:
      if year_q_dirname == "2012_1": print "ignoring 2012"; continue
    create_gephi(output_dir, year_q_dirname)

def tokenize(commit_dir, output_dir):
  for year_q_dirname in os.listdir(output_dir):
    try:
      year, q = year_q_dirname.split('_')
      int(year), int(q)
    except: continue
    print "Tokenizing dir %s" % (year_q_dirname)
    if year_q_dirname != "2012_1": print "ignoring all non-2012"; continue
    #token_preprocess(commit_dir, output_dir, year_q_dirname)
    #token_process(commit_dir, output_dir, year_q_dirname)
    #remove_empty_files(output_dir, year_q_dirname) # empty files created after thresholding
    #write_unique_docs_no_thresh(commit_dir, output_dir, year_q_dirname) # prior to thresholding
    use_user(output_dir, year_q_dirname)
    make_token_counts(output_dir, year_q_dirname) 
    use_commitdoc(output_dir, year_q_dirname)

def probs(commit_dir, output_dir):
  for year_q_dirname in os.listdir(output_dir):
    try:
      year, q = year_q_dirname.split('_')
      int(year), int(q)
    except: continue
    print "Tokenizing dir %s" % (year_q_dirname)
    if year_q_dirname != "2012_1": print "ignoring all non-2012"; continue
    #write_p_dict(output_dir, year_q_dirname)
    token_probs(output_dir, year_q_dirname)
    parse_token_probs(output_dir, year_q_dirname)
    token_probs_pairs(output_dir, year_q_dirname)
    parse_token_probs_pairs(output_dir, year_q_dirname)
    #threshold_check(output_dir, year_q_dirname)

def anonymize(moss_dir, output_dir, commit_dir):
  anonymize_all(moss_dir, output_dir, commit_dir)

def make_holdout(code_dir, holdout_dir, expt_dir, n=400):
  unique_unames = get_unique_unames(code_dir)
  tot_dirnum = len(unique_unames)
  hold_out_ints = set(random.sample(range(tot_dirnum), n))
  hold_out_dirs = []
  expt_dirs = []
  for k in range(tot_dirnum):
    if k in hold_out_ints:
      hold_out_dirs.append(unique_unames[k])
    else:
      expt_dirs.append(unique_unames[k])
  count = 0
  for d in hold_out_dirs:
    src_dir = os.path.join(code_dir, d)
    dst_dir = os.path.join(holdout_dir, d)
    cp_cmd = "cp -r %s %s" % (src_dir, dst_dir)
    print "holdout", count, cp_cmd
    call_cmd(cp_cmd)
    count += 1
  count = 0
  for d in expt_dirs:
    src_dir = os.path.join(code_dir, d)
    dst_dir = os.path.join(expt_dir, d)
    cp_cmd = "cp -r %s %s" % (src_dir, dst_dir)
    print "mass", count, cp_cmd
    call_cmd(cp_cmd)
    count += 1
  print "hold out", "\n".join(hold_out_dirs)
  print "expt_dirs", "\n".join(expt_dirs)
  print "all unames", tot_dirnum, "hold out", len(hold_out_dirs), len(expt_dirs)

if __name__ == "__main__":
  #run(CODE_DIR, COMMIT_DIR, FINAL_SUBMISSIONS_DIR, OUTPUT_DIR)
  #graph_nonmoss(CODE_DIR, OUTPUT_DIR)
  #make_holdout(CODE_DIR, HOLDOUT_DIR, EXPT_DIR)
  #anonymize(MOSS_OUTPUT_TOP_DIR, OUTPUT_DIR, COMMIT_DIR)
  #moss(MOSS_OUTPUT_TOP_DIR, OUTPUT_DIR, FINAL_SUBMISSIONS_DIR)
  #gephi(MOSS_OUTPUT_TOP_DIR, OUTPUT_DIR)
  #tokenize(COMMIT_DIR, OUTPUT_DIR)
  probs(COMMIT_DIR, OUTPUT_DIR)
  #diff(CODE_DIR, OUTPUT_DIR)
