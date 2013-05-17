#!/usr/bin/env python

import fnmatch
import argparse
import os
import sys
from subprocess import call
from mako.template import Template
from programs import cfour,molpro,psi4,qchem,nwchem
import yaml
import socket

sjob_path = os.path.dirname(os.path.abspath(__file__))
hostname = socket.gethostname()
cluster_name = "vortex"
if hostname == "vortex":
    cluster_name = "vortex"
elif "hopper" in hostname:
    cluster_name = "hopper"

def dummy_check_input(args, nodeInfo):
    pass

def dummy_footer():
    return ""

checks = {
           'cfour':  { 'check_input': cfour.check_input, 'footer': cfour.footer },
           'cfour/1.0/parallel':  { 'check_input': cfour.check_input, 'footer': cfour.footer },
           'cfour/1.0/serial':  { 'check_input': cfour.check_input, 'footer': cfour.footer },
           'scfour': { 'check_input': cfour.check_input, 'footer': cfour.footer },
           'molpro': { 'check_input': molpro.check_input, 'footer': dummy_footer },
           'nwchem': { 'check_input': nwchem.check_input, 'footer': dummy_footer },
           'qchem':  { 'check_input': qchem.check_input, 'footer': dummy_footer },
           'psi':    { 'check_input': psi4.check_input, 'footer': dummy_footer } }

curdir = os.getcwd().split('/')[-1]
scriptname = '%s.csh' % curdir
commandline = ' '.join(sys.argv)

nodeInfo = yaml.load(open(sjob_path + '/programs/info.yaml','r'))
queue_choices = nodeInfo[cluster_name].keys()

template_path = sjob_path + '/template/' + cluster_name + '/'
programs = []
for root, dirnames, filenames in os.walk(template_path):
  for filename in fnmatch.filter(filenames, '*.tmpl'):
      programs.append(os.path.join(root, filename))

program_choices = [elem[len(template_path):-5] for elem in programs]
program_choices.remove('header')

parser = argparse.ArgumentParser(description='Submit jobs to the queue.')
parser.add_argument('-d', '--debug', action='store_true',  help='Just create the script. Do not submit.')
parser.add_argument('-i', '--input', help='Set the name of the input file. (Default: input.dat)')
parser.add_argument('-N', '--name', help='Set name of the job. (default: %s)' % curdir, default=curdir)
parser.add_argument('-n', '--nslots', help='Set the number of processors to use.', type=int, default=0)
parser.add_argument('-o', '--output', help='Set the name of the output file. (Default: output.dat)', default='output.dat')
parser.add_argument('-p', '--program', choices=program_choices, required=True, help='Program to use.')
parser.add_argument('-q', '--queue', choices=queue_choices, required=True, help='Queue to submit to.')
parser.add_argument('--no-parse', action='store_false', dest='parseInput', default=True, help='Parse input file to detect common errors [default: parse]')

# global argument checks
args = vars(parser.parse_args())
if args['nslots'] % 2 != 0 and args['nslots'] != 1:
    parser.error("NSLOTS must be even or 1.")
if args['nslots'] == 0:
    args['nslots'] = nodeInfo[cluster_name][args['queue']]['numProc']
    if 'cfour' in args['program']:
        args['nslots'] = int(args['nslots']) / 2

# Check for cfour program and input file
if args['input'] == None:
    if 'cfour' in args['program']:
        args['input'] = 'ZMAT'
    else:
        args['input'] = 'input.dat'

# Input Check
checks[args['program']]['check_input'](args, nodeInfo[cluster_name])

# Load Mako template file
header_template = Template(filename=template_path+'header.tmpl')

script = None
try:
    script = open(scriptname, 'w')
    script.write(header_template.render(queue=args['queue'], name=args['name'], cmdline=commandline))
except IOError as e:
    print "Unable to create your script file."
    sys.exit(1)

# Load in program specific file
program = None
try:
    program = Template(filename=(template_path+'%s.tmpl') % args['program'])
except IOError as e:
    print "Unable to open the program template file for the requested program."
    sys.exit(1)

script.write(program.render(nslots=args['nslots'], input=args['input'], output=args['output']))

script.write(checks[args['program']]['footer']())

# make sure there are blank lines at the end
script.write("\n\n")

script.close()

# Ensure /tmp and /tmp1 have the proper permissions
if args['debug'] == False:
    call(['qsub', scriptname])

