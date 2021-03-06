from helper import *
from git_helper import *
from time import strptime
from datetime import date
import time

output_moss_dir = "moss"
"""
Overall moss processing function.
"""
def moss_process(moss_dir, year_q, output_dir, use_diff=False):
  start_time = time.time()
  if use_diff:
    year_q = 'diff_%s' % year_q
    for diff_type in [1,2]:
      write_all_moss_similar(moss_dir, year_q, output_dir, use_diff=diff_type)
  else:
    write_all_moss_similar(moss_dir, year_q, output_dir)
  time_elapsed = time.time() - start_time
  print "Time for {} process moss: {}".format(year_q, seconds_to_time(time_elapsed))
  #all_sims = load_all_sims_from_log(output_dir, year_q)
  #return all_sims

"""
Saves people who have an online similarity.
"""
def write_online_stats(output_dir, year_q):
  top_sims = load_top_sims_from_log(output_dir, year_q)
  online_sims = get_top_sims_online(top_sims)
  online_moss_path = os.path.join(output_dir, "%s_online_moss.csv" % year_q) 
  with open(online_moss_path, 'w') as f:
    unames = online_sims.keys()
    unames.sort()
    for uname in unames:
      num_commits = len(top_sims[uname].keys())
      if not online_sims[uname]: continue # if zero
      f.write('%s,%s,%s\n' % (uname, online_sims[uname], num_commits))
  print "online sims saved to", online_moss_path

def load_online_stats(output_dir, year_q):
  top_sims = load_top_sims_from_log(output_dir, year_q)
  online_moss_path = os.path.join(output_dir, "%s_online_moss.csv" % year_q) 
  online_sims = {}
  with open(online_moss_path, 'r') as f:
    for line in f.readlines():
      line = line.strip()
      uname, num_online, num_commits = line.split(',')
      posix_times = top_sims[uname].keys()
      posix_times.sort()
      online_info = []
      for commit_ind, posix_time in enumerate(posix_times):
        uname_other, tokens, percent_self, percent_other,_,_ = \
            top_sims[uname][posix_time]
        if 'online' in uname_other:
          online_info.append(
              (int(posix_time), commit_ind, tokens, percent_self, percent_other))
      online_sims[uname] = (int(num_online), int(num_commits),
                            np.array(online_info))
  return online_sims

def load_top_sims_by_uname(top_sims):
  cross_sims = {}
  cross_names = {}
  for uname in top_sims:
    posix_times = top_sims[uname].keys()
    num_commits = float(len(posix_times))
    posix_times.sort()
    cross_sims[uname] = {}
    cross_names[uname] = {}
    for commit_ind, posix_time in enumerate(posix_times):
      uname_other, tokens, percent_self, percent_other, _, commit_hash = \
          top_sims[uname][posix_time]
      if uname_other not in cross_sims[uname]:
        cross_sims[uname][uname_other] = []
        cross_names[uname][uname_other] = []
      cross_sims[uname][uname_other].append(
          (int(posix_time), commit_ind/num_commits, tokens, percent_self, percent_other))
      cross_names[uname][uname_other].append('%s_%s_%s' % (uname, posix_time, commit_hash))
    for uname_other in cross_sims[uname]:
      cross_sims[uname][uname_other] = np.array(cross_sims[uname][uname_other])
  return cross_sims, cross_names

def load_components_info(output_dir, year_q):
  components = {}
  edges = {}
  comp_f_name = '%s_components.csv' % year_q
  with open(os.path.join(output_dir, comp_f_name), 'r') as f:
    for line in f.readlines():
      line = line.strip()
      if len(line.split(',')) != 4: continue
      uname, group_id, indegree, outdegree = line.split(',')
      components[uname] = (int(group_id), int(indegree), int(outdegree))
  edge_f_name = '%s_edges.csv' % year_q
  with open(os.path.join(output_dir, edge_f_name), 'r') as f:
    for line in f.readlines():
      line = line.strip()
      if len(line.split(',')) < 4: continue
      uname, uname_other, commit_hash, posix_time = line.split(',')[:4]
      info = line.split(',')[4:]
      info = map(float, info[1:])
      if uname not in edges:
        edges[uname] = {}
      if uname_other not in edges[uname]:
        edges[uname][uname_other] = {}
      edges[uname][uname_other][posix_time] = \
          tuple([uname_other, commit_hash] + info)
  return components, edges
  
def get_grps(comps, edges):
  components = {}
  for uname, (grp, ind, outd) in comps.iteritems():
    grp_uname = '%s_%s' % (grp, uname[:6])
    if grp == 0: # the online one
      grp_uname = "0"
    if grp_uname not in components:
      components[grp_uname] = []

    components[grp_uname].append(uname)

  components_list = []
  grp_nums = sorted(components.keys())
  count = 0
  for grp in grp_nums:
    count += len(components[grp])
    print sorted(components[grp])
    components_list.append(components[grp])
  print "count components:", count
  return components_list

