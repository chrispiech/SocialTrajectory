from general_stats import *
from git_tool import *
from moss_tool import *
from moss_stats import *

use_sample = False
CODE_DIR_NAME = os.path.join("rawdata", "dir3")
if use_sample: CODE_DIR_NAME = os.path.join("sampledata")
CODE_DIR = os.path.join(homedir, top_dir, CODE_DIR_NAME)

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

def run(code_dir, target_dir, final_submissions_dir, output_dir):
  # reset_all_to_master(code_dir)
  # check_timestamps(code_dir)
  # all_timestamps(code_dir, output_dir)
  #plot_times(output_dir)
  expand_all_commits(code_dir, target_dir)
  #copy_all_final(code_dir, final_submissions_dir)
  #check_all_commits(target_dir, "2012_1")

def moss(moss_dir, output_dir, final_submissions_dir):
  for year_q_dirname in os.listdir(output_dir):
    try:
      year, q = year_q_dirname.split('_')
      int(year), int(q)
    except: continue
    print "Processing moss output for dir %s" % (year_q_dirname)
    if use_sample:
      if year_q_dirname == "2012_1": print "ignoring 2012"; continue
    moss_process(moss_dir, year_q_dirname, output_dir, final_submissions_dir)
    make_moss_graphs(output_dir, year_q_dirname)

if __name__ == "__main__":
  run(CODE_DIR, COMMIT_DIR, FINAL_SUBMISSIONS_DIR, OUTPUT_DIR)
  #moss(MOSS_OUTPUT_TOP_DIR, OUTPUT_DIR, FINAL_SUBMISSIONS_DIR)
