#!/usr/bin/env python

import pylab as pl
import json
import numpy as np

from matplotlib.path import Path
import matplotlib.patches as patches

from matplotlib.patches import RegularPolygon


def plot_perf(to_plot, baseline, label, color, lw=1):
    pl.plot(baseline+to_plot, label=label + " ({:.3f} ms)".format(np.mean(to_plot)), color=color, lw=lw)
    pl.text(len(to_plot), np.mean(baseline+to_plot), "{:.3f}".format(np.mean(to_plot)), color=color, va="center", bbox=dict(facecolor='white'))



def link_subplots( first_axes, base1, out1, second_axes, base2, out2, dint, dout, color, alpha):

    def ax_to_fig(figure, ax, pt):
        return figure.transFigure.inverted().transform( ax.transData.transform( pt ) )

    fig = pl.gcf()
    ax1 = pl.subplot(*first_axes)
    ax2 = pl.subplot(*second_axes)

    zero1, pt1max = ax_to_fig(fig, ax1, (0, np.mean(out1[:10]) ) )
    zero1, pt1min = ax_to_fig(fig, ax1, (0, np.mean(base1[:10]) ) )
    zero2, pt2max = ax_to_fig(fig, ax2, (0, np.mean(out2[:10]) ) )
    zero2, pt2min = ax_to_fig(fig, ax2, (0, np.mean(base2[:10]) ) )

    vertices = [(zero1,pt1max), (zero1 - dout, pt1max),
                (zero1 - dout, pt2min), (zero2, pt2min), (zero2, pt2max), (zero1 - dint, pt2max),
                (zero1 - dint, pt1min), (zero1,pt1min), (zero1,pt1max)]
    codes    =  [Path.MOVETO] + [Path.LINETO]*(len(vertices)-2) + [Path.CLOSEPOLY]
    path = Path(vertices, codes)
    patch = patches.PathPatch(path, facecolor=color, ls="dotted", alpha=alpha, transform=fig.transFigure)

    fig.patches.append(patch)









def plot_performances( perf , outfile="./performances.pdf"):
    """
    """
    if not isinstance(perf, dict):
        with open(perf, "r") as f:
            perf = json.load(f)
    timeline        = np.array(perf['timeline'])*1000.0
    model_update    = np.array(perf["model_update"])*1000.0 
    tasks_update    = np.array(perf["updaters_update"])*1000.0
    compute_output  = np.array(perf["compute_output"])*1000.0
    ctrl_up_tasks   = np.array(perf["controller_update_tasks"])*1000.0
    ctrl_solve      = np.array(perf["controller_solve_problem"])*1000.0
    solver_prepare  = np.array(perf["solver_prepare"])*1000.0
    solver_solve    = np.array(perf["solver_solve"])*1000.0
    
    tot_len = min( len(timeline), len(model_update), len(tasks_update), len(compute_output), len(ctrl_up_tasks), len(ctrl_solve), len(solver_prepare), len(solver_solve)) #because sometimes it saves another value at the end
    timeline        = timeline[:tot_len]
    model_update    = model_update[:tot_len]
    tasks_update    = tasks_update[:tot_len]
    compute_output  = compute_output[:tot_len]
    ctrl_up_tasks   = ctrl_up_tasks[:tot_len]
    ctrl_solve      = ctrl_solve[:tot_len]
    solver_prepare  = solver_prepare[:tot_len]
    solver_solve    = solver_solve[:tot_len]
    
    step_time = []
    for i in range(len(timeline)-1):
        step_time.append(timeline[i+1] - timeline[i])
    step_time = np.array(step_time)

    ##########################
    pl.figure(figsize=(12,12))
    pl.subplot(3,1,1)
    plot_perf(step_time, 0., "step time", "k", 2)
    plot_perf(model_update, 0., "update model", "r")
    plot_perf(tasks_update, model_update, "update updaters", "g")
    plot_perf(compute_output, model_update+tasks_update, "compute output", "b")

    pl.legend(ncol=2, prop={"size":'small'})
    pl.ylim(0, pl.ylim()[1])
    pl.title("orocos loop performances : accumulated times")
    pl.ylabel("time (ms)", labelpad=40)
    
    ##########################
    pl.subplot(3,1,2)
    plot_perf(compute_output, 0., "compute output", "b", 2)
    plot_perf(ctrl_up_tasks, 0., "controller: write tasks matrices", "g")
    plot_perf(ctrl_solve, ctrl_up_tasks, "controller: solve problem", "r")

    pl.legend(ncol=2, prop={"size":'small'})
    pl.ylim(0, pl.ylim()[1])
    pl.title("controller performances : accumulated times")
    pl.ylabel("time (ms)", labelpad=40)

    ##########################
    pl.subplot(3,1,3)
    plot_perf(ctrl_solve, 0., "controller: solve problem", "r", 2)
    plot_perf(solver_prepare, 0., "solver: prepare all matrices", "b")
    plot_perf(solver_solve, solver_prepare, "solver: solve QP", "g")
    
    pl.legend(ncol=2, prop={"size":'small'})
    pl.ylim(0, pl.ylim()[1])
    pl.title("solver performances : accumulated times")
    pl.ylabel("time (ms)", labelpad=40)
    pl.xlabel("step")


    ##########################
    link_subplots( (3,1,1), (model_update+tasks_update), (model_update+tasks_update+compute_output),
                   (3,1,2), [0.], compute_output,
                   .03, .04, "b", 0.3)

    link_subplots( (3,1,2), (ctrl_up_tasks), (ctrl_up_tasks+ctrl_solve),
                   (3,1,3), [0.], ctrl_solve,
                   .05, .06 , "r", 0.3)

    pl.savefig(outfile, bbox_inches='tight' )

    ##########################
    pl.show()


import sys
if __name__ == "__main__":
    if len(sys.argv) == 1:
        to_load = "performances.json"
    else:
        to_load = sys.argv[1]
    plot_performances(to_load)



