#!/opt/python/2.7.3/bin/python
#!/global/project/projectdirs/ccqc/python/hopper/gcc/bin/python

import fnmatch
import argparse
import os
import sys
from subprocess import call
from mako.template import Template
from programs import cfour,molpro,psi4,qchem,nwchem,orca
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

def dummy_footer(cluster):
    return ""

checks = {
           'cfour':  { 'check_input': cfour.check_input,  'footer': cfour.footer },
           'scfour': { 'check_input': cfour.check_input,  'footer': cfour.footer },
           'molpro': { 'check_input': molpro.check_input, 'footer': dummy_footer },
           'nwchem': { 'check_input': nwchem.check_input, 'footer': dummy_footer },
           'qchem':  { 'check_input': qchem.check_input,  'footer': dummy_footer },
           'orca' :  { 'check_input': orca.check_input,   'footer': dummy_footer },
           'psi':    { 'check_input': psi4.check_input,   'footer': dummy_footer } }

curdir = os.getcwd().split('/')[-1]
scriptname = '%s.csh' % curdir
commandline = ' '.join(sys.argv)

nodeInfo = yaml.load(open(sjob_path + '/programs/info.yaml','r'))
queue_choices = nodeInfo[cluster_name]['queues'].keys()

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
parser.add_argument('-o', '--output', help='Set the name of the output file. (Default: output.dat)', default='output.dat')
parser.add_argument('-p', '--program', choices=program_choices, required=True, help='Program to use.')
parser.add_argument('-q', '--queue', choices=queue_choices, required=True, help='Queue to submit to.')
parser.add_argument('-n', '--nslot', help='Set the number of processors to use per node.', type=int, default=0)
parser.add_argument('--no-parse', action='store_false', dest='parseInput', default=True, help='Parse input file to detect common errors [default: parse]')

if cluster_name == "hopper":
  parser.add_argument('-A', '--account', help='Account to charge for time')
  parser.add_argument('-w', '--walltime', required=nodeInfo[cluster_name]['timelimit'], default='00:30:00', help="Maximum wallclock time for your job.")
  parser.add_argument('-c', '--nnode', help='Set the number of nodes to use.', type=int, default=1)

# global argument checks
args = vars(parser.parse_args())
if args['nslot'] % 2 != 0 and args['nslot'] != 1:
    parser.error("nslot must be even or 1.")
if args['nslot'] == 0:
    args['nslot'] = nodeInfo[cluster_name]['queues'][args['queue']]['numProc']
    if 'cfour' in args['program']:
        args['nslot'] = int(args['nslot']) / 2

# Check for cfour program and input file
if args['input'] == None:
    if 'cfour' in args['program']:
        args['input'] = 'ZMAT'
    else:
        args['input'] = 'input.dat'

# Input Check
base_program_name = args['program'].split('/')[0]
checks[base_program_name]['check_input'](args, nodeInfo[cluster_name]['queues'])

# Load Mako template file
header_template = Template(filename=template_path+'header.tmpl')

extrapbscommands = ""
if cluster_name == "hopper" and args['account']:
    extrapbscommands = "#PBS -A %s" % (args['account'])

script = None
if not args.has_key('nnode'):
    args['nnode'] = 1
if not args.has_key('walltime'):
    args['walltime'] = ""

try:
    script = open(scriptname, 'w')
    script.write(header_template.render(queue=args['queue'],
					name=args['name'],
					nslot=args['nslot'],
					nnode=args['nnode'],
					mppwidth=args['nslot'] * args['nnode'],
					walltime=args['walltime'],
                                        extrapbs=extrapbscommands,
					cmdline=commandline))
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

script.write(program.render(nslot=args['nslot'],
			    name=args['name'],
                            input=args['input'],
                            output=args['output'],
                            ncorepernode=nodeInfo[cluster_name]['queues'][args['queue']]['numProc'],
			    nmpipersocket=args['nslot']/4,
			    mppwidth=args['nslot'] * args['nnode'],
                            walltime=args['walltime']))

script.write(checks[base_program_name]['footer'](cluster_name))

# make sure there are blank lines at the end
script.write("\n\n")

script.close()

# Ensure /tmp and /tmp1 have the proper permissions
if args['debug'] == False:
    call(['qsub', scriptname])

