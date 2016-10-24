from helper import *
from git_helper import *
from moss_tool import *
from ta_stats import *
import matplotlib.colors as cl
import matplotlib.cm as cmx
from comp_stats import *

# cross validation information
from sklearn.model_selection import KFold, cross_val_score
from sklearn.metrics import precision_recall_curve
from sklearn import linear_model

# collaboration
uname_ind, grp_ind, num_sims_ind = 0, 1, 2
frac_sims_ind, b4_frac_sims_ind, after_frac_sims_ind = 3, 4, 5
max_t_ind, max_ps_ind, max_po_ind = 6, 7, 8
avg_t_ind, avg_ps_ind, avg_po_ind = 9, 10, 11
start_sim_posix_ind, end_sim_posix_ind = 12, 13
# all
start_posix_ind, end_posix_ind = 14, 15
commits_ind, hrs_ind = 16, 17
avg_work_ind, max_work_ind = 18, 19
# ta
ta_visits_ind, ta_hrs_ind = 20, 21
ta_v_during_ind, ta_h_during_ind = 22, 23
ta_v_b4_ind, ta_h_b4_ind = 24, 25
# grades
assgt1_g_ind, assgt1_r_ind = 26, 27
assgt2_g_ind, assgt2_r_ind = 28, 29
assgt3_g_ind, assgt3_r_ind = 30, 31
mt_g_ind, mt_r_ind = 32, 33
f_g_ind, f_r_ind = 34, 35
gr_st_ind = assgt3_g_ind # always have gr_end be the last in the list
last_ind = f_r_ind

titles = []
titles += ['uname', 'grp', 'n_sims']
titles += ['frac', 'b4_frac', 'after_frac']
titles += ['max_t', 'max_ps', 'max_po']
titles += ['avg_t', 'avg_ps', 'avg_po']
titles += ['st_sim', 'end_sim']
titles += ['st', 'end']
titles += ['commits', 'hrs']
titles += ['avg sess', 'max sess']
titles += ['ta visits', 'ta hrs']
titles += ['ta visits during', 'ta hrs during']
titles += ['ta visits before', 'ta hrs before']
titles += ['1_abs', '1_rnk', '2_abs', '2_rnk']
titles += ['3_abs', '3_rnk', 'mt_abs', 'mt_rnk', 'f_abs', 'f_rnk']

