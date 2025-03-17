from functions import getBoolCounter

class ifstmt:
    def __init__(self,lineno, cond, body):
        self.filename =  f'{lineno:03d}if.py' 
        self.cond = cond
        self.body = body
        self.ifbody()
    def ifbody(self):
        for i in self.body:
            i.ifChange(self.cond)
    

    def z3Gen(self):

        self.gen()

    def gen(self):
        for cmd in self.body:
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
            if "equal" in i:
                Z3init.append(f"{i} = Bool('{i}')")
                continue
            Z3init.append(f"{i} = Int('{i}')")

        
        if getBoolCounter() > 0:
            for i in range(0,getBoolCounter()):
                Z3init.append(f"b_{i} = Bool('b_{i}')")
        return Z3init

