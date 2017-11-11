import os
import sys
import numpy as np
import pandas as pd
import helper
import ta_stats
from scipy.signal import medfilt
from scipy.optimize import curve_fit
from preprocess import *

sim_dir = os.path.join(os.getcwd(), 'top_sim_new')
lair_dir = os.path.join(os.getcwd(), 'lair')
nonsense_day = 12345 # must be gibberish days, since we are using t-minus T_T
headers_uname = ['uname',
        'start_time', 'end_time',
        'start_day', 'end_day',
        'num_commits', 'work_hr', 
        'mt_abs', 'mt_rank', 'f_abs', 'f_rank',
        'hss_frac', 'hss_time', 'hss_day', 'hss_token', 'hss_pother', 'hss_online','hss_true',
        'ta_time', 'ta_day', # when they first got help during assignment
        'ta_num', 'ta_hrs', # over the quarter
        'ta_dur_num', 'ta_dur_hrs', # during the assignment itself
        'ta_b4_num', 'ta_b4_hrs', # before the assignment deadline
        'ta_b4_mt_num', 'ta_b4_mt_hrs', # before mt
        'ta_bt_exam_num', 'ta_bt_exam_hrs'] # between mt and final

def get_header_uname_ind(field):
    return headers_uname.index(field)

def get_generic_ind(gen_headers, field):
    return gen_headers.index(field)

def add_field(arr, ind, val):
    if type(val) is float:
        val = '%.4f' % val
    if len(arr) <= ind:
        for i in range(len(arr), ind+1):
            arr.append('-1')
    arr[ind] = str(val)

def remove_ungraded(uname_info, year_q):
    unames = uname_info.keys()
    unames_removed = []
    f_rank_ind = get_header_uname_ind('f_rank')
    for uname in unames:
        if int(float(uname_info[uname][f_rank_ind]))== -1:
            del(uname_info[uname])
            unames_removed.append(uname)
    print "unames removed:", sorted(unames_removed)

def preprocess_uname_info(uname_info, year_q):
    top_sims = load_top_sims(year_q)
    day_length = helper.day_length
    def time_things(uname):
        sims_uname = top_sims[uname]
        time_ind = get_header_ind('time')
        sim_times = [int(sim[time_ind]) for sim in sims_uname]

        start_time = min(sim_times)
        end_time = max(sim_times)
        num_commits = len(sim_times)
        work_hr, _ = helper.get_hours(sim_times)

        add_field(uname_info[uname], get_header_uname_ind('start_time'), start_time)
        add_field(uname_info[uname], get_header_uname_ind('end_time'), end_time)
        add_field(uname_info[uname], get_header_uname_ind('num_commits'), num_commits)
        add_field(uname_info[uname], get_header_uname_ind('work_hr'), work_hr)

    extra_days=2
    posix_range = helper.get_day_range(year_q,plus_minus=[0,extra_days], incr=day_length)
    day_range = [int(helper.get_t_minus(posix_time, year_q).split('T')[-1]) for posix_time in posix_range]
    day_range= np.array(day_range)
    print "day range", day_range
    def get_t_minus_days(arr):
        # start_time_bound = helper.all_startend_times[year_q][helper.START_TIME]
        # end_time_bound = helper.all_startend_times[year_q][helper.END_TIME] + 2*day_length
        # bin[i-1] < x < bin[i]
        arr_day_inds = np.digitize(arr, posix_range) - 1
        arr_days = day_range[arr_day_inds]
        return arr_days

    def advanced_time_things():
        unames = sorted(uname_info.keys())
        start_ind = get_header_uname_ind('start_time')
        end_ind = get_header_uname_ind('end_time')
        start_times = [uname_info[uname][start_ind] for uname in unames]
        end_times = [uname_info[uname][end_ind] for uname in unames]

        start_days = get_t_minus_days(start_times)
        end_days = get_t_minus_days(end_times)
        
        for i, uname in enumerate(unames):
            add_field(uname_info[uname], get_header_uname_ind('start_day'), start_days[i])
            add_field(uname_info[uname], get_header_uname_ind('end_day'), end_days[i])

    def grade_things():
        mt_ind, f_ind = -2, -1
        gr = helper.load_all_graderanks('', year_q)
        for uname in uname_info:
            mt_abs, mt_rank, f_abs, f_rank = [-1]*4
            if uname in gr:
                gr_uname_abs, gr_uname_rank = gr[uname]
                mt_abs, mt_rank = gr_uname_abs[mt_ind], gr_uname_rank[mt_ind]
                f_abs, f_rank = gr_uname_abs[f_ind], gr_uname_rank[f_ind]
            add_field(uname_info[uname], get_header_uname_ind('mt_abs'), mt_abs)
            add_field(uname_info[uname], get_header_uname_ind('mt_rank'), mt_rank)
            add_field(uname_info[uname], get_header_uname_ind('f_abs'), f_abs)
            add_field(uname_info[uname], get_header_uname_ind('f_rank'), f_rank)


    def hss_things(uname):
        hss_frac, hss_time, hss_day = 0, -1, nonsense_day
        hss_token, hss_pother = 0, 0
        hss_online = 0
        hss_true = 0
        if uname in outlier_dict:
            hss_frac = outlier_dict[uname][get_generic_ind(hss_headers, 'hss_frac')]
            hss_time = outlier_dict[uname][get_generic_ind(hss_headers, 'hss_time')]
            hss_day = get_t_minus_days([hss_time])[0]
            hss_token = outlier_dict[uname][get_generic_ind(hss_headers, 'hss_token')]
            hss_pother = outlier_dict[uname][get_generic_ind(hss_headers, 'hss_pother')]
            hss_online = outlier_dict[uname][get_generic_ind(hss_headers, 'hss_online')]
            hss_true = 1

        add_field(uname_info[uname], get_header_uname_ind('hss_frac'), hss_frac)
        add_field(uname_info[uname], get_header_uname_ind('hss_time'), hss_time)
        add_field(uname_info[uname], get_header_uname_ind('hss_day'), hss_day)
        add_field(uname_info[uname], get_header_uname_ind('hss_token'), hss_token)
        add_field(uname_info[uname], get_header_uname_ind('hss_pother'), hss_pother)
        add_field(uname_info[uname], get_header_uname_ind('hss_online'), hss_online)
        add_field(uname_info[uname], get_header_uname_ind('hss_true'), hss_true)

    def ta_things():
        ta_types = ['ta', 'ta_dur', 'ta_b4', 'ta_b4_mt', 'ta_bt_exam']
        for ta_type_ind, ta_type in enumerate(ta_types):
            ta_dict = ta_stats.get_ta_stats_only('', year_q, ta_bounds=ta_type_ind)

            for uname in uname_info:
               ta_num, ta_hrs = 0, 0
               if uname in ta_dict:
                   ta_num, ta_hrs = ta_dict[uname]
               add_field(uname_info[uname], get_header_uname_ind('%s_num' % ta_type), ta_num)
               add_field(uname_info[uname], get_header_uname_ind('%s_hrs' % ta_type), ta_hrs)
        # add ta start times during assignment
        ta_st_time_dict = ta_stats.get_ta_start_time('', year_q)
        unames = sorted(uname_info.keys())
        dependent_unames = filter(lambda uname: uname in ta_st_time_dict, unames)
        independent_unames = filter(lambda uname: uname not in ta_st_time_dict, unames)
        ta_st_times = [ta_st_time_dict[uname] for uname in dependent_unames]
        ta_st_days = get_t_minus_days(ta_st_times)
        for uname, ta_time, ta_day in zip(dependent_unames, ta_st_times, ta_st_days):
            add_field(uname_info[uname], get_header_uname_ind('ta_time'), ta_time)
            add_field(uname_info[uname], get_header_uname_ind('ta_day'), ta_day)
        for uname in independent_unames:
            ta_time, ta_day = -1, nonsense_day
            add_field(uname_info[uname], get_header_uname_ind('ta_time'), ta_time)
            add_field(uname_info[uname], get_header_uname_ind('ta_day'), ta_day)

    [time_things(uname) for uname in uname_info]
    grade_things()
    outlier_dict, hss_headers = load_outliers(year_q)
    if outlier_dict:
      [hss_things(uname) for uname in uname_info]
    advanced_time_things()
    ta_things()


