from islFunctions import *
from functions import *
import random

class Parameter:
    def __init__(self,paramName, constraint,paramsMap):
        self.paramName = paramName
        self.constraint = constraint
        self.paramsMap = paramsMap
    def getConstraint(self):
        resolved_constraints =self.constraint  # Copy current constraints
        dependencies = [self.paramName]
        for const in self.constraint:
            parent = re.split(r'[<>]=?', const)
            if parent[1] in self.paramsMap and not (parent[1] in self.paramName) and not parent[1].isdigit():
                parent_param = self.paramsMap[parent[1]]
                parent_constraints, parent_dependencies = parent_param.getConstraint()
                resolved_constraints += parent_constraints
                dependencies.append( parent[1])
            """
            elif parent[0] in self.paramsMap and not (parent[0] in self.paramName) and not parent[0].isdigit():
                parent_param = self.paramsMap[parent[0]]
                parent_constraints, parent_dependencies = parent_param.getConstraint()
                resolved_constraints += parent_constraints
                dependencies.append( parent[0])
            """
        return resolved_constraints, dependencies 


class Tensor:
    tensorsID = [0]
    def __init__(self, tName, dims,paramMap):
        self.tName = tName 
        self.dims = dims
        self.paramMap = paramMap
        self.tensorISL = getSet(dims,tName,paramMap)
        self.ID = 0
        while self.ID in Tensor.tensorsID:
            self.ID = random.randint(1,50) 

    def z3(self):
        return [self.tName], [f"{self.tName} == {self.ID}"]
        
class Grid:
    worldFlag = True
    def __init__(self, lineno,dims,paramMap,commMap):
        if Grid.worldFlag:
            self.gName = "COMM_WORLD"
        #    Grid.worldFlag = False
        else:
            self.gName = "COMM_LN_"+str(lineno)
        self.dims = dims
        self.paramMap = paramMap

        if Grid.worldFlag:
            self.ref = self.gridISL = getSet(dims, "COMM_WORLD",paramMap)
            
            Grid.worldFlag = False
        else:
            self.gridISL, self.ref = changeSet(commMap.get("COMM_WORLD").gridISL , dims, f'g{lineno}')
        self.commMap = commMap

    def getISL(self):
        return self.gridISL
    def gridSize(self):
        return len(self.dims)
    def getGridName(self):
        return self.gName
    def setISL(self, islset ,islref):
        self.gridISL = islset
        self.ref = islref

class phi(Grid):
    def __init__(self, lineno, dims, functionName,functionDims,paramMap, commMap):
        self.gexpr = Grid(lineno, dims, paramMap, commMap) ## parent grid for phi
        self.funcName = functionName
        self.funcDims = functionDims
        super().__init__(lineno+1,dims,paramMap,commMap) # new grid
        print(self.funcName)
        getattr(self,self.funcName)()
        #self.Prev()
    def Even(self):
        
        tmp = getMap(self.gexpr , self)
        
        tmp0 = tmp[0].to_str().split("}")[0]
        tmp1 = tmp[1].to_str().split("}")[0] ## ref
        
        for i in self.funcDims:
            i = int(i)
            setname = tmp[0].get_dim_name(isl.dim_type.set, i)
            inname = tmp[0].get_dim_name(isl.dim_type.in_, i)
            tmp0 += f" and {setname} = {inname} and {setname} % 2 = 0 "
       
            setname = tmp[1].get_dim_name(isl.dim_type.set, i)
            inname = tmp[1].get_dim_name(isl.dim_type.in_, i)
            
            tmp1 += f" and {setname} = {inname} and {setname} % 2 = 0"

        self.gridISL = isl.Map(tmp0 + "}").domain()
        self.ref = isl.Map(tmp1 + "}").domain()
    
    def Odd(self):
        tmp = getMap(self.gexpr , self)

        tmp0 = tmp[0].to_str().split("}")[0]
        tmp1 = tmp[1].to_str().split("}")[0]

        for i in self.funcDims:
            i = int(i)
            setname = tmp[0].get_dim_name(isl.dim_type.set, i)
            inname = tmp[0].get_dim_name(isl.dim_type.in_, i)
            tmp0 += f" and {setname} = {inname} and {setname} % 2 = 1 "
            setname = tmp[1].get_dim_name(isl.dim_type.set, i)
            inname = tmp[1].get_dim_name(isl.dim_type.in_, i)
            tmp1 += f" and {setname} = {inname} and {setname} % 2 = 1 "

        self.gridISL = isl.Map(tmp0 + "}").domain()
        self.ref = isl.Map(tmp1 + "}").domain()
        #print(self.gridISL)

    def Next(self):
        tmp = getMap(self.gexpr , self, self.funcDims)
        tmp0 = tmp[0].to_str().split("}")[0]
        tmp1 = tmp[1].to_str().split("}")[0]
        for i in self.funcDims:
            i = int(i)
            setname = tmp[0].get_dim_name(isl.dim_type.set, i)
            inname = tmp[0].get_dim_name(isl.dim_type.in_, i)
            tmp0 += f" and {setname} = {inname} +1"
            setname = tmp[1].get_dim_name(isl.dim_type.set, i)
            inname = tmp[1].get_dim_name(isl.dim_type.in_, i)
            tmp1 += f" and {setname} = {inname} +1"
        self.gridISL = isl.Map(tmp0 + "}").domain()
        self.ref = isl.Map(tmp1 + "}").domain()
        #print(self.gridISL)
    def Prev(self):
        tmp = getMap(self.gexpr , self, self.funcDims)
        #print(tmp[0])
        tmp0 = tmp[0].to_str().split("}")[0]
        tmp1 = tmp[1].to_str().split("}")[0]
        for i in self.funcDims:
            i = int(i)
            setname = tmp[0].get_dim_name(isl.dim_type.set, i)
            inname = tmp[0].get_dim_name(isl.dim_type.in_, i)
            tmp0 += f" and {setname} = {inname} - 1"
            setname = tmp[1].get_dim_name(isl.dim_type.set, i)
            inname = tmp[1].get_dim_name(isl.dim_type.in_, i)
            tmp1 += f" and {setname} = {inname} - 1"
        #TODO range or domaim
        self.gridISL = isl.Map(tmp0 + "}").domain()
        self.ref = isl.Map(tmp1 + "}").domain()
        #print("=>",self.gridISL)


