import islpy as isl
import re
def getSet(dimension,name,paramMap, partList = []):
    constraints = []
    sets = []
    params = []
    k = 0
    for i in range(len(dimension)):
        sets.append(name+"_"+str(i))
        if not dimension[i].isdigit() and  dimension[i] in paramMap:
            constraints.append(f'0 <= {name}_{i} < {dimension[i]}')
            if not dimension[i] in params:
                tmp = paramMap.get(dimension[i]).getConstraint()
                params += tmp[1]
                constraints += tmp[0]

        elif dimension[i].isdigit():
            constraints.append(f'0 <= {name}_{i} < {dimension[i]}')
        elif partList:  ##PARTITION
            params.append(dimension[i])
            constraints.append(f'0 <= {name}_{i} < {dimension[i]}')
            constraints.append(f"0 <= {dimension[i]} < {partList[k]}")
            if not partList[k] in params:
#                params.append(partList[k])
                tmp = paramMap.get(partList[k]).getConstraint()
                params += tmp[1]
                constraints += tmp[0]
#                constraints += paramMap.get(partList[k]).constraint

            k += 0 

        """
        elif not dimension[i] in paramMap: # i,j,*,.
            constraints.append(f'0 <= {name}_{i} < {parent[i]}')
            if not parent[i]  in params:
                params.append(parent[i])
                constraints += paramMap.get(dimension[i]).constraint

        """
    params = list(set(params))
#    print("["+", ".join(params) + "] -> { ["+ ",".join(sets) + "] : " + " and ".join(constraints) + "}")

    if params:
        return isl.Set("["+", ".join(params) + "] -> { ["+ ",".join(sets) + "] : " + " and ".join(constraints) + "}")
    return isl.Set(" { ["+ ",".join(sets) + "] : " + " and ".join(constraints) + "}")

def ifSet(cond, obj , dims):
    islset = obj.getISL()
    ref = obj.ref
    for d in range(len(dims)):
        if not dims[d].isdigit() and dims[d] in cond: ## not dims[d].isdigit()  added because digits are being replaced in some cases?
            islname = islset.get_dim_name(isl.dim_type.set, d)
            tmp = cond.replace(dims[d], islname)
            islset = islset.to_str().split(":")
            islset = isl.Set(f"{islset[0]} : {tmp} and {islset[1]} ")

            refname = ref.get_dim_name(isl.dim_type.set, d)
            tmp = cond.replace(dims[d], refname)
            ref = ref.to_str().split(":")
            ref = isl.Set(f"{ref[0]} : {tmp} and {ref[1]} ")


    return islset , ref
            

def loopSet(loopset,loopVar, obj, dims):
    islset = obj.getISL()
    ref = obj.ref

    islmap = isl.Map.from_domain_and_range(loopset, islset)
    refmap = isl.Map.from_domain_and_range(loopset, ref)

    '''
    tmp = tmp.insert_dims(isl.dim_type.param,0, 1)
    tmp = tmp.set_dim_name(isl.dim_type.param,0, f"I{loopVar}")
    space = tmp.get_space()
    constraint = isl.Constraint.alloc_equality(space)
    constraint = constraint.set_coefficient_val(isl.dim_type.param, 0, 1)
    constraint = constraint.set_coefficient_val(isl.dim_type.set, 0 , -1)
    constraint = constraint.set_constant_val(0)
    tmp = tmp.add_constraint(constraint)
    '''

    islset = obj.getISL()
    ref = obj.ref
    for d in range(len(dims)):
        if loopVar == dims[d]:
            space = islmap.get_space()
            constraint = isl.Constraint.alloc_equality(space)
            constraint = constraint.set_coefficient_val(isl.dim_type.in_, 0, 1)
            constraint = constraint.set_coefficient_val(isl.dim_type.set, d , -1)
            constraint = constraint.set_constant_val(0)
            islmap = islmap.add_constraint(constraint)

            space = refmap.get_space()
            constraint = isl.Constraint.alloc_equality(space)
            constraint = constraint.set_coefficient_val(isl.dim_type.in_, 0, 1)
            constraint = constraint.set_coefficient_val(isl.dim_type.set, d , -1)
            constraint = constraint.set_constant_val(0)
            refmap = refmap.add_constraint(constraint)



            
#    print(islmap.range())
    return islmap.range(), refmap.range()

