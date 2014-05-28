from __future__ import division
from fabric.api import local, lcd
from fabric import state

state.output['status'] = False


def dependency_graph():
    local('sfood -i -q --ignore=`pwd`/iris/services iris | grep -v /tests/ | grep -v /utils | grep -v exceptions.py | sfood-graph -p | dot -Tpdf -o deps.pdf')


def docs(clean=False):
    with lcd('docs'):
        if clean:
            local('make clean')
        local('make html')


def coverage():
    local('coverage run --timid --source=iris -m py.test iris')
    local('coverage html')
    #local('open .coverage-report/index.html')


def flakes():
    import subprocess, yaml
    popen = subprocess.Popen(['cloc', 'iris', '--yaml', '--quiet'], stdout=subprocess.PIPE)
    lines = int(yaml.load(popen.stdout)['Python']['code'])
    flakes = int(subprocess.check_output('flake8 iris | wc -l', shell=True))
    print '%s flakes, %s lines, %.5f flakes per kLOC, one flake every %.1f lines'  % (flakes, lines, 1000 * flakes / lines, lines / flakes)


def fixme():
    local(r"egrep -rn '#\s*(FIXME|TODO|XXX)\b' iris")

