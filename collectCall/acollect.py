#from functions import *
#from islFunctions import *
from shadowClass import *
class acollect:
    def __init__(self,lineno,ID,send_expr,recv_expr,g_expr):
        self.ID = ID
        self.filename = f'{lineno:03d}{ID}.py'
        self.lineno = lineno
        self.funcName = ID.lower().replace('-','')
        self.send_expr = send_expr
        self.recv_expr = recv_expr
        self.g_rexpr = g_expr
        self.acollectMap,self.ref = getMap(recv_expr,g_expr)
        self.sendmap , self.sendref = '',''
        self.timer = 0
        self.functionID = 2

    def loopChange(self,loopISL, loopVar):
        self.send_expr.pexprISL, self.send_expr.ref = loopSet(loopISL, loopVar, self.send_expr, self.send_expr.dims)
        self.recv_expr.pexprISL, self.recv_expr.ref = loopSet(loopISL, loopVar, self.recv_expr, self.recv_expr.dims)
        self.g_rexpr.gridISL, self.g_rexpr.ref = loopSet(loopISL, loopVar,  self.g_rexpr , self.g_rexpr.dims)

        self.acollectMap, self.ref = getMap(self.recv_expr,self.g_rexpr)

    def has_data(self):
        D2G = getD2G()
        for (i0,i1) in list(D2G.keys()):
            if i1 == self.send_expr.getTensorName():
                sendTmp = getMap(self.send_expr, D2G[(i0,i1)].get_gexpr())[1]
#                is_subset = is_set_subset(self.send_expr.ref, D2G[(i0,i1)].get_expr().ref)
                is_subset = is_map_subset(sendTmp ,  D2G[(i0,i1)].recvMap(1))
                if is_subset:
#                    return D2G[(i0,i1)]
                    self.sendmap, self.sendref = D2G[(i0,i1)].recvMap(2) ## send back both
                    return D2G[(i0,i1)]
        return False

    def recvAtgrecv(self):
        D2G = getD2G()
        for (i0,i1) in list(D2G.keys()):
            if i1 == self.recv_expr.getTensorName():
                is_subset = is_map_subset(self.ref, D2G[(i0,i1)].ref)
                if is_subset:
                    return i0

        return -1
    def z3(self):
        constraints = islConstraints_map(self.acollectMap, self.send_expr.paramMap)
        init = islInit_map(self.acollectMap)
        return init, constraints
   
    def sendMap(self, key = 0): #TODO -- done
        if key == 0 :
            return self.sendmap
        elif key == 1:
            return self.sendref
        else:
            return self.sendmap, self.ref

    def recvMap(self, key = 0):
        if key == 0:
            return self.acollectMap
        elif key == 1:
            return self.ref
        else:
            return self.acollectMap, self.ref
    
    def sendGrid(self):
        tmp = self.has_data()
        if tmp:
            return tmp.get_gexpr()
        else:
            return False

    def getState(self): 
        return "CONST_HOLD"

    def get_gexpr(self):
        return self.g_rexpr
    def get_expr(self):
        return self.recv_expr
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
        if sendGrid:
            for i in self.g_rexpr.commMap.get("COMM_WORLD").dims:
                init.append(f"ANY_DIMS_{k}")
                constraints.append(f"0 <= ANY_DIMS_{k}, ANY_DIMS_{k} < {i}")
                constraints.append(f"ANY_DIMS_{k} != {sendGrid.gridISL.get_dim_name(isl.dim_type.set,k)}") 
                grid.append(f"ANY_DIMS_{k}")
                k += 1
            b = f"b_{useBoolCounter()}"
        
            const = f"Implies(And({', '.join(constraints)}), STATE({sendTensorName}, {sendexprISLDims}, {', '.join(grid)}, {sendtime}) == CONST_ANY)"

            constraints += [f"ForAll([{', '.join(grid)}], {const})"]
        constraints += [f"STATE({sendTensorName}, {sendexprISLDims}, {sendgexprISLDims}, {sendtime}) == {holder.getState()} "]
        constraints += [f"STATE({sendTensorName}, {sendexprISLDims}, {sendgexprISLDims}, {sendtime}) > 1 "]
        constraints += [f"t{holder.timer} == {holder.timer}"]

        return init, constraints 

    def defineAfterState(self, holder):
        init = []
        constraints = []

        sendTensorName = self.send_expr.getTensorName()
        sendexprISLDims = ', '.join(getSetDims(self.send_expr.getISL()))
        sendgexprISLDims = ', '.join(getSetDims(holder.get_gexpr().getISL()))
        self.timer = holder.timer+1
        time = f"t{self.timer}"
        sendtime = f"t{holder.timer}"
        init.append(time)
        #print(self.timer)
        prevtime = f"t{holder.timer}"
        constraints += [f"{time} == {self.timer}"]
        constraints += [f"STATE({sendTensorName}, {sendexprISLDims}, {sendgexprISLDims}, {sendtime}) == STATE({sendTensorName}, {sendexprISLDims}, {sendgexprISLDims}, {time})" ]
        
        recvTensorName = self.recv_expr.getTensorName()
        recvexprISLDims = ', '.join(getSetDims(self.recv_expr.getISL()))
        recvgexprISLDims = ', '.join(getSetDims(self.g_rexpr.getISL()))
        

        constraints += [f"STATE({recvTensorName}, {recvexprISLDims}, {sendgexprISLDims}, {time}) == CONST_HOLD"]

        return init, constraints 
    def z3Gen(self):
        func = getattr(self, self.funcName)
        return func()

    def allgather(self):
        init = ["HAS_DATA", f"{self.recv_expr.getTensorName()}_AT_{self.g_rexpr.getGridName()}"]#, "NOT_REDUNDANT"]
        constraints = []

        holder = self.has_data()
        if holder:
            z3val = holder.z3()
            init += z3val[0]
            constraints += z3val[1]
            constraints.append(f"SEND_TENSOR_SIZE == {card(holder.sendMap().to_str())}, SEND_TENSOR_SIZE > 0")
            constraints.append(f"HAS_DATA == {holder.timer}, HAS_DATA > -1")
            init.append("SEND_TENSOR_SIZE")
            for i,j in zip(getSetDims(self.send_expr.getISL()), getSetDims(holder.get_expr().getISL())):
                init.append(i)
                constraints.append(f"{i} == {j}")
        else:
            constraints.append(f"HAS_DATA == -1, HAS_DATA > -1")
            holder = shadow(self.lineno , self.send_expr, self.g_rexpr, self.acollectMap, self.ref)
            z3val = holder.z3()
            init += z3val[0]
            constraints += z3val[1]
