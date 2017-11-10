from outliers_util import *

def plot_outlier_lines(x, interp_y, interp_whisk, axs):
    co = ['r', 'g', 'b']
    field_ys = interp_y.keys()
    for i, field_y in enumerate(field_ys):
        y_95 = interp_y[field_y]
        y_uw = interp_whisk[field_y]
        if field_y == 'token':
            ind = 1
        else:
            ind = 0

        axs[ind].plot(x, y_95, c=co[i], alpha=0.3, label="%s_95" % field_y)
        axs[ind].plot(x, y_uw, c=co[i], alpha=0.6, label="%s_uw" % field_y)

from matplotlib.patches import Ellipse
def draw_ellipse(coords_ell, ax, slope=0):
    x1, x2, y1, y2 = coords_ell
    w, h = x2-x1, y2-y1
    x_c, y_c = (x1+x2)/2, (y1+y2)/2
    #if slope == 0: slope = h/w
    # angle = get_angle(slope)
    # print "slope", slope, "angle", angle, "radians", np.arctan(slope)
    ell = Ellipse((x_c, y_c), w, h,
                  fc='none', lw=1,ec='k',alpha=0.6)#, angle=angle)
    ax.add_artist(ell)
    ax.plot([x1,x2],[y1+h/2,y1+h/2], alpha=0.6, lw=1, c='k')
    ax.plot([x1+w/2,x1+w/2],[y1, y2], alpha=0.6, lw=1, c='k')
    
from matplotlib.patches import Rectangle
def draw_rectangle(coords_ell, ax):
    x1, x2, y1, y2 = coords_ell
    w, h = x2-x1, y2-y1
    rect = Rectangle((x1, y1), w, h,
                  fc='none', lw=1,ec='k',alpha=0.6)
    ax.add_artist(rect)

def draw_thresh(coords_abs, ax):
    x_thresh, y_thresh = coords_abs
    y_lim = ax.get_ylim()
    x_lim = ax.get_xlim()
    ax.plot(x_lim, [y_thresh]*2, '--', lw=1, c='k', alpha=0.6)
    ax.plot([x_thresh]*2, y_lim, '--', lw=1, c='k', alpha=0.6)

def graph_max_outliers_ell(x, y, ax, coords_ell):
    out_ell, in_ell = get_ellipse_outliers(x, y, coords_ell)

    alpha_out = 0.5
    c_in, alpha_in = 'g', 0.3
    ax.scatter(x[out_ell], y[out_ell], c='r', alpha=alpha_out, label='ellipse')
    ax.scatter(x[in_ell], y[in_ell], c=c_in, alpha=alpha_in)

    # guiding lines
    draw_ellipse(coords_ell, ax)
    draw_rectangle(coords_ell, ax)

def graph_max_outliers_abs(x, y, ax, coords_abs):
    out_abs, in_abs = get_abs_outliers(x, y, coords_abs)
    alpha_out = 0.5
    c_in, alpha_in = 'g', 0.3
    ax.scatter(x[out_abs], y[out_abs], c='b', alpha=alpha_out, label='abs')
    ax.scatter(x[in_abs], y[in_abs], c=c_in, alpha=alpha_in)
    
    # guiding lines
    draw_thresh(coords_abs, ax)

def graph_max(x, y, ax):
    c_in, alpha_in = 'g', 0.3
    ax.scatter(x, y, c=c_in, alpha=alpha_in)
