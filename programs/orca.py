import math
import sys
import re

def check_input(args,nodeInfo):

  def error(message):
    print(message)
    sys.exit(1)

  def convert_mem_units(memory, iUnits):
    memConv = {'kb': 1/1024.0, 'mb': 1.0, 'gb': 1024.0, 'kib': 1000*math.pow(1024,-2), 'mib': math.pow(10,6)*math.pow(1024,-2), 'gib': math.pow(10,9)*math.pow(1024,-2)}
    return memory * memConv[iUnits]

  # main
#  if args['parseInput']:
#    inputData = open(args['input'],'r').read()
#    memMatch = re.search(r'memory\s+([+-]?\d*\.?\d+)\s+([KMG]i?B)',inputData,re.IGNORECASE)
#    nodeMemLimit = nodeInfo[args['queue']]['nodeMem'] * 0.95
#    if memMatch:
#      jobMemory = int(memMatch.group(1))
#      jobMemUnit = memMatch.group(2).lower()
#      jobMemory = convert_mem_units(jobMemory, jobMemUnit)
#      if jobMemory > nodeMemLimit:
#        error('Please reduce the memory of your job from '+str(int(jobMemory))+' MB to '+str(int(nodeMemLimit))+' MB or less.')
#    else:
#      print('Memory card not found.  Max memory allowed is '+str(int(nodeMemLimit))+' MB. Default is 256 MB.')
#

def footer(cluster):
    job_id = "JOB_ID"
    workdir = "SGE_O_WORKDIR"
    if cluster == "hopper":
        job_id = "PBS_JOBID"
        workdir = "PBS_O_WORKDIR"

    cmd = """
# delete any temporary files that my be hanging around.
rm -f *.tmp
tar --transform "s,^,Job_Data_${%s}/," -vzcf ${%s}/Job_Data_${%s}.tar.gz *""" % (job_id, workdir, job_id)
    return cmd
