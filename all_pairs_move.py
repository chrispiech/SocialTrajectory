from helper import *

f = open(os.path.join(homedir, top_dir, 'expanded_dir3', 'tmp_doc'), 'r')
lines = f.readlines()
lines = [line.strip() for line in lines]

dir_2012_1 = os.path.join(homedir, top_dir, 'expanded_dir3', '2012_1')
dir_all_pairs = os.path.join(homedir, top_dir, 'expanded_dir3', 'all_pairs')

for line in lines:
  dirname, fname = line.split('/')
  source_dirname = os.path.join(dir_2012_1, dirname)
  target_dirname = os.path.join(dir_all_pairs, dirname)
  if not os.path.exists(target_dirname):
    os.makedirs(target_dirname)
  cp_cmd = "cp %s/%s %s/%s" % (source_dirname, fname, target_dirname, fname)
  call_cmd(cp_cmd) 
  