#            constraints.append(f"SEND_CARD == {card(self.sendmap.to_str())}, SEND_CARD < 2")
            constraints.append(f"HAS_DATA == {holder.timer}, HAS_DATA > -1")
            init.append("SEND_TENSOR_SIZE")
            init += islInit_set(self.send_expr.getISL())
       

        ## num. of communicators = size of set USING comm
        init.append("COMMUNICATOR_SIZE")
        constraints.append(f"COMMUNICATOR_SIZE == { commsize(self.g_rexpr.getISL().to_str()) }")
        constraints.append("COMMUNICATOR_SIZE > 1")

        sendexpr = self.send_expr.z3()
        recvexpr = self.recv_expr.z3()
        init += sendexpr[0] + recvexpr[0]
        constraints += sendexpr[1] + recvexpr[1]

        rcvr = self.z3()
        init += rcvr[0]
        constraints += rcvr[1]
        
        constraints.append(f"{self.recv_expr.getTensorName()}_AT_{self.g_rexpr.getGridName()} "+
                f" == {self.recvAtgrecv()}")#, {self.recv_expr.getTensorName()}_AT_{self.g_rexpr.getGridName()} >= 0") ## to do- tensor at rcvr
        
        ## state
        exprParamSize = 0
        if self.send_expr.tensorSize() < self.recv_expr.tensorSize():
            exprParamSize = self.recv_expr.tensorSize()
        else:
            exprParamSize = self.send_expr.tensorSize()
        params = ("IntSort(), " * (self.g_rexpr.gridSize() + exprParamSize + 3))[:-2] # tensorName, partition, grid, time = output
        init.append(f"STATE = Function('STATE', {params})")
       
        constraints.append(f"RECV_TENSOR_SIZE == {card(self.acollectMap.to_str())}, RECV_TENSOR_SIZE > SEND_TENSOR_SIZE")
        init.append("RECV_TENSOR_SIZE")
        cState = self.defineCurrentState(holder)
        init += cState[0]
        constraints += cState[1]
        
        aState = self.defineAfterState(holder)
        init += aState[0]
        constraints += aState[1]
        updateD2G(self.recv_expr.getTensorName(),self)

        return init, constraints
    def reduce(self):
        init = ["HAS_DATA", f"{self.recv_expr.getTensorName()}_AT_{self.g_rexpr.getGridName()}"]#, "NOT_REDUNDANT"]
        constraints = []

        holder = self.has_data()
        if holder:
            z3val = holder.z3()
            init += z3val[0]
            constraints += z3val[1]
            constraints.append(f"SEND_CARD == {card(holder.sendMap().to_str())}")
            constraints.append(f"HAS_DATA == {holder.timer}, HAS_DATA > -1")
            init.append("SEND_CARD")
            for i,j in zip(getSetDims(self.send_expr.getISL()), getSetDims(holder.get_expr().getISL())):
                init.append(i)
                constraints.append(f"{i} == {j}")
        else:
            constraints.append(f"HAS_DATA == -1, HAS_DATA > -1")

        sendexpr = self.send_expr.z3()
        recvexpr = self.recv_expr.z3()
        init += sendexpr[0] + recvexpr[0]
        constraints += sendexpr[1] + recvexpr[1]

        rcvr = self.z3()
        init += rcvr[0]
        constraints += rcvr[1]

        constraints.append(f"{self.recv_expr.getTensorName()}_AT_{self.g_rexpr.getGridName()} "+
                f" == {self.recvAtgrecv()}, {self.recv_expr.getTensorName()}_AT_{self.g_rexpr.getGridName()} >= 0")

        ## state
        exprParamSize = 0
        if self.send_expr.tensorSize() < self.recv_expr.tensorSize():
            exprParamSize = self.recv_expr.tensorSize()
        else:
            exprParamSize = self.send_expr.tensorSize()
        params = ("IntSort(), " * (self.g_rexpr.gridSize() + exprParamSize + 3))[:-2] # tensorName, partition, grid, time = output
        init.append(f"STATE = Function('STATE', {params})")

        constraints.append(f"RECV_CARD == {card(self.acollectMap.to_str())}, RECV_CARD <= SEND_CARD")
        constraints.append(f"RECV_CARD < 2")
        init.append("RECV_CARD")
        cState = self.defineCurrentState(holder)
        init += cState[0]
        constraints += cState[1]

        aState = self.defineAfterState(holder)
        init += aState[0]
        constraints += aState[1]
        updateD2G(self.recv_expr.getTensorName(),self)


        return init, constraints

