import os
import numpy as np
from scipy.stats import wilcoxon
from preprocess_per_user import *

# from preprocess_per_user, here for reference
# headers_uname = ['uname',
#         'start_time', 'end_time',
#         'start_day', 'end_day',
#         'num_commits', 'work_hr', 
#         'mt_abs', 'mt_rank', 'f_abs', 'f_rank',
#         'hss_frac', 'hss_time', 'hss_day', 'hss_token', 'hss_pother', 'hss_online', 'hss_true',
#         'ta_time', 'ta_day', # when they first got help during assignment
#         'ta_num', 'ta_hrs', # over the quarter
#         'ta_dur_num', 'ta_dur_hrs', # during the assignment itself
#         'ta_b4_num', 'ta_b4_hrs', # before the assignment deadline
#         'ta_b4_mt_num', 'ta_b4_mt_hrs', # before mt
#         'ta_bt_exam_num', 'ta_bt_exam_hrs'] # between mt and final

workbench_dir = os.path.join(os.getcwd(), 'top_sim')
def load_np(sim_dir, remove_headers=None):
    year_qs = ['2012_1', '2013_1', '2014_1']
    all_uname_info = {}
    for year_q in year_qs:
        all_uname_info.update(load_uname_info(workbench_dir, year_q))
    return uname_info_to_array(all_uname_info)

def bootstrap_on_field(uname_np, field_x, field_ys, bins):
    num_unames = uname_np.shape[0]
    x_np = uname_np[:,get_header_uname_ind(field_x)]
    uname_bin_inds = get_bin_inds(x_np, bins)
    if field_x == 'hss_frac':
        for i, bin_val in enumerate(bins):
            if bin_val == 1.:
                uname_bin_inds[i-1] = np.array(uname_bin_inds[i-1].tolist() + uname_bin_inds[i].tolist())
                uname_bin_inds[i] = []
                print "hss frac", map(len, uname_bin_inds)
                break
    field_inds = map(get_header_uname_ind, field_ys)
    all_things = []
    for uname_bin_ind, bin_i in zip(uname_bin_inds, bins[:-1]):
        sub_np = uname_np[uname_bin_ind,:][:,field_inds]
        if sub_np.shape[0] == 0:
            all_things.append((None, None))
        else:
            boot_samples = bootstrap_multiple(sub_np)
            temp_headers, temp_stats = get_boot_stats(boot_samples, sub_np, field_ys)
            all_things.append((temp_headers, temp_stats))
    return all_things

def get_bins(uname_np, field_x, bin_width):
    x_np = uname_np[:,get_header_uname_ind(field_x)]
    if bin_width == 0:
        print "No bin width specified"
        return []
    min_x, max_x = int(np.amin(x_np)), (int(np.amax(x_np))/bin_width + 2) * bin_width
    bins = np.arange(min_x, max_x+1, bin_width)
    return bins

def get_bin_inds(x_np, bins):
    num_unames = x_np.shape[0]
    hist_vals, bin_edges = np.histogram(x_np, bins)
    print hist_vals
    print bin_edges
    digits = np.digitize(x_np, bins)

    uname_bin_inds = [0]*(len(bins)-1)
    for i, bin_i in enumerate(range(1, len(bins))):
        uname_bin_inds[i] = np.arange(num_unames)[digits == bin_i]
    return uname_bin_inds

def bootstrap_multiple(sub_np, b=1000):
    m = sub_np.shape[0]
    sample_inds = np.random.choice(range(m), size=(b,m), replace=True)
    all_samples = sub_np[sample_inds,:]
    return all_samples
    
def get_boot_stats(boot_samples, orig_np, field_ys):
    # [b,num_unames_in_bin,num_field_ys]
    actual_mean = np.average(orig_np, axis=0)
    boot_means = np.average(boot_samples, axis=1)
    boot_mean = np.average(boot_means, axis=0)
    boot_se = np.std(boot_means, axis=0)
    lower, upper = 2.5, 97.5
    lower_percentile = np.percentile(boot_means, lower, axis=0)
    upper_percentile = np.percentile(boot_means, upper, axis=0)
    headers_by_field = [0]*len(field_ys)
    stats_by_field = [0]*len(field_ys)
    for i, field_y in enumerate(field_ys):
        headers_by_field[i] = ["orig mean", "boot mean", "boot SE",
                    "CI %f" % lower, "CI %f" % upper]
        stats_by_field[i] = [actual_mean[i], boot_mean[i], boot_se[i],
                lower_percentile[i], upper_percentile[i]]
    return headers_by_field, stats_by_field

def write_tsv(fpath, tuple_list):
    with open(fpath, 'w') as f:
        f.write('\n'.join(['\t'.join(map(str, item)) for item in tuple_list]))
        print "Wrote tsv to %s" % fpath

def prepare_stats_for_writing(headers_and_stats_per_bin, bins, field_ys):
    all_bin_header_stats = [0]*(2*len(field_ys))
    for j, field_y in enumerate(field_ys):
        # add field name header
        all_bin_header_stats[2*j] = [field_y]
        all_bin_header_stats[2*j+1] = ['']

    for i, (h, s) in enumerate(headers_and_stats_per_bin):
        # add bin range
        for j, _ in enumerate(field_ys):
            all_bin_header_stats[2*j].append(bins[i])
            all_bin_header_stats[2*j+1].append(bins[i+1])
            if h is not None and s is not None:
                all_bin_header_stats[2*j] += h[j]
                all_bin_header_stats[2*j+1] += s[j]
    return all_bin_header_stats

