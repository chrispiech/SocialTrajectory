from general_stats import *
from git_tool import *
from moss_tool import *
from moss_stats import *
from gephi_tool import *
from anonymize import *
from ta_stats import *
from tokenize_tool import *
from prob_tool import *
from diff_tool import *
from diff_stats import *
from lecture_stats import *
from comp_stats import *
from model_stats import *
import random

top_dir = load_path() # from helper.py

# for making a holdout set
EXPT_DIR = os.path.join("rawdata", "dir_mass")
HOLDOUT_DIR = os.path.join("rawdata", "dir_holdout")

CODE_DIR_NAME = os.path.join("rawdata", "dir_mass")
CODE_DIR_NAME = os.path.join("rawdata", "dir_holdout")
CODE_DIR_NAME = os.path.join("rawdata")
CODE_DIR = os.path.join(top_dir, CODE_DIR_NAME)

COMMIT_DIR_NAME = "expanded_mass"
COMMIT_DIR = os.path.join(top_dir, COMMIT_DIR_NAME)

# final submissions and all known online versions
FINAL_SUBMISSIONS_DIR_NAME = "final_submissions"
FINAL_SUBMISSIONS_DIR = os.path.join(COMMIT_DIR, FINAL_SUBMISSIONS_DIR_NAME)
ONLINE_DIR_NAME = "online"
ONLINE_DIR = os.path.join(COMMIT_DIR, ONLINE_DIR_NAME)

# the most important directory ever
OUTPUT_DIR_NAME = "proc_output"
OUTPUT_DIR = os.path.join(top_dir, OUTPUT_DIR_NAME)

# for moss
MOSS_OUTPUT_TOP_DIR = "moss_mass"

# for grades
GRADE_DIR_NAME = "anon_grades"
GRADE_DIR = os.path.join(OUTPUT_DIR, GRADE_DIR_NAME)
GRADES_AND_LAIR_DIR = os.path.join("grades_and_lair")

"""
Expands all commits.

"""
def run(code_dir, target_dir, final_submissions_dir, output_dir):
  reset_all_to_master(code_dir)
  #get_unique_unames(code_dir)
  #check_timestamps(CODE_DIR)
  #copy_all_final(code_dir, final_submissions_dir)

  expand_all_commits(code_dir, target_dir, only_year='2012_1')
  # check_all_commits(target_dir, "2012_1")
  pass

def graph_general(code_dir, output_dir):
  all_timestamps(code_dir, output_dir)
  #plot_times(output_dir)
  #graph_gradetime_multi(output_dir)
  return
  plot_ta_stats_multi(output_dir)
  for year_q_dirname in os.listdir(output_dir):
    try:
      year, q = year_q_dirname.split('_')
      int(year), int(q)
    except: continue
    print "using", year_q_dirname
    #graph_gradetime(output_dir, year_q_dirname)
    #plot_times_sorted(output_dir, year_q_dirname)
    plot_ta_stats(output_dir, year_q_dirname)
    #plot_k_means(output_dir, year_q_dirname)

def diff(moss_dir, code_dir, output_dir):
  year_q = '2012_1'
  #all_diffs(code_dir, output_dir, year_q)
  moss_process(moss_dir, year_q, output_dir, use_diff=True)
  process_diffs(code_dir, output_dir, year_q)
  plot_diffs(output_dir, year_q)

def moss(moss_dir, output_dir, final_submissions_dir):
  #output_dir = '%s_mass' % output_dir
  #for year_q_dirname in os.listdir(output_dir):
  #make_moss_graphs_multi(output_dir)
  for year_q_dirname in ['2012_1', '2013_1', '2014_1']:
    try:
      year, q = year_q_dirname.split('_')
      int(year), int(q)
    except: continue
    print "Processing moss output for dir %s" % (year_q_dirname)
    #year_q_dirname = 'noonline_2012_1'
    moss_process(moss_dir, year_q_dirname, output_dir)
    #make_moss_graphs(output_dir, year_q_dirname)
    #create_gephi(output_dir, year_q_dirname)

def component(output_dir):
  component_stats_multi(output_dir)
  #cvmodel(output_dir)
  for year_q_dirname in ['2012_1', '2013_1', '2014_1']:
    try:
      year, q = year_q_dirname.split('_')
      int(year), int(q)
    except: continue
    #component_stats(output_dir, year_q_dirname)

def lecture(output_dir):
  lecture_plot(output_dir, '2012_1')

def pairwise(output_dir):
  pair = '2012010030_2012010091'
  pair_prefix = 'max_pairs_users'
  pair_dir = os.path.join(pair_prefix, pair)
  #moss_process(moss_dir, pair_dir, output_dir, final_submissions_dir)
  make_moss_pair_graphs(output_dir, pair, pair_prefix)

def gephi(moss_dir, output_dir):
  for year_q_dirname in os.listdir(output_dir):
    try:
      year, q = year_q_dirname.split('_')
      int(year), int(q)
    except: continue
    print "Making gephi csv for dir %s" % (year_q_dirname)
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
  #anonymize_all(moss_dir, output_dir, commit_dir)
  #anonymize_all(moss_dir, output_dir, commit_dir, code_dir=CODE_DIR)
  anonymize_grades_and_lair(GRADES_AND_LAIR_DIR)

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

def baseline(moss_dir, output_dir):
  for year_q_dirname in ['2012_1', '2013_1', '2014_1']: 
    baseline_dirname = 'baseline_%s' % year_q_dirname
    write_moss_similar(moss_dir, baseline_dirname, output_dir)
    """
    Change the following in write_moss_similar:
      similarities.append((self_f, other_f_path, report_html,
                tokens_matched, percent_self, percent_other))
      for sim in similarities: # ignore rank!!
        f.write('%s,%s,%s,%d,%.2f,%.2f\n' % sim)
    """
if __name__ == "__main__":
  #anonymize(MOSS_OUTPUT_TOP_DIR, OUTPUT_DIR, COMMIT_DIR)
  #make_holdout(CODE_DIR, HOLDOUT_DIR, EXPT_DIR)
  run(CODE_DIR, COMMIT_DIR, FINAL_SUBMISSIONS_DIR, OUTPUT_DIR)
  #moss(MOSS_OUTPUT_TOP_DIR, OUTPUT_DIR, FINAL_SUBMISSIONS_DIR)
  #graph_general(CODE_DIR, OUTPUT_DIR)
  #baseline(MOSS_OUTPUT_TOP_DIR, OUTPUT_DIR)
  print tfw
  component(OUTPUT_DIR)
  #lecture(OUTPUT_DIR)
  #gephi(MOSS_OUTPUT_TOP_DIR, OUTPUT_DIR)
  #tokenize(COMMIT_DIR, OUTPUT_DIR)
  #probs(COMMIT_DIR, OUTPUT_DIR)
  #diff(MOSS_OUTPUT_TOP_DIR, CODE_DIR, OUTPUT_DIR)
  #pairwise(OUTPUT_DIR)
