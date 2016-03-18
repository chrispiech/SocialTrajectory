from git_helper import *
from general_stats import *

"""
Goes through everything and changes all commits per
student into different snapshots of the code directory.
Each snapshot will be in a timestamp folder (also contains git hash).

Timestamp: UNIX timestamp.
  To convert to human dates: date -d @<dirname>
"""
def expand_all_commits(code_dir, target_dir):
  for student in os.listdir(code_dir):
    student_dir = os.path.join(code_dir, student)
    all_commits = git_log(git_dir=student_dir,
            format_str="%h %ct",
            extra_str="--date=local").split('\n')
    if not all_commits[0]:
      print "expand: %s ignored, corrupt git" % (student)
      continue

    year_q = get_submit_time(student_dir) 
    year_target_dir = os.path.join(target_dir, year_q)
    print "expand to:", target_dir
    for commit in all_commits:
      git_checkout(commit, orig_dir=student_dir, target_dir=year_target_dir, prefix=student)

"""
Removes commits from the expanded directory that do not
have the right files for MOSS processing.
"""
def check_all_commits(target_dir, year_q):
  year_dir = os.path.join(target_dir, year_q)
  for student_commit in os.listdir(os.path.join(target_dir, year_dir)):
    commit_path = os.path.join(target_dir, year_dir, student_commit)
    if not moss_okay(commit_path):
      shutil.rmtree(commit_path)
      print "No java files in %s. Removing." % (student_commit)
      continue
    

############## UTILITY FUNCTIONS #################
def reset_all_to_master(code_dir):
  for student in os.listdir(code_dir):
    student_dir = os.path.join(code_dir, student)
    git_master(student_dir)

"""
Copy all final submissions to the directory specified.
"""
def copy_all_final(code_dir, final_submissions_dir):
  reset_all_to_master(code_dir)
  for student in os.listdir(code_dir):
    student_dir = os.path.join(code_dir, student)
    year_q = get_submit_time(student_dir) 
    if not year_q: continue
    target_final_dir = os.path.join(final_submissions_dir, "%s_%s" % (year_q, student))
    if not os.path.exists(target_final_dir):
      os.makedirs(target_final_dir)
    cp_cmd = "cp -r %s/* %s" % (student_dir, target_final_dir)
    call_cmd(cp_cmd)
    print "Copied student %s (%s) to final dir %s" % (student, year_q, target_final_dir)
