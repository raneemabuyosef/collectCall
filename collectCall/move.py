#from functions import *
#from islFunctions import *
from shadowClass import *
class move:
    def __init__(self, lineno, send_expr, send_gexpr, recv_expr, recv_gexpr):
        self.filename = f'{lineno:03d}move.py'
        self.send_expr = send_expr
        self.send_gexpr = send_gexpr 
        self.recv_expr = recv_expr
        self.recv_gexpr = recv_gexpr
        self.moveMap, self.ref = getMap(recv_expr,recv_gexpr)
        self.sendmap , self.sendref = getMap(send_expr, send_gexpr)
        self.functionID = 1 
        self.lineno = lineno
        self.timer = 0

    def ifChange(self, cond):
        self.send_expr.pexprISL, self.send_expr.ref = ifSet(cond, self.send_expr, self.send_expr.dims)
        self.send_gexpr.gridISL, self.send_gexpr.ref = ifSet(cond,  self.send_gexpr , self.send_gexpr.dims)
        self.recv_expr.pexprISL, self.recv_expr.ref = ifSet(cond, self.recv_expr, self.recv_expr.dims)
        self.recv_gexpr.gridISL, self.recv_gexpr.ref = ifSet(cond,  self.recv_gexpr , self.recv_gexpr.dims)
        
        self.moveMap, self.ref = getMap(self.recv_expr,self.recv_gexpr)
        self.sendmap , self.sendref = getMap(self.send_expr, self.send_gexpr)
        

    
    def loopChange(self,loopISL, loopVar):
        self.send_expr.pexprISL, self.send_expr.ref = loopSet(loopISL, loopVar, self.send_expr, self.send_expr.dims)
        self.send_gexpr.gridISL, self.send_gexpr.ref = loopSet(loopISL, loopVar,  self.send_gexpr , self.send_gexpr.dims)
        self.recv_expr.pexprISL, self.recv_expr.ref = loopSet(loopISL, loopVar, self.recv_expr, self.recv_expr.dims)
        self.recv_gexpr.gridISL, self.recv_gexpr.ref = loopSet(loopISL, loopVar,  self.recv_gexpr , self.recv_gexpr.dims)

        self.moveMap, self.ref = getMap(self.recv_expr,self.recv_gexpr)
        self.sendmap , self.sendref = getMap(self.send_expr, self.send_gexpr)


    def has_data(self):
        D2G = getD2G()
#        for (i0,i1) in list(D2G.keys()):
        for (i0,i1) in sorted(D2G.keys(), key=lambda x: x[0], reverse=True):
            if i1 == self.send_expr.getTensorName():
                is_subset = is_map_subset(self.sendref, D2G[(i0,i1)].recvMap(1))
                if is_subset:
                    return D2G[(i0,i1)]