def prepare_stats_for_graphing(headers_and_stats_per_bin, bins, field_ys):
    nz_inds = []
    for i, (h, s) in enumerate(headers_and_stats_per_bin):
        if h is not None and s is not None:
            nz_inds.append(i)
    headers_and_stats_per_bin = [headers_and_stats_per_bin[i] for i in nz_inds]
    bins = [bins[i] for i in nz_inds]
    all_graph_stats = [['']]
    for i, (h, s) in enumerate(headers_and_stats_per_bin):
        all_graph_stats.append([bins[i]])
    print "prior", all_graph_stats
    stat_inds = [-2, -1, 0, 2] # 2.5, 97.5, original mean, boot se
    for j, field_y in enumerate(field_ys):
        # 2 rows per bin...
        # for i, (h, s) in enumerate(headers_and_stats_per_bin):
        #     all_graph_stats[i+1].append('') # because field_y takes up one row
        #     for stat_ind in stat_inds[:-1]:
        #         all_graph_stats[0].append(bins[i])
        #         for k, _ in enumerate(headers_and_stats_per_bin):
        #             if i == k:
        #                 all_graph_stats[k+1].append(s[j][stat_ind])
        #             else:
        #                 all_graph_stats[k+1].append('')

        # one row...graph percentile as err bar and A-OK
        all_graph_stats[0].append(field_y)
        all_graph_stats[0] += ['CI 2.5', 'CI 97.5', 'mean', 'boot se']
        for i, (h, s) in enumerate(headers_and_stats_per_bin):
            all_graph_stats[i+1].append('') # because field_y takes up one row
            for stat_ind in stat_inds:
                all_graph_stats[i+1].append(s[j][stat_ind])

    print map(len, all_graph_stats)

    # for j, field_y in enumerate(field_ys):
    #     # add field name header
    #     all_graph_stats[j+1] = [field_y]

    # for i, (h, s) in enumerate(headers_and_stats_per_bin):
    #     if h is None or s is  None: continue
    #     for stat_ind in [-2, -1, 0]: # 2.5, 97.5, original mean
    #         all_graph_stats[0].append(bins[i])
    #         for j, _ in enumerate(field_ys):
    #             all_graph_stats[j+1].append(s[j][stat_ind])
    return all_graph_stats

def save_boot_stats(uname_np, field_x, field_ys, bins, prefix=None):
    if not prefix:
        prefix = ''
    else:
        prefix = '%s_' % prefix
    all_things = bootstrap_on_field(uname_np, field_x, field_ys, bins)
    cols_to_write = prepare_stats_for_writing(all_things, bins, field_ys)
    write_tsv(os.path.join(workbench_dir, '%sstats_%s.tsv' % (prefix, field_x)),
        zip(*cols_to_write))
    cols_to_write = prepare_stats_for_graphing(all_things, bins, field_ys)
    write_tsv(os.path.join(workbench_dir, '%sgraphs_%s.tsv' % (prefix, field_x)),
        zip(*cols_to_write))

    
def separate_by_field(uname_np, binary_field):
    binary_np = uname_np[:,get_header_uname_ind(binary_field)]
    binary_options = sorted(np.unique(binary_np).tolist())
    if len(binary_options) != 2:
        return "not binary field"
    false_opt, true_opt = binary_options
    false_np = uname_np[binary_np == false_opt,:]
    true_np = uname_np[binary_np == true_opt,:]
    return false_np, true_np
    
def save_hss_stats(uname_np, field_xs, field_ys, bin_xs_all):
    non_hss_np, hss_np = separate_by_field(uname_np, 'hss_true')
    print "non hss", non_hss_np.shape, "hss", hss_np.shape, "orig", uname_np.shape
    for field_x, bin_xs in zip(field_xs, bin_xs_all):
        save_boot_stats(non_hss_np, field_x, field_ys, bin_xs, prefix='non')
        save_boot_stats(hss_np, field_x, field_ys, bin_xs, prefix='hss')
    offline_hss_np, online_hss_np = separate_by_field(hss_np, 'hss_online')
    print "offline shape", offline_hss_np.shape, "online shape", online_hss_np.shape

    # run only for hss frac
    field_xs = ['hss_frac']
    field_ys += ['hss_frac', 'hss_pother', 'hss_day']
    bin_xs_all = [get_bins(hss_np, 'hss_frac', .2)]
    for field_x, bin_xs in zip(field_xs, bin_xs_all):
        save_boot_stats(online_hss_np, field_x, field_ys, bin_xs, prefix='online')
        save_boot_stats(offline_hss_np, field_x, field_ys, bin_xs, prefix='offline')


if __name__ == '__main__':
    uname_np = load_np(workbench_dir) 
    field_xs = ['start_day', 'num_commits', 'work_hr']
    field_ys = ['start_day', 'num_commits', 'work_hr', 'mt_rank', 'f_rank',
            'ta_hrs', 'ta_dur_hrs', 'ta_b4_mt_hrs', 'ta_bt_exam_hrs']
    bin_widths = [1, 50, 5]
    bin_xs_all = [get_bins(uname_np, field_x, bin_width) \
            for field_x, bin_width in zip(field_xs, bin_widths)]
    for field_x, bin_xs in zip(field_xs, bin_xs_all):
        save_boot_stats(uname_np, field_x, field_ys, bin_xs)
    save_hss_stats(uname_np, field_xs, field_ys, bin_xs_all)
