from helper import *
from git_helper import *
from time import strptime
from datetime import date
from lxml import etree, html

output_moss_dir = "moss"
"""
Overall moss processing function.
"""
def moss_process(moss_dir, year_q, output_dir, final_submissions_dir):
  write_all_moss_similar(moss_dir, year_q, output_dir)
  load_top_sims_from_log(output_dir, year_q)
  all_sims = load_all_sims_from_log(output_dir, year_q)
  return all_sims

def load_top_sims_from_log(output_dir, year_q):
  top_sim_path = os.path.join(output_dir, "top_sim_%s.csv" % year_q) 
  print "load_top_sims_from_log not implemented yet"

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

def write_all_moss_similar(moss_dir, year_q, output_dir):
  moss_dir = os.path.join(moss_dir, year_q)
  output_yq_dir = os.path.join(output_dir, year_q, output_moss_dir)
  if not os.path.exists(output_yq_dir):
    os.makedirs(output_yq_dir)
  all_sims = {}
  top_sims = {}
  for commit in os.listdir(moss_dir):
    print commit
    similarities = write_moss_similar(moss_dir, commit, output_yq_dir)
    top_sim = moss_top_similar(similarities, commit)
    uname = '_'.join(commit.split('_')[:2]) # ignores additional integer, e.g. uid_1
    if top_sim:
      if uname not in all_sims:
        all_sims[uname] = {}
        top_sims[uname] = {}
      all_sims[uname][commit] = similarities
      top_sims[uname][commit] = top_sim
  
  top_sim_path = os.path.join(output_dir, "top_sim_%s.csv" % year_q) 
  with open(top_sim_path, 'w') as f:
    for uname in top_sims:
      f.write('%s\n' % uname)
      for commit in top_sims[uname]:
        f.write('%s,' % commit)
        f.write('%s,%s,%d,%.2f,%.2f\n' % top_sims[uname][commit])
      f.write('\n')
  print "Wrote all top matches in file", top_sim_path
  

"""
Takes similar file and saves to output dir. Also returns list.
Format:
other_f_path, other_f_html, tokens_matched, percent_self, percent_other 

report_html: usually reportX.html
percent_self: the number of tokens over all self's tokens
percent_other: the number of tokens over all other's tokens
"""
def write_moss_similar(moss_dir, commit, output_dir):
  commit_dir = os.path.join(moss_dir, commit)
  uname = '_'.join(commit.split('_')[:2]) # ignores additional integer, e.g. uid_1
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
    rank = int(sim_elt.find_class("rank")[0].text) # ignored
    other_f = ((sim_elt.find_class("name1"))[0]).xpath("a")[0]
    other_f_path, report_html = other_f.text, other_f.get('href')
    
    percent_self, percent_other = [float(elt.text.strip('%')) for elt in \
                sim_elt.find_class("percent0")]
    tokens_matched = int(sim_elt.find_class("match")[0].text)
    if uname not in other_f_path:
      similarities.append((other_f_path, report_html,
                tokens_matched, percent_self, percent_other))

  output_path = os.path.join(output_dir, '%s.csv' % commit)
  with open(output_path, 'w') as f:
    for sim in similarities: # ignore rank!!
      f.write('%s,%s,%d,%.2f,%.2f\n' % sim)
  return similarities
  
def moss_top_similar(similarities, commit):
  if similarities:
    return similarities[0]
  return []
