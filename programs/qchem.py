import math
import sys
import re

def check_input(args,nodeInfo):

  def error(message):
    print(message)
    sys.exit(1)

  # main
  if args['parseInput']:
    inputData = open(args['input'],'r').read()
    memMatch = re.search(r'\s*mem\_total\s*(\d+)',inputData,re.IGNORECASE)
    nodeMemLimit = nodeInfo[args['queue']]['nodeMem'] * 0.95 / args['nslot']
    if memMatch:
      jobMemory = int(memMatch.group(1))
      if jobMemory > nodeMemLimit:
        error('Please reduce the memory of your job from '+str(int(jobMemory))+' MB to '+str(int(nodeMemLimit))+' MB or less for '+str(args['nslot'])+' processors')
    else:
      print('Memory card not found.  Max memory allowed is '+str(int(nodeMemLimit))+' MB. Default is 2000 MB.')

