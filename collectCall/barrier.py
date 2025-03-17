from functions import *
from islFunctions import *
class barrier:
    def __init__(self,lineno, comm):
        self.lineno = lineno
        self.filename  = f'{lineno:03d}barrier.py'
        self.comm = comm
        self.map = ''
        self.ifcond = ''
    def ifChange(self, cond):
        self.ifcond = cond
        return 0

    def z3Gen(self):

        if self.ifcond == '':
            return

        
        cond = self.ifcond.z3()

        init = cond[0]
        constraints = cond[1]
        
        init += islInit_set(self.comm.getISL())
        constraints += islConstraints_set(self.comm.getISL())

        init.append(f"{self.comm.gName}_card")
        init.append(f"{self.ifcond.leftside.gName}_card")

        constraints.append(f"{self.comm.gName}_card == {commsize(self.comm.getISL().to_str())}")

        constraints.append(f"{self.ifcond.leftside.gName}_card == {commsize(self.ifcond.leftside.getISL().to_str())}")
        


        constraints.append(f"{self.comm.gName}_card ==  {self.ifcond.leftside.gName}_card")
        
        constraints += self.equal_dims()

        return init,constraints

    def equal_dims(self):
        const = []

        bset1 = self.comm.getISL().get_basic_sets()
        bset2 = self.ifcond.leftside.getISL().get_basic_sets()
        space = isl.Space.create_from_names(isl.DEFAULT_CONTEXT, set=[])

        print(self.comm.getISL().get_space())
        for i in range(len(self.comm.dims)):
            tmp1 = self.comm.getISL().get_dim_name(isl.dim_type.set,i)
            tmp2 = self.ifcond.leftside.getISL().get_dim_name(isl.dim_type.set,i)

            b1 = isl.BasicSet.universe(self.comm.getISL().get_space())
            b2 = isl.BasicSet.universe(self.ifcond.leftside.getISL().get_space())
            dim_constraints = []
            
            for b in bset1:
                for constraint in b.get_constraints():
                    if constraint.involves_dims(isl.dim_type.set, i , 1):
                        b1 = b1.add_constraint(constraint)
            
            for b in bset2:
                for constraint in b.get_constraints():
                    if constraint.involves_dims(isl.dim_type.set, i, 1):
                        b2 = b2.add_constraint(constraint)
        
        
            for b in bset1:
                for constraint in b.get_constraints():
                    for ii in range(self.comm.getISL().n_param()):
                        if constraint.involves_dims(isl.dim_type.param, ii , 1):
                            b1 = b1.add_constraint(constraint)
            for b in bset2:
                for constraint in b.get_constraints():
                    for ii in range(self.comm.getISL().n_param()):
                        if constraint.involves_dims(isl.dim_type.param, ii , 1):
                            b1 = b1.add_constraint(constraint)
            
            dim_constraints += islConstraints_set(b1) + islConstraints_set(b2)
            const += self.get_equality(dim_constraints, tmp1 , tmp2)



        return const

    def get_equality(self, const, t0, t1):
        constraints = []
        
        boolCounter = useBoolCounter()
        constraints.append(f"Implies(b_{boolCounter}, And({','.join(const)}, {t0} == {t1}))")
        constraints.append(f"ForAll([{t0},{t1}], b_{boolCounter})")
        
        return constraints

