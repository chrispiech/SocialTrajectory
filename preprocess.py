import os
import sys
import numpy as np
import pandas as pd
from scipy.signal import medfilt
from scipy.optimize import curve_fit

SIM_DIR = os.path.join(os.getcwd(), 'top_sim_new_new')
headers = ['uname', 'other', 'token', 'pself', 
        'pother', 'step', 'time',
        'hash', 'fname', 'fpath',
        'type_other', 'fpath_other', 'report',
        'norm_step', 'time_round',
        'scale_time', 'work_time']
largest_factor = 1500
def get_header_ind(field):
    return headers.index(field)

def load_top_sims(year_q, sim_dir=None):
    if sim_dir is None:
      sim_dir = SIM_DIR
    top_sims = {}
    with open(os.path.join(sim_dir, '%s.csv' % year_q), 'r') as f:
        line = f.readline() # headers
        line = f.readline()
        while line:
            fields = (line.strip()).split(',')
            uname = fields[0]
            if uname not in top_sims:
                top_sims[uname] = []
            top_sims[uname].append(fields)

            line = f.readline()
        print "loaded top sims from", f.name
    return top_sims

headers_hss = ['uname', 'hss_num', 'hss_frac', 'hss_time', 'hss_token', 'hss_pother', 'hss_online', 'other']
def save_outliers(year_q, outlier_dict, add_uname=True, sim_dir=None):
    if sim_dir is None:
      sim_dir = SIM_DIR
    unames = sorted(outlier_dict.keys())
    with open(os.path.join(sim_dir, '%s_outliers.csv') % year_q, 'w') as f:
        f.write('%s\n' % ','.join(headers_hss))
        if add_uname:
            f.write('\n'.join(['%s,%s' % (uname,
                            ','.join(map(str,outlier_dict[uname]))) for uname in unames]))
        else:
            f.write('\n'.join([','.join(map(str,outlier_dict[uname])) \
                    for uname in unames]))
        print "Wrote outliers to", f.name

def load_outliers(year_q, sim_dir=None):
    if sim_dir is None:
      sim_dir = SIM_DIR
    outlier_dict = {}
    outlier_fpath = os.path.join(sim_dir, '%s_outliers.csv') % year_q
    if not os.path.exists(outlier_fpath):
      return None, None
    with open(outlier_fpath, 'r') as f:
        line = f.readline() # headers
        headers = (line.strip()).split(',')

        line = f.readline()
        while line:
            fields = (line.strip()).split(',')
            uname = fields[0]
            outlier_dict[uname] = fields

            line = f.readline()
    return outlier_dict, headers

def load_95(sim_dir=None):
    if sim_dir is None:
      sim_dir = SIM_DIR
    with open(os.path.join(sim_dir, 'moss_ps_po.csv'), 'r') as f:
        line = f.readline() # headers
        lines = f.readlines()
        inds, pself, tokens = zip(*[line.strip().split(',') for line in lines])
        pself = map(float, pself)
        tokens = map(float, tokens)
    return pself, tokens
        

def preprocess_top_sims(top_sims):
    print "Factor for norming steps", largest_factor
    def norm_step(uname):
        sims_uname = top_sims[uname]
        len_sims = float(len(sims_uname))
        step_ind = get_header_ind('step')
        norm_step_ind = get_header_ind('norm_step')
        for sim in sims_uname:
            val = max(int((int(sim[step_ind]) + 1)/len_sims * largest_factor), 1)
            if len(sim) <= norm_step_ind:
                sim.append(str(val))
            else:
                sim[norm_step_ind] = str(val)

    def round_time(uname):
        half_hour = 1800
        sims_uname = top_sims[uname]
        time_ind = get_header_ind('time')
        round_ind = get_header_ind('time_round')
        for sim in sims_uname:
            val = int(int(sim[time_ind])/half_hour * half_hour)
            if len(sim) <= round_ind:
                sim.append(str(val))
            else:
                sim[round_ind] = str(val)

    def med_filt(uname, field):
        field_ind = get_header_ind(field)
        vals = [float(sim[field_ind]) for sim in top_sims[uname]]
        meds = medfilt(vals, kernel_size=3) # 3 is default
        for i in range(len(vals)):
            top_sims[uname][i][field_ind] = meds[i]
    # [med_filt(uname, 'pself') for uname in top_sims]
    # [med_filt(uname, 'pother') for uname in top_sims]
    # [med_filt(uname, 'token') for uname in top_sims]

    # scales everyone to same time
    def scaled_time():
        time_ind = get_header_ind('time')
        min_time = min([min([float(sim[time_ind]) for sim in top_sims[uname]]) \
                for uname in top_sims])
        for uname in top_sims:
            sims_uname = top_sims[uname]
            scale_ind = get_header_ind('scale_time')
            for sim in sims_uname:
                val = str(float(sim[time_ind]) - min_time)
                if len(sim) <= scale_ind:
                    sim.append(val)
                else:
                    sim[scale_ind] = val

    # only looks at work time
    def work_time(uname):
        time_ind = get_header_ind('time')
        work_ind = get_header_ind('work_time')
        sims_uname = top_sims[uname]
        min_time = min([float(sim[time_ind]) for sim in sims_uname])
        for sim in sims_uname:
            val = str(float(sim[time_ind]) - min_time)
            if len(sim) <= work_ind:
                sim.append(val)
            else:
                sim[work_ind] = val

    # scaled_time()
    # [work_time(uname) for uname in top_sims]
    [norm_step(uname) for uname in top_sims]
    return norm_step, round_time, med_filt

def save_top_sims(top_sims, year_q, addstr='', sim_dir=None):
    if sim_dir is None:
      sim_dir = SIM_DIR
    with open(os.path.join(sim_dir, '%s%s.csv' % (year_q, addstr)), 'w') as f:
        f.write('%s\n' % ','.join(headers))
        for uname in sorted(top_sims.keys()):
            f.write('\n'.join([','.join(line) for line in top_sims[uname]]))
            f.write('\n')
        print "Wrote", f.name

if __name__ == '__main__':
    for year_q in ['2012_1', '2013_1', '2014_1']:
        top_sims = load_top_sims(year_q)
        preprocess_top_sims(top_sims)
        subset = {}
        unames = top_sims.keys()
        #np.random.shuffle(unames)
        uname_set = unames
        # uname_set = unames[:10]
        # uname_set = ['2012010160', '2012010132', '2012010103', '2012010028', '2012010414', '2012010221', '2012010329', '2012010018', '2012010376', '2012010369']
        #uname_set = ['2012010414']
        print "unames", uname_set, len(uname_set)
        for uname in uname_set:
            subset[uname] = top_sims[uname]
            
        # for field_y in ['pother', 'pself', 'token']:
        #     plot_subset(subset, year_q, 'norm_step', field_y)
        #     plot_box_whisker(top_sims, 'norm_step', field_y, year_q)
        save_top_sims(top_sims, year_q)
        #break