def load_uname_info(sim_dir, year_q):
    addstr = '_uname'
    top_name_f = os.path.join(sim_dir, '%s%s.csv' % (year_q, addstr))
    if not os.path.exists(top_name_f):
        top_sims = load_top_sims(year_q)
        uname_info = dict([(uname, [uname]) for uname in top_sims.keys()])
        return uname_info

    uname_info = {}
    with open(top_name_f, 'r') as f:
        line = f.readline() # headers
        line = f.readline()
        while line:
            fields = (line.strip()).split(',')
            uname = fields[0]
            uname_info[uname] = fields

            line = f.readline()
    return uname_info

def uname_info_to_array(uname_info, field_ys=None):
    unames = sorted(uname_info.keys())
    items = [0]*len(unames)
    field_inds = range(len(uname_info[unames[0]]))
    if field_ys:
        field_inds = map(get_header_uname_ind, field_ys)
    for i, uname in enumerate(unames):
        items[i] = [float(uname_info[uname][j]) for j in field_inds]
        #items[i] = [float(uname_info[uname][get_header_uname_ind(field_y)]) for field_y in field_ys]
    return np.array(items)

def save_uname_info(uname_info, year_q):
    addstr = '_uname'
    with open(os.path.join(sim_dir, '%s%s.csv' % (year_q, addstr)), 'w') as f:
        f.write('%s\n' % ','.join(headers_uname))
        for uname in sorted(uname_info.keys()):
            f.write(','.join(uname_info[uname]))
            f.write('\n')
        print "Wrote", f.name


if __name__ == '__main__':
    for year_q in ['2012_1', '2013_1', '2014_1']:
        uname_info = load_uname_info(sim_dir, year_q)
        preprocess_uname_info(uname_info, year_q)
        save_uname_info(uname_info, year_q)

    for year_q in ['2012_1', '2013_1', '2014_1']:
        uname_info = load_uname_info(sim_dir, year_q)
        remove_ungraded(uname_info, year_q)
        save_uname_info(uname_info, year_q)
