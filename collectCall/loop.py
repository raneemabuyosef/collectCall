#from functions import *
from ifstmt import *
import re
import islpy as isl
class Loop:
    def __init__(self, lineno, loopVar, LB, UB, loopbody, variablesMap):
        self.filename =  f'{lineno:03d}loop.py'
        self.loopVar = loopVar
        self.LB = LB
        self.UB = UB
        self.variablesMap = variablesMap
        self.loopBody = loopbody
        self.loopISL = self.set()        
        self.loopbody()

    def loopbody(self):
        for i in self.loopBody:
            if isinstance(i, ifstmt):
                continue
            i.loopChange(self.loopISL, self.loopVar)

    def set(self):
        dimensions = [self.LB, self.UB]
        param = []
        constraints = []
        ops = r'+|-|/|*|%'
        for i in dimensions:
            i = i.strip()
            if not i.isdigit():
                tmp = i
                if ops in i:
                    tmp = re.split(r'+|-|/|*|%', i)

                for j in tmp:
                    if j in self.variablesMap:
                        j = j.strip()
                        param.append(j)
                        constraints.append(self.variablesMap.get(j).constraint)
        
        return isl.Set(f"[{','.join(param)}] -> {{ [{self.loopVar}] : {self.LB} <= {self.loopVar} < {self.UB} }}")


    def z3Gen(self):
        self.gen() 

    def gen(self):
        for cmd in self.loopBody:
            print("\t", cmd.filename)
            f = open(cmd.filename,'w')
            init , consts = cmd.z3Gen()
            header = "from z3 import *\n\n"
            init = "\n".join(self.Z3Init(list(set(init)))) +"\n\n"

            k = 4
            for i in ["CONST_OWN", "CONST_HOLD", "CONST_ANY", "CONST_NONE"]:
                consts.append(f"{i} == {k}")
                k -= 1
            consts =  "solver = Solver()\n" + "\n".join(["solver.add({})".format(const) for const in consts])+"\n"
            footer = "print(solver.check())\n"

            f.writelines(header + init + consts + footer)
            f.close()



    def Z3Init(self,initList): # init Z3 variables
        Z3init = list()
        initList += ["CONST_OWN", "CONST_HOLD", "CONST_ANY", "CONST_NONE"]
        for i in initList:
            if "Function" in i:
                Z3init.append(i)
                continue
            Z3init.append(f"{i} = Int('{i}')")
        if getBoolCounter() > 0:
            for i in range(0,getBoolCounter()):
                Z3init.append(f"b_{i} = Bool('b_{i}')")
        return Z3init