def changeSet(islset, dims, ID):
    k = 0
    islset_ref = islset.copy()
    for i in range(len(dims)):
        islset = islset.set_dim_name(isl.dim_type.set, i, f'{ID}_{i}') ## rename
        if dims[i] == '.':
            islset = islset.insert_dims(isl.dim_type.param, k, 1)
            islset = islset.set_dim_name(isl.dim_type.param, k, f'I{ID}_{i}')

            # ref for subset
            islset_ref = islset_ref.insert_dims(isl.dim_type.param, k, 1)
            id_ref = re.sub(r'\d+','',ID)
            islset_ref = islset_ref.set_dim_name(isl.dim_type.param, k, f'I{id_ref}_{i}')

            space = islset.get_space()
        
            # set = param
            constraint = isl.Constraint.alloc_equality(space)
            constraint = constraint.set_coefficient_val(isl.dim_type.set, i, 1)
            constraint = constraint.set_coefficient_val(isl.dim_type.param,k, -1)
            constraint = constraint.set_constant_val(0)
            islset = islset.add_constraint(constraint)

            space = islset_ref.get_space()
            constraint = isl.Constraint.alloc_equality(space)
            constraint = constraint.set_coefficient_val(isl.dim_type.set, i, 1)
            constraint = constraint.set_coefficient_val(isl.dim_type.param,k, -1)
            constraint = constraint.set_constant_val(0)
            islset_ref = islset_ref.add_constraint(constraint)

            k += 1
        elif dims[i].isdigit():
            islset = islset.insert_dims(isl.dim_type.param, k, 1)
            islset = islset.set_dim_name(isl.dim_type.param, k, f'I{ID}_{i}')

            # ref for subset
            islset_ref = islset_ref.insert_dims(isl.dim_type.param, k, 1)
            id_ref = re.sub(r'\d+','',ID)
            if 'SEND' in id_ref or 'RECV' in id_ref:
                id_ref = re.sub(r'[SEND|RECV]','', id_ref)
            islset_ref = islset_ref.set_dim_name(isl.dim_type.param, k, f'I{id_ref}_{i}')
            space = islset.get_space()

            # set = param
            constraint = isl.Constraint.alloc_equality(space)
            constraint = constraint.set_coefficient_val(isl.dim_type.set, i, 1)
            constraint = constraint.set_coefficient_val(isl.dim_type.param,k, -1)
            constraint = constraint.set_constant_val(0)
            islset = islset.add_constraint(constraint)
            
            space = islset_ref.get_space()
            constraint = isl.Constraint.alloc_equality(space)
            constraint = constraint.set_coefficient_val(isl.dim_type.set, i, 1)
            constraint = constraint.set_coefficient_val(isl.dim_type.param,k, -1)
            constraint = constraint.set_constant_val(0)
            islset_ref = islset_ref.add_constraint(constraint)



            space = islset.get_space()
            constraint = isl.Constraint.alloc_equality(space)
            constraint = constraint.set_coefficient_val(isl.dim_type.set, i , 1)
            constraint = constraint.set_constant_val(-1*int(dims[i]))
            islset = islset.add_constraint(constraint)
            
            space = islset_ref.get_space()
            constraint = isl.Constraint.alloc_equality(space)
            constraint = constraint.set_coefficient_val(isl.dim_type.set, i , 1)
            constraint = constraint.set_constant_val(-1*int(dims[i]))
            islset_ref = islset_ref.add_constraint(constraint)
            k +=1
    return islset,islset_ref



