from functions import getBoolCounter
from ifstmt import *
from loop import *
class z3Gen:
    timer = 0
    boolCount = 0
    def __init__(self,cmdList):
        self.cmdList = cmdList
        self.gen()
    
    def gen(self):
        print("Z3py files generated:")
        for cmd in self.cmdList:
            if isinstance(cmd, ifstmt) or isinstance(cmd, Loop):
                cmd.z3Gen()
                continue
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

           
    ## TODO : A FUNCTION THAT ADDES CONSTS TO THE INIT LIST BEFORE CALLING Z3INIT
    
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
 