def cvmodel(output_dir, year_q=None):
  global titles
  year_q_list = []
  if not year_q:
    year_q_list = ['2012_1', '2013_1', '2014_1']
  else:
    year_q_list = [year_q]
  print "year_q_list", year_q_list
  # for year_q in year_q_list:
  #   filter_process(output_dir, year_q)

  num_groups = 4
  day_range = get_day_range(max(year_q_list), plus_minus=(0,3),incr=day_length)
  divs = np.linspace(0,len(day_range)-1,num=num_groups+1).astype(int)
  divs[-1] = len(day_range) # add one day onto the end

  info, non_info = load_info_noninfo(output_dir, year_q_list)
  info_np = np.array(info)
  non_info_np = np.array(non_info)
  
  all_info_np = np.array(info + non_info)

  feature_inds = [avg_t_ind, avg_po_ind, commits_ind, ta_h_b4_ind, ta_h_during_ind, hrs_ind, assgt1_r_ind, assgt2_r_ind]
  # feature_inds = [commits_ind, ta_h_b4_ind, ta_h_during_ind, hrs_ind, assgt1_r_ind, assgt2_r_ind]
  Y = np.array(np.ones(len(info)).tolist() + np.zeros(len(non_info)).tolist())

  tot_studs = len(info) + len(non_info)
  # use the same shuffle for everyone
  shuffle_inds = range(tot_studs)
  np.random.shuffle(shuffle_inds)
  Y = Y[shuffle_inds]
  print "shuffled Y", Y
  print " no work limit"
  per_year_stats(year_q_list, info, non_info)

  day_bounds = []
  X_groups = []
  for i in range(num_groups):
    if i == 0:
      bound_st = day_range[0]
      bound_end = day_range[divs[i+1]]
    elif i == num_groups - 1:
      bound_st = day_range[divs[i]-1]
      bound_end = day_range[-1]+1
    else:
      bound_st = day_range[divs[i]-1]
      bound_end = day_range[divs[i+1]]
    day_bounds.append((bound_st, bound_end))

  print map(posix_to_datetime, day_range)
  info_list = []
  for bound_st, bound_end in day_bounds:
    info, non_info = load_info_noninfo(output_dir, year_q_list, work_limit=bound_end)
    info_list.append((info, non_info))
    info_np = np.array(info)
    non_info_np = np.array(non_info)
    all_info_np = np.array(info + non_info)

    print "work limit", bound_end
    print map(lambda ind: titles[ind], feature_inds)
    per_year_stats(year_q_list, info, non_info)

    nz_start = (all_info_np[:,start_posix_ind] < bound_end).tolist()
    nz_end = (all_info_np[:,end_posix_ind]  < bound_end).tolist()
    bools = np.array(zip(nz_start, nz_end))

    print bools.shape, all_info_np[:,feature_inds].shape
    features_only = np.hstack([all_info_np[:,feature_inds],bools])
    print features_only.shape

    X = features_only[shuffle_inds,:] # shuffle the same way every time

    X_groups.append(X)

  print "\n\n\n\n"
  k_fold = KFold(n_splits=3)
  kfold_split = []
  for i in range(num_groups):
    kfold_split.append([])
    for train_indices, test_indices in k_fold.split(X_groups[i]):
      kfold_split[i].append((X_groups[i][train_indices,:], Y[train_indices], X_groups[i][test_indices,:], Y[test_indices]))

  fig = plt.figure()
  ax = plt.gca()
  colors = ['r', 'g', 'b', 'm']
  shapes = ['^', 'o', 's', 'p']
  legend_items = []
  legend_str = []

  cols = []
  col_headers = []
  col_headers2 = []
  for i in range(num_groups):
    bound_st, bound_end = day_bounds[i]
    print i, map(posix_to_datetime, [bound_st, bound_end])
    info, non_info = info_list[i]
    per_year_stats(year_q_list, info, non_info)
    kf_split_group = kfold_split[i]
    all_preds = []
    all_tests = []

    # train model
    for j, (X_train, y_train, X_test, y_test) in enumerate(kf_split_group):
      print "time", i, "fold", j
      print "nonzero cheaters: train %s/%s, test %s/%s" % (len(np.nonzero(y_train)[0].tolist()), len(y_train.tolist()), len(np.nonzero(y_test)[0].tolist()), len(y_test.tolist()))
      #lr = linear_model.LinearRegression()
      lr = linear_model.LogisticRegression(C=100.0)
      lr.fit(X_train, y_train)
      y_pred = lr.predict(X_test) # between 0 and 1, X*h + b
      y_prob = lr.predict_proba(X_test)[:,1] # first col is "0" prob, vs "1" prob
      cheaters = np.nonzero(y_test)[0]
      print "prediction", np.array(zip(y_test[cheaters].tolist(), y_pred[cheaters].tolist(), y_prob[cheaters].tolist()))
      err = np.mean((y_pred - y_test)**2)
      y_pred_train = lr.predict(X_train)
      err_train = np.mean((y_pred_train - y_train)**2)
      var = lr.score(X_test, y_test)

      all_tests += y_test.tolist()
      all_preds += y_prob.tolist()
      
      print "lr's mean sq err", err, "score ", var, "train err", err_train
      print

    col_headers.append(','.join(map(str, (bound_st, bound_end, get_t_minus(bound_st, max(year_q_list)), get_t_minus(bound_end, max(year_q_list))))))
    col_headers2 += ['recall', 'precision', 'thresholds']
    precision, recall, thresholds = precision_recall_curve(all_tests, all_preds)#y_test, y_prob)
    cols.append(recall)
    cols.append(precision)
    cols.append(thresholds)
    label = 'time %s kfold ' % (i)
    leg = ax.plot(recall, precision, marker=shapes[i], color=colors[i], label=label,alpha=0.7)
    legend_items.append(leg)
    legend_str.append(label)

    cv_scores = cross_val_score(linear_model.LinearRegression(), X_groups[i], Y)
    print "cross val scores", cv_scores
    print "cv mean: %s, cv stdev: %s" % (np.mean(cv_scores), np.std(cv_scores))
    print
    print
    print

  #ax.legend()
  ax.set_xlabel('Recall')
  ax.set_ylabel('Precision')
  fig_dest = os.path.join(output_dir, '%s_precisionrecall.png' % '_'.join(year_q_list))
  print "Saving fig dest", fig_dest
  fig.savefig(fig_dest)
  plt.close(fig)

  with open(os.path.join(output_dir, '%s_precisionrecall.csv' % '_'.join(year_q_list)), 'w') as f:
    f.write('%s\n' % ','.join(col_headers))
    f.write('%s\n' % ','.join(col_headers2))
    rows = []
    for i in range(max(map(len, cols))):
      item = []
      for j in range(len(cols)):
        if i < len(cols[j]):
          item.append(cols[j][i])
        else:
          item.append('')
      rows.append(','.join(map(str, item)))

    f.write('\n'.join(rows))
    print "Saving csv file", f.name
