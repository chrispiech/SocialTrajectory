from helper import *
from git_helper import *
from time import strptime
from datetime import datetime
from moss_tool import *
import matplotlib.colors as cl
import matplotlib.cm as cmx

def create_gephi(output_dir, year_q):
  top_sims = load_top_sims_from_log(output_dir, year_q)
  uname_to_id = load_uname_to_id_lookup()
  nodes = node_gephi_format(top_sims, uname_to_id)
  edges = edge_gephi_format(top_sims, uname_to_id, nodes)
  static_edges = edge_static_format(top_sims, uname_to_id, nodes)
  # write
  write_nodes_to_csv(output_dir, year_q, nodes)
  write_edges_to_csv(output_dir, year_q, edges)
  write_static_edges_to_csv(output_dir, year_q, static_edges)

def posix_to_time_gephi(posix_time):
  posix_time = int(posix_time) # in case fed a string
  return datetime.fromtimestamp(posix_time).strftime('%Y-%m-%dT%H:%M:%S')

"""
Create an array per uname (node) and puts it in a dictionary.
Contains uid (not uname!) and first commit time.
Node label is also uid, not uname.
"""
def node_gephi_format(top_sims, uname_to_id):
  init_format = {}
  for uname in top_sims:
    init_commit_posix = min([int(posix_time) for posix_time in top_sims[uname]])
    init_commit_time = posix_to_time_gephi(init_commit_posix)
    #uid = uname_to_id[uname]
    uid = uname[6:]
    init_format[uid] = [uid, init_commit_time]
    #print "uname %s, id %s, %s, %s" % (uname, uname_to_id[uname], init_commit_posix, init_commit_time)
  for uname in uname_to_id:
    uid = uname_to_id[uname]
    if uid not in init_format and 'online' in uid:
      init_format[uid] = [uid, '', 'online']
  return init_format

def write_nodes_to_csv(output_dir, year_q, nodes):
  node_csv = os.path.join(output_dir, '%s_nodes.csv' % year_q)
  with open(node_csv, 'w') as f:
    f.write('Id,Label,Time,Online\n')
    nodes_keys = nodes.keys()
    nodes_keys.sort()
    for uid in nodes_keys:
      #print "attn", uid, nodes[uid]
      f.write(','.join(map(str, [uid] + nodes[uid])) + '\n')
    print "Nodes written to %s" % node_csv

def write_edges_to_csv(output_dir, year_q, edges):
  edge_csv = os.path.join(output_dir, '%s_edges.csv' % year_q)
  with open(edge_csv, 'w') as f:
    f.write('Id,Label,Source,Target,Start,End,Token,PercentSelf,Commit,Online\n')
    for edge_id in edges:
      f.write(','.join(map(str, [edge_id] + edges[edge_id])) + '\n')
    print "Edges written to %s" % edge_csv
    
"""
Create an array per edge and puts it in a dictionary.
label: uid1_commitposix
src: uid1
dst: uid2 (person to similarity)
start: commit time
end: next commit time
attribute1: tokens
attribute2: percent similarity
attribute3: online

If username is not defined, add it (and make a print note)
"""
def edge_gephi_format(top_sims, uname_to_id, nodes):
  edges = {}
  for uname in top_sims:
    all_posix = np.array([int(commit_posix) for commit_posix in top_sims[uname]])
    all_posix = all_posix[all_posix.argsort()]
    #uid = uname_to_id[uname]
    uid = uname
    print "uid", uid, uname
    for i in range(len(top_sims[uname])):
      commit_posix = all_posix[i]
      commit_time = posix_to_time_gephi(commit_posix)
      other_uname, tokens, percent, _, commit_num, commit_hash = top_sims[uname][str(commit_posix)]
      #   uname_to_id[other_uname] = len(uname_to_id)
      #   other_uid = uname_to_id[other_uname]
      #   nodes[other_uid] = [other_uid, '']
      #   if 'online' in other_uname:
      #other_uid = uname_to_id[other_uname]
      other_uid = other_uname
      if 'online' not in other_uid:
        other_uid = other_uid[6:]
      if other_uid in uname_to_id: other_uid = uname_to_id[other_uid]
      other_uid = other_uid.split('_')[-1]
      edge_id = "%s_%s_%s" % (uid, commit_posix, commit_hash)
      edges[edge_id] = [edge_id, uid, other_uid, commit_time]
      if i+1 != len(top_sims[uname]):
        next_commit_posix = all_posix[i+1]
        next_commit_time = posix_to_time_gephi(next_commit_posix)
        edges[edge_id].append(next_commit_time)
      else:
        edges[edge_id].append('')

      edges[edge_id].append(tokens)
      edges[edge_id].append(percent)
      edges[edge_id].append(commit_num)
      if 'online' in other_uid:
        edges[edge_id].append('online')
  return edges

def edge_static_format(top_sims, uname_to_id, nodes, token_thresh=100):
  token_weights = {}
  for uname in top_sims:
    orig_uname = uname
    uname = uname[6:]
    token_weights[uname] = {}
    for commit_posix in top_sims[orig_uname]:
      other_uname, tokens, percent, _, _, _ = top_sims[orig_uname][commit_posix]
      if 'online' not in other_uname:
        other_uname = other_uname[6:]
      if other_uname in uname_to_id: other_uname = uname_to_id[other_uname]
      other_uname = other_uname.split('_')[-1]
      if tokens > token_thresh:
        if other_uname not in token_weights[uname]:
          token_weights[uname][other_uname] = 0
        token_weights[uname][other_uname] += 1
  edges = {}
  max_all_counts = np.amax(np.array([token_weights[uname][other_uname] for uname in token_weights for other_uname in token_weights[uname] ]))
  print "maximum count", max_all_counts
  for uname in token_weights:
    other_unames = [other_uname for other_uname in token_weights[uname]]
    if not other_unames: continue
    counts = np.array([token_weights[uname][other_uname] for other_uname in other_unames])
    tot_counts = np.sum(counts)
    count_weights = counts.astype(float)/max_all_counts
    count_local_weights = counts.astype(float)/np.amax(counts)
    for i in range(len(counts)):
      other_uname = other_unames[i]
      weight = count_weights[i]
      edge_id = "%s_%s" % (uname, other_uname)
      online_str = ''
      if 'online' in other_uname: online_str = 'online'
      edges[edge_id] = [edge_id, uname, other_uname, counts[i], count_local_weights[i], count_weights[i], online_str]
  return edges

def write_static_edges_to_csv(output_dir, year_q, edges):
  edge_csv = os.path.join(output_dir, '%s_edges_static.csv' % year_q)
  with open(edge_csv, 'w') as f:
    f.write('Id,Label,Source,Target,Count,Weight,NormWeight,Online\n')
    edge_keys = edges.keys()
    edge_keys.sort()
    for edge_id in edge_keys:
      f.write(','.join(map(str, [edge_id] + edges[edge_id])) + '\n')
    print "Edges written to %s" % edge_csv

"""
other ids written on bent piece of paper
(1) dynamic: for all current times, add weights for edges that are
  larger than a certain threshold (for tokens)
(2) over all times, weight = count(sim>= token_thresh)
(3) over all times, all token counts and if online, put in red 
"""
