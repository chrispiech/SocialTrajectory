import os
import numpy as np
from scipy.stats import wilcoxon
from preprocess_per_user import *

sim_dir = os.path.join(os.getcwd(), 'top_sim')

def get_new_online(outlier_dict, year_q):
    unames = sorted(outlier_dict.keys())
    onlines = get_current_online(unames, outlier_dict)
    print year_q, onlines
    edge_dict = get_edges(outlier_dict, year_q)
    update_outlier_others(outlier_dict, edge_dict)

    new_onlines = []
    count_online = 0
    for i, uname in enumerate(unames):
        print i, uname
        if is_online(uname, set(), onlines, edge_dict):
            print "\t", uname, "online"
            count_online += 1
            if uname not in onlines:
                new_onlines.append(uname)
    print "total online", count_online, "/", len(unames)
    return new_onlines

def is_online(uname, seen_set, onlines, edge_dict):
    if uname in onlines: return True
    if uname not in edge_dict: return False
    other = edge_dict[uname]
    print "\t", uname, "->", other
    if other in seen_set: return False
    seen_set.add(uname)
    return is_online(other, seen_set, onlines, edge_dict)

def get_current_online(unames, online_dict):
    hss_all_onlines = [outlier_dict[uname][get_header_outlier_ind('hss_online')] \
            for uname in unames]
    onlines = [uname for (uname, is_online) in zip(unames, hss_all_onlines) if int(is_online)]
    print "\toriginally %d online" % len(onlines)
    return onlines

def get_edges(online_dict, year_q):
    max_field = 'hss_pother'
    top_sims = load_top_sims(year_q)
    edge_dict = {}
    for uname in online_dict:
        other_uname = get_max_other(top_sims[uname],
                online_dict[uname][get_header_outlier_ind(max_field)],
                max_field)
        edge_dict[uname] = other_uname
    return edge_dict

def get_max_other(sims_uname, max_pother, hss_field):
    top_sim_field = hss_field.split('_')[-1] # hss_pother -> pother
    field_ind = get_header_ind(top_sim_field)
    all_pothers = np.array([float(sim[field_ind]) for sim in sims_uname])
    all_others = [sim[get_header_ind('other')] for sim in sims_uname]
    argmax_ind = np.argmax(all_pothers)
    return all_others[argmax_ind]

def get_header_outlier_ind(field):
    # headers_hss defined in preprocess
    return get_generic_ind(headers_hss, field)

def update_outlier_onlines(outlier_dict, new_onlines):
    for uname in new_onlines:
        add_field(outlier_dict[uname], get_header_outlier_ind('hss_online'), 1)

def update_outlier_others(outlier_dict, edge_dict):
    for uname in outlier_dict:
        add_field(outlier_dict[uname], get_header_outlier_ind('other'), edge_dict[uname])

if __name__ == "__main__":
    for year_q in ['2012_1', '2013_1', '2014_1']:
        outlier_dict, _ = load_outliers(year_q)
        new_onlines = get_new_online(outlier_dict, year_q)
        update_outlier_onlines(outlier_dict,  new_onlines)
        print "new onlines from first pass", new_onlines

        save_outliers(year_q, outlier_dict, add_uname=False)
