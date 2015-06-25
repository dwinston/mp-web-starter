"""Tasks views.

This module is divorced from much code necessary for it to work. The
module is intended as a sketch to give a "feel" for a couple of Django
views that work in concert with urls and templates to fetch materials
data from a mongodb database (via a pymatgen-db QueryEngine).
"""
__copyright__ = "Materials Project, 2015"

# System imports
import logging
import re
# Django imports
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound, Http404
# MP imports
from pymatgen.core.structure import Composition, Structure
from utils import connector
from django.template import RequestContext, loader
from utils.decorators import rest_API
from pymatgen.io.cifio import CifWriter

# Logging

logger = logging.getLogger('mg.' + __name__)

@login_required
@connector.mdb
def tasks(request, task_id, mdb=None):
    logger.debug("tasks_view.begin id={}".format(task_id))
    try:
        material = mdb.mat_qe.query(properties=["task_ids", "blessed_tasks"],
                                    criteria={'task_id': task_id})[0]
        task_ids = material['task_ids']
        blessed_tasks = material.get('blessed_tasks', {})
        tasks, ids = [], []
        logger.debug("tasks_view.taskids num={}".format(len(task_ids)))
        for task_type, tid in blessed_tasks.iteritems():
            t = {"task_type": task_type, "task_id": tid, "blessed": True}
            tasks.append(t)
        others = mdb.tasks_qe.query(
                  properties=["task_id", "task_type"],
                  criteria={"task_id": {"$in": task_ids}})

        # Add tasks if not already added as 'blessed'
        ids = {t['task_id'] for t in tasks}
        for t in others:
            if t['task_id'] not in ids:
                tasks.append(t)

        ids = " ".join(ids)
    except IndexError: # No `material`. Just a lone task.
        try:
            task = mdb.tasks_qe.query(properties=["task_id", "task_type"],
                                      criteria={"task_id": task_id})[0]
            tasks, ids = [task], task_id
        except IndexError:
            raise Http404

    t = loader.get_template('tasks/templates/task.html')
    c = RequestContext(request, {'tasks': tasks, 'ids': ids})
    logger.debug("tasks_view.end id={}".format(task_id))
    return HttpResponse(t.render(c))


def _clean_formula(formula):
    formula = Composition(formula).reduced_formula
    return re.sub(r'(\d+)', r'<sub>\1</sub>', formula)

@rest_API(supported_methods=["GET"])
@connector.mdb
def task_details(request, task_id, mdb=None):
    task = mdb.tasks_qe.query(criteria={'task_id': task_id})[0]
    if "analysis" in task and "decomposes_to" in task["analysis"]:
        decomposes_to = []
        if task['is_compatible']:
            for d in task['analysis']['decomposes_to']:
                if d['task_id'] < 0:
                    decomposes_to.append(_clean_formula(d['formula']))
                elif d['task_id'] == task_id:
                    decomposes_to.append('Stable')
                else:
                    decomposes_to.append('<a href="/tasks/%s">%s</a>' % (
                        d['task_id'],
                        _clean_formula(d['formula'])))
        task['analysis']['decomposes_to'] = " + ".join(decomposes_to)
    else:
        task['analysis']['decomposes_to'] = 'Stable'
    for key in ['relax1', 'relax2']:
        try:
            for subkey in task['run_stats'][key].keys():
                cleankey = re.sub("\s+\(.*\)", "", subkey)
                cleankey = re.sub("\s+", "_", cleankey)
                task['run_stats'][key][cleankey] = task['run_stats'][key][subkey]
        except: pass
    init_d = task['input']['crystal']
    init_s = Structure.from_dict(init_d)
    init_cif = str(CifWriter(init_s))
    task['cif_initial'] = init_cif
    return task

@connector.mdb
def download_kpts(request, task_id, mdb=None):
    from pymatgen.io.vaspio import Kpoints
    task = tuple(mdb.tasks_qe.query(properties=["calculations"],
                          criteria={'task_id': task_id}))[0]
    kp = Kpoints.from_dict(task["calculations"][0]["input"]["kpoints"])
    response = HttpResponse(kp, mimetype='text/plain')
    if (request.GET.get('download', 'false') == 'true'):
        response['Content-Disposition'] = 'attachment; filename=%s_kpoints.txt' % task_id
    return response
