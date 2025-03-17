#from functions import *
#from islFunctions import *
from shadowClass import *
class Assert:
    def __init__(self, lineno, leftside, rightside, key):
        self.lineno = lineno
        self.filename  = f'{lineno:03d}assert.py'
        self.leftside = leftside
        self.rightside = rightside
        self.key = key ## 0 : in 1: at
        self.map , self.ref = getMap(leftside, rightside)
    
    def ifChange(self, cond):
        leftside = ifSet(cond, self.leftside , self.leftside.dims)
        self.leftside.setISL(leftside[0], leftside[1])

        rightside = ifSet(cond, self.rightside , self.rightside.dims)
        self.rightside.setISL(rightside[0], rightside[1])

        self.map, self.ref = getMap(self.leftside,self.rightside)

    def z3Gen(self):
        if self.key == 0:
            return self.gridAssert()
        else:
            return self.placeAssert()

    
    def has_data(self):
        D2G = getD2G()
        for (i0,i1) in sorted(D2G.keys(), key=lambda x: x[0], reverse=True):
            if i1 == self.leftside.getTensorName():
                #print(D2G[(i0,i1)])
                is_subset = is_map_subset(self.ref, D2G[(i0,i1)].recvMap(1))
                if is_subset:
                    return D2G[(i0,i1)]
        return False

    def defineCurrentState(self,holder):
        init = []
        constraints = []
        grid = []
        sendTensorName = self.leftside.getTensorName()
        sendexprISLDims = ', '.join(getSetDims(self.leftside.getISL()))
        sendgexprISLDims = ', '.join(getSetDims(holder.get_gexpr().getISL()))
        sendtime = f"t{holder.timer}"
        init.append(sendtime)
       #    constraints += [f"STATE({sendTensorName}, {sendexprISLDims}, {sendgexprISLDims}, {sendtime}) == {holder.getState()}"]
        '''
        k = 0
        sendGrid = self.sendGrid()
        for i in self.rightside.commMap.get("COMM_WORLD").dims:
            init.append(f"ANY_DIMS_{k}")
            constraints.append(f"0 <= ANY_DIMS_{k}, ANY_DIMS_{k} < {i}")
            constraints.append(f"ANY_DIMS_{k} != {sendGrid.gridISL.get_dim_name(isl.dim_type.set,k)}")
            grid.append(f"ANY_DIMS_{k}")
            k += 1
        b = f"b_{useBoolCounter()}"

#        const = f"Implies(And({', '.join(constraints)}), STATE({sendTensorName}, {sendexprISLDims}, {', '.join(grid)}, {sendtime}) == CONST_ANY)"
        '''
        #constraints += [f"ForAll([{', '.join(grid)}], {const})"]
        constraints += [f"STATE({sendTensorName}, {sendexprISLDims}, {sendgexprISLDims}, {sendtime}) == {holder.getState()}"]
        constraints += [f"STATE({sendTensorName}, {sendexprISLDims}, {sendgexprISLDims}, {sendtime}) > 1"] ## not none
        constraints += [f"t{holder.timer} == {holder.timer}"]

        return init, constraints

    def placeAssert(self):
        init = ["HAS_DATA"]#, f"{self.recv_expr.getTensorName()}_AT_{self.recv_gexpr.getGridName()}"]#, "NOT_REDUNDANT"]
        constraints = []

        holder = self.has_data()
        if holder:
            z3val = holder.z3()
            init += z3val[0]
            constraints += z3val[1]
            constraints.append(f"HAS_DATA == {holder.timer}, HAS_DATA > -1")

            constraints += islConstraints_map(self.map , self.leftside.paramMap) ## relation between sender and receiver is contained previously; move has pexpr AT gexpr
            init += islInit_map(self.map)

            for i,j in zip(getSetDims(self.leftside.getISL()), getSetDims(holder.get_expr().getISL())):
                init.append(i)
                constraints.append(f"{i} == {j}")
        else:
            constraints.append(f"HAS_DATA == -1, HAS_DATA > -1")
            holder = shadow(self.lineno , self.leftside, self.rightside, self.map, self.ref)
            z3val = holder.z3()
            init += z3val[0]
            constraints += z3val[1]
            constraints.append(f"HAS_DATA == {holder.timer}, HAS_DATA > -1")



        sendexpr = self.leftside.z3()
        #recvexpr = self.rightside.z3()
        init += sendexpr[0] #+ recvexpr[0]
        constraints += sendexpr[1] #+ recvexpr[1]



        params = ("IntSort(), " * (self.rightside.gridSize() + self.leftside.tensorSize() + 3))[:-2] # tensorName, partition, grid, time = output

        init.append(f"STATE = Function('STATE', {params})")



        cState = self.defineCurrentState(holder)
        init += cState[0]
        constraints += cState[1]

        return init, constraints

    def gridAssert(self):
        init = []
        constraints = []
        init += islInit_map(self.map)
        const =  islConstraints_map(self.map,self.leftside.paramMap)
        if not const:
            init.append('empty_map')
            constraints.append('empty_map == 1, empty_map > 1')
            return init, constraints
        
        constraints += const


#        init += islInit_set(self.leftside.getISL())
 #       init += islInit_set(self.rightside.getISL())

        init += [f"{self.leftside.gName}_LSIZE", f"{self.rightside.gName}_RSIZE"]
        
        lsize = commsize(self.leftside.getISL().to_str())
        rsize = commsize(self.rightside.getISL().to_str())

        constraints += [f"{self.leftside.gName}_LSIZE == {lsize} ", f"{self.rightside.gName}_RSIZE == {rsize}", f"{self.leftside.gName}_LSIZE <= {self.rightside.gName}_RSIZE"]
#        print(self.leftside.getISL())       
 #       print(self.rightside.getISL())
  #      print(self.map)


        constraints += commEquality(self.leftside.getISL(), self.rightside.getISL(), self.leftside)

        if self.leftside.gridSize() > 1:
            for i in range(self.leftside.gridSize()):
                init.append(f"{self.leftside.gName}_LSIZE_{i}")
                init.append(f"{self.rightside.gName}_RSIZE_{i}")
                constraints.append(f"{self.leftside.gName}_LSIZE_{i} == "+ card_index(self.leftside.getISL().to_str(),i))
                constraints.append(f"{self.rightside.gName}_RSIZE_{i} == "+ card_index(self.rightside.getISL().to_str(),i))
                constraints.append(f"{self.leftside.gName}_LSIZE_{i} <=  {self.rightside.gName}_RSIZE_{i}") 

        return init, constraints