"""
Returns the number of times "online" appears in this list of usernames.
"""
def get_number_online(other_array):
  return ['online' in x for x in other_array].count(True)

"""
Calls get_number_online for all commits of each user in top_sims.
"""
def get_top_sims_online(top_sims):
  online_sims = {}
  for uname in top_sims:
    online_sims[uname] = get_number_online(\
        [top_sims[uname][posix_time][0] \
            for posix_time in top_sims[uname]])
  return online_sims

def get_all_output_f(all_sims):
  all_output_f = set()
  for uname in all_sims:
    print "username", uname
    for commit in all_sims[uname]:
    #other_f_path, other_f_html, tokens_matched, percent_self, percent_other 
      commit_output_f = [sim[0] for sim in all_sims[uname][commit]]
      for full_f in commit_output_f:
        all_output_f.add(get_uname_from_f(full_f))
  return all_output_f

"""
Does not work with use_diff because I was lazy.
"""
#other_f_path, other_f_html, tokens_matched, percent_self, percent_other 
def load_all_sims_from_log(output_dir, year_q):
  output_yq_dir = os.path.join(output_dir, year_q, output_moss_dir)
  all_sims = {}
  for commit in os.listdir(output_yq_dir):
    uname = '_'.join(commit.split('_')[:2]) # ignores additional integer, e.g. uid_1
    if uname not in all_sims:
      all_sims[uname] = {}
    with open(os.path.join(output_yq_dir, commit), 'r') as f:
      posix_time, commit_hash = commit.split('_')[-2:]
      sims = []
      for line in f.readlines():
        other_f_path, other_f_html, tokens_matched, \
            percent_self, percent_other = line.split(',')
        sims.append((other_f_path, other_f_html, int(tokens_matched),
                      float(percent_self), float(percent_other)))
      all_sims[uname][posix_time] = sims
  print "Finished loading all moss csv files."
  return all_sims

def write_all_moss_similar(moss_dir, year_q, output_dir, use_diff=0):
  moss_dir = os.path.join(moss_dir, year_q)
  add_str = ''
  output_yq_dir = os.path.join(output_dir, year_q, output_moss_dir)
  if use_diff == 1: # only use inserts for now?
    moss_dir = os.path.join(moss_dir, 'insert')
    output_yq_dir = os.path.join(output_yq_dir, 'insert')
    add_str = '_insert'
  elif use_diff == 2:
    moss_dir = os.path.join(moss_dir, 'delete')
    output_yq_dir = os.path.join(output_yq_dir, 'delete')
    add_str = '_delete'
  if not os.path.exists(output_yq_dir):
    os.makedirs(output_yq_dir)
  all_sims = {}
  top_sims = {}
  commit_list = os.listdir(moss_dir)
  commit_list.sort()
  for commit in commit_list:
    uname = commit.split('_')[0]
    if use_diff:
      for line in os.listdir(os.path.join(moss_dir, commit)):
        print use_diff, uname, commit, line
        # do not write similarities per line per commit
        similarities = write_moss_similar(moss_dir, os.path.join(commit, line),
                                            output_dir=None)
        top_sim = moss_top_similar(similarities, commit)
        if top_sim:
          if uname not in all_sims:
            all_sims[uname] = {}
            top_sims[uname] = {}
          if commit not in all_sims[uname]:
            all_sims[uname][commit] = {}
            top_sims[uname][commit] = {}
          all_sims[uname][commit][line] = similarities
          top_sims[uname][commit][line] = top_sim
    else:
      print uname, commit
      # create directory per student.
      similarities = get_moss_similar(moss_dir, commit)
      # save_moss_similar(similarities, commit, output_dir, add_str=''):
      # load top similarity for each.
      top_sim = moss_top_similar(similarities, commit)
      #uname = '_'.join(commit.split('_')[:2]) # ignores additional integer, e.g. uid_1
      if top_sim:
        if uname not in all_sims:
          all_sims[uname] = {}
          top_sims[uname] = {}
        all_sims[uname][commit] = similarities
        top_sims[uname][commit] = top_sim
  
  top_sim_path = os.path.join(output_dir, "%s_top_sim%s.csv" % (year_q, add_str)) 
  write_top_sims_to_file(top_sims, top_sim_path)

header_top_sims = ["uname", "other",
                   "token", "pself", "pother",
                   "step", "time", "hash",
                   "fname", "fpath",
                   "type_other",  "fpath_other", "report"]
def write_top_sims_to_file(top_sims, top_sim_path):
  with open(top_sim_path, 'w') as f:
    f.write('%s\n' % ','.join(header_top_sims))
    for uname in sorted(top_sims.keys()):
      lines = format_top_sims(uname, top_sims[uname])
      f.write('\n'.join(lines) + '\n')