def getMap(expr1, expr2, norelation = []): ## domain , range
    islmap =  isl.Map.from_domain_and_range(expr1.getISL(), expr2.getISL())
    ref = isl.Map.from_domain_and_range(expr1.ref, expr2.ref)
    for i in range(len(expr1.dims)):
        if expr1.dims[i] == "*":# or expr1.dims[i].isdigit():
            continue
        if len(expr2.dims) > i and expr1.dims[i] == expr2.dims[i] and expr1.dims[i].isdigit():
            space = islmap.get_space()
            constraint = isl.Constraint.alloc_equality(space)
            constraint = constraint.set_coefficient_val(isl.dim_type.set, i , 1)
            constraint = constraint.set_coefficient_val(isl.dim_type.in_, i , -1)
            constraint = constraint.set_constant_val(0)
            islmap = islmap.add_constraint(constraint)

            space = ref.get_space()
            constraint = isl.Constraint.alloc_equality(space)
            constraint = constraint.set_coefficient_val(isl.dim_type.set, i , 1)
            constraint = constraint.set_coefficient_val(isl.dim_type.in_, i , -1)
            constraint = constraint.set_constant_val(0)
            ref = ref.add_constraint(constraint)

            continue
        elif len(expr2.dims) > i and expr1.dims[i] == expr2.dims[i] and expr1.dims[i] != '*' and not i in norelation: ## in case of A[.,.] At G[.,.]
            islmap = islmap.insert_dims(isl.dim_type.param,0, 1)
            islmap = islmap.set_dim_name(isl.dim_type.param,0, f"I{islmap.get_dim_name(isl.dim_type.in_,i)}")

            space = islmap.get_space() 
            constraint = isl.Constraint.alloc_equality(space)
            constraint = constraint.set_coefficient_val(isl.dim_type.param, 0 , 1)
            constraint = constraint.set_coefficient_val(isl.dim_type.in_, i , -1)
            constraint = constraint.set_constant_val(0)
            islmap = islmap.add_constraint(constraint)
            
            ref = ref.insert_dims(isl.dim_type.param,0, 1)
            
           # refID =  re.sub(r'([A-Za-z])\d+_', r'\1_', ref.get_dim_name(isl.dim_type.in_,i))
           # refID = f"I{refID}"
           # print(refID)
            ref = ref.set_dim_name(isl.dim_type.param,0, f"I{ref.get_dim_name(isl.dim_type.in_,i)}")

            space = ref.get_space()
            constraint = isl.Constraint.alloc_equality(space)
            constraint = constraint.set_coefficient_val(isl.dim_type.param, 0 , 1)
            constraint = constraint.set_coefficient_val(isl.dim_type.in_, i , -1)
            constraint = constraint.set_constant_val(0)
            ref = ref.add_constraint(constraint)

            space = islmap.get_space()
            constraint = isl.Constraint.alloc_equality(space)
            constraint = constraint.set_coefficient_val(isl.dim_type.set, i , 1)
            constraint = constraint.set_coefficient_val(isl.dim_type.in_, i , -1)
            constraint = constraint.set_constant_val(0)
            islmap = islmap.add_constraint(constraint)
            
            space = ref.get_space()
            dconstraint = isl.Constraint.alloc_equality(space)
            constraint = constraint.set_coefficient_val(isl.dim_type.set, i , 1)
            constraint = constraint.set_coefficient_val(isl.dim_type.in_, i , -1)
            constraint = constraint.set_constant_val(0)
            ref = ref.add_constraint(constraint)
            continue
        
        for j in range(len(expr2.dims)):
            if j in norelation or i in norelation:
                continue
            elif i!=j and expr1.dims[i] == expr2.dims[j] and expr1.dims[i] != '*' and not (expr1.dims[i] == '.' and expr2.dims[j] == '.'): ## or number?
                islmap = islmap.insert_dims(isl.dim_type.param,0, 1)
                islmap = islmap.set_dim_name(isl.dim_type.param,0, f"I{islmap.get_dim_name(isl.dim_type.in_,i)}")
                
                
                space = islmap.get_space()
                constraint = isl.Constraint.alloc_equality(space)
                constraint = constraint.set_coefficient_val(isl.dim_type.param, 0 , 1)
                constraint = constraint.set_coefficient_val(isl.dim_type.in_, i , -1)
                constraint = constraint.set_constant_val(0)
                islmap = islmap.add_constraint(constraint)
         
                ref = ref.insert_dims(isl.dim_type.param,0, 1)
                ref = ref.set_dim_name(isl.dim_type.param,0, f"I{ref.get_dim_name(isl.dim_type.in_,i)}")
                space = ref.get_space()
                constraint = isl.Constraint.alloc_equality(space)
                constraint = constraint.set_coefficient_val(isl.dim_type.param, 0 , 1)
                constraint = constraint.set_coefficient_val(isl.dim_type.in_, i , -1)
                constraint = constraint.set_constant_val(0)
                ref = ref.add_constraint(constraint)

                space = islmap.get_space()
                constraint = isl.Constraint.alloc_equality(space)
                constraint = constraint.set_coefficient_val(isl.dim_type.set, j , 1)
                constraint = constraint.set_coefficient_val(isl.dim_type.in_, i , -1)
                constraint = constraint.set_constant_val(0)
                islmap = islmap.add_constraint(constraint)
                
                space = ref.get_space()
                constraint = isl.Constraint.alloc_equality(space)
                constraint = constraint.set_coefficient_val(isl.dim_type.set, j , 1)
                constraint = constraint.set_coefficient_val(isl.dim_type.in_, i , -1)
                constraint = constraint.set_constant_val(0)
                ref = ref.add_constraint(constraint)
    return islmap, ref

def is_set_subset(expr1,expr2):
    return expr1.is_subset(expr2)

def is_map_subset(expr1,expr2):
    #print("->",expr1)
    #print("->",expr2)
    #print(expr1.is_subset(expr2))
    #print()
#    return (is_set_subset(expr1.range(), expr2.range()) and is_set_subset(expr1.domain(), expr2.domain()))
 #   print(expr2.is_subset(expr1))
    return expr1.is_subset(expr2)
