import math
import sys
import re

def check_input(args,nodeInfo):

  def error(message):
    print(message)
    sys.exit(1)

  def convert_mem_units(memory, iUnits):
    memConv = {'': math.pow(10,-6), 'k': math.pow(10,-3), 'm': 1.0}
    return memory * memConv[iUnits]

  # main
  if args['parseInput']:
    inputData = open(args['input'],'r').read()
    memMatch = re.search(r'memory,(\d+)(?:[,]*)([a-zA-Z]*)',inputData,re.IGNORECASE)
    nodeMemLimit = nodeInfo[args['queue']]['nodeMem'] * 131072 * math.pow(10,-6) * 0.95 / args['nslots']
    if memMatch:
      jobMemory = int(memMatch.group(1))
      jobMemUnit = memMatch.group(2).lower()
      jobMemory = convert_mem_units(jobMemory, jobMemUnit)
      if jobMemory > nodeMemLimit:
        error('Please reduce the memory of your job from '+str(int(jobMemory))+' m to '+str(int(nodeMemLimit))+' m or less for '+str(args['nslots'])+' processors')
    else:
      print('Memory card not found.  Max memory allowed is '+str(int(nodeMemLimit))+' m. Default is 8 m.')

