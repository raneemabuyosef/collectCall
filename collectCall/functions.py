import re
import islpy as isl
import ctypes

boolCounter = 0
globalTimer = 0
D2G = {}

def updateD2G(tensorName, obj, noIncFlag = False ): ## flag for move
    global globalTimer
    if not(noIncFlag):
        globalTimer += 1
    
    D2G[(globalTimer,tensorName)] = obj

    return globalTimer
def getD2G():
    return D2G

def card(islObj): ##relation card
    output = open("isl_dump.txt",'w')
    output.write(islObj)
    
    output.close()
    
    fun = ctypes.CDLL("./card_map.so")
    fun.main()
    inputfile = open("isl_card.txt",'r')
    card = inputfile.readline()
    inputfile.close()
    card = re.split("{",card)
    card = card[1]
    card = card[card.index("->") +2 :card.index(":")]
    if "^" in card:
        card = card.replace("^","**")
    
    if "floor" in card:
        card =  re.sub(r'floor\((.+)\)', r'\1', card)

    return card.strip()

def card_index(set_,index):
    output = open("isl_index_dump.txt",'w')
    output.write(set_)
    output.close()
    fun = ctypes.CDLL("./card_index.so")
    fun.main.argtypes = [ctypes.c_uint]
    fun.main(index)
    inputfile = open("isl_index_card.txt",'r')
    card = inputfile.readline()
    inputfile.close()
    card = re.split("{",card)
    card = card[1]

    card = card[:card.index(":")]
    if "^" in card:
        card = re.sub(r'\^','**',card)
    if "floor" in card:
        card =  re.sub(r'floor\((.+)\)', r'\1', card)

    return card.strip()

def commsize(islObj): #set card
    output = open("isl_set_dump.txt",'w')
    output.write(islObj)
    output.close()
    fun = ctypes.CDLL("./card_set.so")
    fun.main()

    inputfile = open("isl_set_card.txt",'r')
    card = inputfile.readline()
    inputfile.close()
    card = re.split("{",card)
    card = card[1]

    card = card[:card.index(":")]
    if "^" in card:
        card = card.replace("^","**")
    if "floor" in card:
        card =  re.sub(r'floor\((.+)\)', r'\1', card)

    return card.strip()


def islInit_map(islmap):
    ls = []
    #print(islmap)
    mapRange = islmap.range()
    mapDomain = islmap.domain()
    ls = islInit_set(mapRange) + islInit_set(mapDomain)
    return ls
def islInit_set(islset):
    ls = []
    for i in range(islset.n_dim()):
        ls.append(islset.get_dim_name(isl.dim_type.set,i))
    for i in range(islset.n_param()):
        ls.append(islset.get_dim_name(isl.dim_type.param,i))
    
    return ls

def islConstraints_set(islset):
    setRange = islset.get_basic_sets()
    const = []
    for set_ in setRange:
        for j in set_.get_constraints():
            constraint = str(j).split(":")[1].replace("}","").strip()
            if "floor" in constraint:
                 constraint = floorToMod(constraint)
            if re.search (r'(\d+)([a-zA-Z])', constraint):
                pattern = r'(\b-?\d+)([a-zA-Z])'
                constraint = re.sub(r'(\b-?\d+)([a-zA-Z])', r'\1*\2', constraint)
            if "mod" in constraint:
                constraint = constraint.replace("mod", "%")

            if "=" in constraint and not( ">" in constraint or "<" in constraint):
                constraint = constraint.replace("=","==")
            const.append(constraint)

    return const

def islConstraints(constraint): ## isl constraints 
    return 0
def getSetDims(islset):
    setDims = []
    for i in range(islset.n_dim()):
        setDims.append(islset.get_dim_name(isl.dim_type.set,i))
    return setDims


def islConstraints_map(islmap, param=[]):
    basicMap = islmap.get_basic_maps()
    const = []
    forall = []
    
    if islmap.is_empty(): ## false
        return False
    
    for i in basicMap:
        for j in i.get_constraints():
            constraint = str(j).split(":")[1].replace("}","").strip()
            if "floor" in constraint:
                constraint = floorToMod(constraint)
            if re.search (r'(\d+)([a-zA-Z])', constraint):
                pattern = r'(\b-?\d+)([a-zA-Z])'
                constraint = re.sub(r'(\b-?\d+)([a-zA-Z])', r'\1*\2', constraint)

            if "=" in constraint and not( ">" in constraint or "<" in constraint):
                constraint = constraint.replace("=","==")
                forall.append(constraint) ## for all values where grid == tensor partiton  
            const.append(constraint)
        range_ = i.range()
        setRange = range_.get_basic_sets()
        for set_ in setRange:
            for j in set_.get_constraints():
                constraint = str(j).split(":")[1].replace("}","").strip()
                if "floor" in constraint:
                     constraint = floorToMod(constraint)
                if re.search (r'(\d+)([a-zA-Z])', constraint):
                    pattern = r'(\b-?\d+)([a-zA-Z])'
                    constraint = re.sub(r'(\b-?\d+)([a-zA-Z])', r'\1*\2', constraint)
                if "mod" in constraint:
                    constraint = constraint.replace("mod", "%")

                if "=" in constraint and not( ">" in constraint or "<" in constraint):
                    constraint = constraint.replace("=","==")
                if not constraint in const:
                    const.append(constraint)
    const += forallConstraint(forall, const,param)
    return const