class pexpr:
    exprCounter = 0
    def __init__(self, tensorPtr, dims,paramMap ):
        self.tensorPtr = tensorPtr
        self.dims = dims
        self.ID = pexpr.exprCounter
        pexpr.exprCounter += 1
        self.pexprISL, self.ref  = changeSet(tensorPtr.tensorISL, dims, f'{tensorPtr.tName}{self.ID}')
        #print(self.pexprISL)
        self.paramMap = paramMap 
    def getISL(self):
        return self.pexprISL
    def z3(self):
        return self.tensorPtr.z3()
    def getTensorName(self):
        return self.tensorPtr.tName
    def tensorSize(self):
        return len(self.dims)
    def tensorDims(self):
        return self.tensorPtr.dims
    def setISL(self,islset, islref):
        self.pexprISL = islset
        self.ref = islref
class Part:
    def __init__(self,p_expr, partList):#, tensor):
        self.p_expr = p_expr
        self.partList = partList
#        self.tensor = tensor
        self.partValue, self.partDims = self.getPart()
        
        self.p_expr.tensorPtr.tensorISL = getSet(self.partDims, self.p_expr.getTensorName(), self.p_expr.paramMap, self.p_expr.tensorDims())
        self.p_expr.pexprISL, self.p_expr.ref = changeSet(self.p_expr.tensorPtr.tensorISL, self.p_expr.tensorPtr.dims, f'{self.p_expr.tensorPtr.tName}{self.p_expr.ID}')

        #print("=>",self.p_expr.pexprISL)

    def getPart(self):
        k = 0
        ls = []
        ls2 = []
        tensorDims = self.p_expr.tensorDims()
        tensorName = self.p_expr.getTensorName()
        for i in self.partList:
         #   print(i,k)
            if self.p_expr.dims[k] != '*':
                ls.append(f"{tensorDims}/{i}")
            else:
                ls.append(f"{tensorDims}")
            
            ls2.append(f"PART_{tensorName}_{k}")
            k += 1

        return ls, ls2
    def z3(self):
        constraint = []
        for (i,j) in zip(self.partValue, self.partDims):
            constraint.append(f"{i} <= {j}, {i} > 0")
        return constraint
class Place:
    def __init__(self,p_expr, g_expr):
        self.p_expr = p_expr
        self.g_expr = g_expr
        self.placeISL, self.ref = getMap(p_expr,g_expr)
        self.timer = globalTimer
        updateD2G(self.p_expr.getTensorName(),self, True)

#        print(self.placeISL)
    def get_expr(self):
        return self.p_expr

    def get_gexpr(self):
        return self.g_expr

    def getState(self):
        return "CONST_OWN"

    def sendMap(self, key = 0):
        if key == 0:
            return self.placeISL
        elif key == 1:    
            return self.ref
        else:
            return self.placeISL, self.ref
    
    def recvMap(self, key = 0):
        if key == 0:
            return self.placeISL
        elif key == 1:    
            return self.ref
        else:
            return self.placeISL, self.ref
    
    def recvGrid(self):
        return self.g_expr

    def z3(self):
        constraints = islConstraints_map(self.placeISL, self.p_expr.paramMap)
        init = islInit_map(self.placeISL)
        return init,constraints


class equals:
    def __init__(self, leftside, rightside):
        self.leftside = leftside
        self.rightside = rightside

        self.is_equal = leftside.ref.is_equal(rightside.ref)

        print(self.is_equal)

    def get_equality():
        return self.is_equal

    def z3(self):
        init = ["if_equality_cond"]
        constraints = [f"And({init[0]} == {self.is_equal}, {init[0]})"]
        
        init += islInit_set(self.leftside.getISL())
        constraints += islConstraints_set(self.leftside.getISL())
        return init, constraints