#            if self.functionID == 2:
 #               break

        return False
    def sendGrid(self):
        return self.send_gexpr
    
    def get_expr(self):
        return self.recv_expr
    
    def sendMap(self, key = 0):
        if key == 0:
            return self.sendmap
        elif key == 1:
            return self.sendref
        else:
            return self.sendmap, self.sendref

    def recvMap(self, key = 0):
        if key == 0:
            return self.moveMap
        elif key == 1:
            return self.ref
        else:
            return self.moveMap, self.ref
    
    def get_gexpr(self):
        return self.recv_gexpr
    def z3(self):
        constraints = islConstraints_map(self.moveMap, self.send_expr.paramMap)
        init = islInit_map(self.moveMap)
        return init, constraints
    
    def defineCurrentState(self,holder):
        init = []
        constraints = []
        grid = []
        sendTensorName = self.send_expr.getTensorName()
        sendexprISLDims = ', '.join(getSetDims(self.send_expr.getISL()))
        sendgexprISLDims = ', '.join(getSetDims(holder.get_gexpr().getISL()))
        sendtime = f"t{holder.timer}"
        init.append(sendtime)
    #    constraints += [f"STATE({sendTensorName}, {sendexprISLDims}, {sendgexprISLDims}, {sendtime}) == {holder.getState()}"]

        k = 0
        sendGrid = self.sendGrid()
        for i in self.send_gexpr.commMap.get("COMM_WORLD").dims:
            init.append(f"ANY_DIMS_{k}")
            constraints.append(f"0 <= ANY_DIMS_{k}, ANY_DIMS_{k} < {i}")
            constraints.append(f"ANY_DIMS_{k} != {sendGrid.gridISL.get_dim_name(isl.dim_type.set,k)}")
            grid.append(f"ANY_DIMS_{k}")
            k += 1
        b = f"b_{useBoolCounter()}"

        const = f"Implies(And({', '.join(constraints)}), STATE({sendTensorName}, {sendexprISLDims}, {', '.join(grid)}, {sendtime}) == CONST_ANY)"

        constraints += [f"ForAll([{', '.join(grid)}], {const})"]
        constraints += [f"STATE({sendTensorName}, {sendexprISLDims}, {sendgexprISLDims}, {sendtime}) == {holder.getState()}"]
        constraints += [f"STATE({sendTensorName}, {sendexprISLDims}, {sendgexprISLDims}, {sendtime}) > 3"] ## not none and has to be own
        constraints += [f"t{holder.timer} == {holder.timer}"]

        return init, constraints

    def getState(self): # recv, sender has shadow object
        return "CONST_OWN"
    def defineAfterState(self, holder):
        init = []
        constraints = []
        if holder:
            sendTensorName = self.send_expr.getTensorName()
            sendexprISLDims = ', '.join(getSetDims(self.send_expr.getISL()))
            sendgexprISLDims = ', '.join(getSetDims(holder.get_gexpr().getISL()))
            self.timer = holder.timer+1
        time = f"t{self.timer}"
        init.append(time)
        #print(self.timer)

        prevtime = f"t{holder.timer}"
        constraints += [f"{time} == {self.timer}"]
        constraints += [f"STATE({sendTensorName}, {sendexprISLDims}, {sendgexprISLDims}, {time}) == CONST_NONE" ]

        recvTensorName = self.recv_expr.getTensorName()
        recvexprISLDims = ', '.join(getSetDims(self.recv_expr.getISL()))
        recvgexprISLDims = ', '.join(getSetDims(self.recv_gexpr.getISL()))


        constraints += [f"STATE({recvTensorName}, {recvexprISLDims}, {sendgexprISLDims}, {time}) == CONST_OWN"]

        return init, constraints

    def z3Gen(self):
        init = ["HAS_DATA"]#, f"{self.recv_expr.getTensorName()}_AT_{self.recv_gexpr.getGridName()}"]#, "NOT_REDUNDANT"]
        constraints = []

        holder = self.has_data()
        if holder:
            z3val = holder.z3()
            init += z3val[0]
            constraints += z3val[1]
            constraints.append(f"SEND_CARD == {card(self.sendmap.to_str())}, SEND_CARD < 2")
            constraints.append(f"HAS_DATA == {holder.timer}, HAS_DATA > -1")
            init.append("SEND_CARD")

            constraints += islConstraints_map(self.sendmap , self.send_expr.paramMap) ## relation between sender and receiver is contained previously; move has pexpr AT gexpr
            init += islInit_map(self.sendmap)

            for i,j in zip(getSetDims(self.send_expr.getISL()), getSetDims(holder.get_expr().getISL())):
                init.append(i)
                constraints.append(f"{i} == {j}")
        else:
            constraints.append(f"HAS_DATA == -1, HAS_DATA > -1")
            holder = shadow(self.lineno , self.send_expr, self.send_gexpr, self.sendmap, self.sendref)
            z3val = holder.z3()
            init += z3val[0]
            constraints += z3val[1]
            constraints.append(f"SEND_CARD == {card(self.sendmap.to_str())}, SEND_CARD < 2")
            constraints.append(f"HAS_DATA == {holder.timer}, HAS_DATA > -1")
            init.append("SEND_CARD")
 
        sendexpr = self.send_expr.z3()
        recvexpr = self.recv_expr.z3()
        init += sendexpr[0] + recvexpr[0]
        constraints += sendexpr[1] + recvexpr[1]

        rcvr = self.z3()
        init += rcvr[0]
        constraints += rcvr[1]

        if self.send_expr.tensorSize() < self.recv_expr.tensorSize():
            exprParamSize = self.recv_expr.tensorSize()
        else:
            exprParamSize = self.send_expr.tensorSize()

        params = ("IntSort(), " * (self.send_gexpr.gridSize() + exprParamSize + 3))[:-2] # tensorName, partition, grid, time = output
        init.append(f"STATE = Function('STATE', {params})")

        constraints.append(f"RECV_CARD == {card(self.moveMap.to_str())}, RECV_CARD == SEND_CARD")
        init.append("RECV_CARD")

    
        cState = self.defineCurrentState(holder)
        init += cState[0]
        constraints += cState[1]
        
        aState = self.defineAfterState(holder)
        init += aState[0]
        constraints += aState[1]

        updateD2G(self.recv_expr.getTensorName(),self)
        global globalTimer
        globalTimer -= 1
        
        shadowSend = shadow(self.lineno , self.send_expr, self.send_gexpr, self.sendmap, self.sendref)
        
        self.timer = shadowSend.timer = updateD2G(shadowSend.send_expr.getTensorName(), shadowSend)
        #print(self.timer)
        return init, constraints