def format_top_sims(uname, commit_dict):
  num_commits = len(commit_dict.keys())
  per_commit = []
  for i, commit in enumerate(sorted(commit_dict.keys())):
    _, posix_time, commit_hash = commit.split('_')
    self_f, fpath_other, report_html, token, pself, pother = commit_dict[commit]
    fname = self_f.split('_')[-1] # e.g., "Breakout"
    tup_other = fpath_other.split('/')
    # /mnt_crypt/socialTrajectories/expanded_mass/final_submissions/2012_1/2012010326
    other_uname = tup_other[-1]
    if 'online' in tup_other:
      type_other = 'online'
    else:
      type_other = 'final_submissions'
    
    per_commit.append(map(str,
      (uname, other_uname, token, pself, pother, i, posix_time,
        commit_hash, fname, commit, type_other, fpath_other, report_html)))
  return [','.join(x) for x in per_commit]

def write_top_sims_to_file_old(top_sims, top_sim_path, use_diff=0):
  with open(top_sim_path, 'w') as f:
    unames = top_sims.keys()
    unames.sort()
    for uname in unames:
      f.write('%s\n' % uname)
      top_commit_list = top_sims[uname].keys()
      top_commit_list.sort()
      for i in range(len(top_commit_list)):
        commit = top_commit_list[i]
        try:
          _,posix_time,_ = commit.split('_')
        except: # probably the baseline case happening, which only has uname
          commit = '%s_%s_%s' % (commit, 0, 0)
          _,posix_time,_ = commit.split('_')
        if use_diff != 0: # several line ranges per commit
          lines = top_sims[uname][commit].keys()
          lines.sort()
          for line in lines:
            f.write('%s,' % commit)
            f.write('%s,%s,%d,%.2f,%.2f' % top_sims[uname][commit][line])
            f.write(',%d,%s' % (i, posix_time))
            f.write(',%s\n' % line)
        else: # one lines per commit
          f.write('%s,' % commit)
          f.write('%s,%s,%d,%.2f,%.2f' % top_sims[uname][commit])
          f.write(',%d,%s\n' % (i, posix_time))
      f.write('\n')
  print "Wrote all top matches in file", top_sim_path

"""
Arg: commit can be a directory, uname_posix_hash/line
uname still will be first element when split by underscore.

Takes similar file and saves to output dir. Also returns list.
Format:
other_f_path, other_f_html, tokens_matched, percent_self, percent_other 

report_html: usually reportX.html
percent_self: the number of tokens over all self's tokens
percent_other: the number of tokens over all other's tokens
"""
def get_moss_similar(moss_dir, commit):
  commit_dir = os.path.join(moss_dir, commit)
  #uname = '_'.join(commit.split('_')[:2]) # ignores additional integer, e.g. uid_1
  uname = commit.split('_')[0] # now only user id anyway
  sim_sum_name = "index.html"
  sim_sum_path = os.path.join(commit_dir, sim_sum_name)
  parser = etree.HTMLParser()
  tree = etree.parse(sim_sum_path, parser)
  t = html.parse(sim_sum_path)

  """
  <tr>
      <td class="rank">7</th>
      <td class="name0"><a href="report7.html">own_commit_file</a></td>
      <td class="percent0">similar_lines_over_own_lines</td>
      <td class="match">tokens_matched</td>
      <td class="percent0">similar_lines_over_final_lines</td>
      <td class="name1"><a href="report7.html">final_file</a></td>
  </tr>
  """
  similarities = []
  # first table, ignore title row
  sim_elts = (t.xpath("/html/body/table")[0]).xpath("tr")[1:]
  for sim_elt in sim_elts:
    self_f = ((sim_elt.find_class("name0"))[0]).xpath("a")[0].text.split('/')[-1]
    rank = int(sim_elt.find_class("rank")[0].text) # ignored
    other_f = ((sim_elt.find_class("name1"))[0]).xpath("a")[0]
    other_f_path, report_html = other_f.text, other_f.get('href')
    
    percent_self, percent_other = [float(elt.text.strip('%')) for elt in \
                sim_elt.find_class("percent0")]
    tokens_matched = int(sim_elt.find_class("match")[0].text)
    if uname not in other_f_path:
      # don't save similarities to your own final submission
      similarities.append((self_f, other_f_path, report_html,
                tokens_matched, percent_self, percent_other))
    # similarities.append((self_f, other_f_path, report_html,
    #           tokens_matched, percent_self, percent_other))
  return similarities


def save_moss_similar(similarities, commit, output_dir, add_str=''):
  output_path = os.path.join(output_dir, '%s%s.csv' % (commit, add_str))
  with open(output_path, 'w') as f:
    for sim in similarities: # ignore rank!!
      f.write('%s,%s,%s,%s,%d,%.2f,%.2f\n' % sim)
      #f.write('%s,%s,%s,%d,%.2f,%.2f\n' % sim) # for baseline
  return similarities
  
def moss_top_similar(similarities, commit):
  if similarities:
    return similarities[0]
  return []
