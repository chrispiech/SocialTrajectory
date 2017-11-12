from outliers_util import *
from stats_util import *
from preprocess import *
import stats_util
from helper import *
from git_helper import *
from time import strptime
from datetime import date
import time

fname = 'all_maxes_new_new.csv'
moss_dir = 'moss_mass'

def load_top_sims_original(year_q):
    top_sims = {}
    with open(os.path.join('proc_output', '%s_top_sim_new.csv' % year_q), 'r') as f:
        line = f.readline() # headers
        line = f.readline()
        while line:
            fields = (line.strip()).split(',')
            uname = fields[0]
            if uname not in top_sims:
                top_sims[uname] = []
            top_sims[uname].append(fields)

            line = f.readline()
    return top_sims

def get_token_count(report_fpath):
  """
  <tr>
    <th>2012010000_1351053262_a9835d2_Breakout:</th>
    <th>Match:</th>
    <th>/mnt_crypt/socialTrajectories/expanded_mass/final_submissions/2012_1/2012010231_Breakout:</th>
  </tr>
  <tr>
    <td>19.87%</td>
    <td>181 (+ 162 common)</td>
    <td>19.98%</td>
  </tr>
  """
  t = html.parse(report_fpath)
  header_div = t.find("//div[@class='header']")
  summary_table = header_div.findall("table[@class='summary']")[0]
  stats_tr = summary_table.xpath("tr")[1]
  _, tokens_td, _ = stats_tr.xpath("td")
  # 181 (+ 162 common)
  tokens_str, common_str = tokens_td.text_content().split('(+')
  tokens_str = tokens_str.strip()
  common_str = common_str.split('common')[0].strip()
  return int(tokens_str), int(common_str)

def get_percents(report_fpath):
  t = html.parse(report_fpath)
  header_div = t.find("//div[@class='header']")
  summary_table = header_div.findall("table[@class='summary']")[0]
  stats_tr = summary_table.xpath("tr")[1]
  pself_td, tokens_td, pother_td = stats_tr.xpath("td")
  pself_str = pself_td.text_content().split('%')[0]
  pother_str = pother_td.text_content().split('%')[0]
  return float(pself_str), float(pother_str)

def get_lines(report_fpath):
  t = html.parse(report_fpath)
  content_div = t.find("//div[@class='content']")
  self_spans = content_div.find("div[@id='file0']")
  self_lineno_spans = self_spans.find_class("lineno")
  self_len = len(self_lineno_spans)

  other_spans = content_div.find("div[@id='file1']")
  other_lineno_spans = other_spans.find_class("lineno")
  other_len = len(other_lineno_spans)
  return self_len, other_len

"""
percent: pself or pother (max is 100)
shared_tokens: moss identified tokens
common_tokens: matched from starter code
"""
import math
def get_tot_tokens(percent, shared_tokens, common_tokens):
  return int(math.ceil(shared_tokens/(percent/100) + common_tokens))

def get_token_lens(uname, other, fname, report):
  year, q = uname[:4], uname[4:6] # 201201
  year_q = '%s_%s' % (int(year), int(q))
  commit_dir = os.path.join(moss_dir, year_q, fname)
  report_fpath = os.path.join(commit_dir, report)
  shared_tokens, common_tokens = get_token_count(report_fpath)
  pself, pother = get_percents(report_fpath)
  self_len, other_len = get_lines(report_fpath)
  self_tokens = get_tot_tokens(pself, shared_tokens, common_tokens)
  other_tokens = get_tot_tokens(pother, shared_tokens, common_tokens)

  return shared_tokens, common_tokens, pself, pother, \
      self_len, other_len, self_tokens, other_tokens, \
      other, fname, report


def get_token_lens_headers():
  return ["t", "tc", "ps", "po", \
      "lens", "leno", "lents", "lento", \
      "other", "fname", "report"]

top_sims = {}
year_qs = ['2012_1', '2013_1', '2014_1']
for year_q in year_qs:
    top_sims_year_q = load_top_sims_original(year_q)
    preprocess_top_sims(top_sims_year_q)
    top_sims.update(top_sims_year_q)

field_ys = ['pself', 'pother', 'token']
top_sims_arr = top_sims_to_array(top_sims, 'norm_step', field_ys)
max_tokens, max_pothers = get_max_token_pother(top_sims_arr)
headers, all_items = get_avg_and_max_full(top_sims_arr, ['pother', 'token'])
pother_ind, token_ind, fpath_ind = map(get_header_ind, ['pother', 'token', 'fpath'])
pself_ind, other_ind = get_header_ind('pself'), get_header_ind('other')
report_ind = get_header_ind('report')
new_items = []

pother_headers = ['pother_%s' % header for header in get_token_lens_headers()]
token_headers = ['token_%s' % header for header in get_token_lens_headers()]
new_headers = ['uname'] + pother_headers + token_headers
for i, (uname, pother_po, pother_t, token_po, token_t) in enumerate(all_items):
    sys.stdout.write("{}/{} {}\r".format(i, len(all_items), uname))
    sims_uname = top_sims[uname]
    pother_sims = filter(lambda item: float(item[pother_ind]) == pother_po and float(item[token_ind]) == pother_t, sims_uname)
    pother_first_sim = pother_sims[0]
    pother_fname = pother_first_sim[fpath_ind]
    pother_report = pother_first_sim[report_ind]
    pother_other = pother_first_sim[other_ind]
    
    pother_tup = get_token_lens(uname, pother_other, pother_fname, pother_report)
    
    token_sims = filter(lambda item: float(item[pother_ind]) == token_po and float(item[token_ind]) == token_t, sims_uname)
    token_first_sim = token_sims[0]
    token_fname = token_first_sim[fpath_ind]
    token_report = token_first_sim[report_ind]
    token_other = token_first_sim[other_ind]
    token_t, token_ps, token_po = [token_first_sim[item] for item in [token_ind, pself_ind, pother_ind]]

    token_tup = get_token_lens(uname, token_other, token_fname, token_report)
    new_items.append([uname] + list(pother_tup) + list(token_tup))

sys.stdout.write('\n')
all_items, headers = new_items, new_headers
with open('all_maxes_len.csv', 'w') as f:
    f.write('{}\n'.format(','.join(headers)))
    f.write('\n'.join([','.join(map(str, item)) for item in all_items]))
    print "Wrote csv to", f.name