def forallConstraint(forall, const, param=[]):
    constraints = []
    global boolCounter
    for i in forall:
        i0 = ''
        i1 = ''
        ls = []

        if "+" in i:
            tmp = i.strip()

            match = re.search(r'\((.*?)\)', tmp)
            if match:
                tmp = match.group(1).strip()


            tmp = tmp.split("+")
            if '-' in tmp[0]:
                i0 = tmp[0].split("-")[1].strip()
            else:
                i0 = tmp[0].strip()

            i1 = tmp[1].split("==")[0].strip()

        if i0.isdigit() or i1.isdigit() or i0 == '' or i1 == '':
            continue
        
        for i in const:
            isparam = re.findall(r'[a-zA-Z]',i)
            if i0 in i or i1 in i:
                ls.append(i)
            elif len(isparam) == 1 and isparam[0] in list(param.keys()) and not isparam in ls:
                ls.append(i)
        constraints.append(f"Implies(b_{boolCounter}, And({','.join(ls)}))")
        constraints.append(f"ForAll([{i0},{i1}], b_{boolCounter})")
        boolCounter += 1
    return constraints

def commEquality(islComm1, islComm2, comm1):#, comm2): ## comm1 and 2 are grid obj
    constraints = []
    islComm1_bset = islComm1.get_basic_sets()
    islComm2_bset = islComm2.get_basic_sets()
    global boolCounter

    for i in range(comm1.gridSize()):
        tmp = []
        comm1name = islComm1.get_dim_name(isl.dim_type.set, i)
        comm2name = islComm2.get_dim_name(isl.dim_type.set , i)
        ## comm1
        for bset in islComm1_bset:
            for constraint in bset.get_constraints():
                if constraint.involves_dims(isl.dim_type.set, i , 1): ## dim = i
                    constraint = str(constraint).split(":")[1].replace("}","").strip()
                    if "floor" in constraint:
                         constraint = floorToMod(constraint)
                    if re.search (r'(\d+)([a-zA-Z])', constraint):
                        pattern = r'(\b-?\d+)([a-zA-Z])'
                        constraint = re.sub(r'(\b-?\d+)([a-zA-Z])', r'\1*\2', constraint)
                    if "mod" in constraint:
                        constraint = constraint.replace("mod", "%")

                    if "=" in constraint and not( ">" in constraint or "<" in constraint):
                        constraint = constraint.replace("=","==")
                    tmp.append(constraint)
        ## comm2
        for bset in islComm2_bset:
            for constraint in bset.get_constraints():
                if constraint.involves_dims(isl.dim_type.set, i , 1): ## dim = i
#                    tmp.append(str(constraint).split(":")[1].replace("}",""))
                    constraint = str(constraint).split(":")[1].replace("}","").strip()
                    if "floor" in constraint:
                         constraint = floorToMod(constraint)
                    if re.search (r'(\d+)([a-zA-Z])', constraint):
                        pattern = r'(\b-?\d+)([a-zA-Z])'
                        constraint = re.sub(r'(\b-?\d+)([a-zA-Z])', r'\1*\2', constraint)
                    if "mod" in constraint:
                        constraint = constraint.replace("mod", "%")

                    if "=" in constraint and not( ">" in constraint or "<" in constraint):
                        constraint = constraint.replace("=","==")
                    tmp.append(constraint)


        constraints.append(f"Implies(b_{boolCounter}, And({','.join(tmp)}, {comm1name} == {comm2name} ))")
        constraints.append(f"ForAll([{comm1name},{comm2name}], b_{boolCounter})")
        boolCounter += 1

    return constraints



def floorToMod(constraint):
    parts = constraint.split("+",1)[1].split("/")
    lhs = parts[0]
    rhs = parts[1].replace(")","").replace("(","")
    lhs = lhs.split("floor(")
    return lhs[1] +  " % " +rhs
def getBoolCounter():
    return boolCounter


def useBoolCounter():
    global boolCounter
    b = boolCounter
    boolCounter += 1
    return b
