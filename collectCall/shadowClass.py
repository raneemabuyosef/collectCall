from functions import *
from islFunctions import *
class shadow:
    def __init__(self, lineno, send_expr, send_gexpr, Map1, Map2):
        self.filename = f'{lineno:03d}move.py'
        self.send_expr = send_expr
        self.send_gexpr = send_gexpr
        self.sendmap , self.sendref = Map1, Map2
        self.functionID = 1
        self.timer = 0
    def sendMap(self, key = 0):
        if key == 0:
            return self.sendmap
        elif key == 1:    
            return self.sendref
        else:
            return self.sendmap, self.sendref
    
    def get_expr(self):
        return self.send_expr
    def get_gexpr(self):
        return self.send_gexpr
    def recvGrid(self):
        return self.send_gexpr

    def z3(self):
        constraints = islConstraints_map(self.sendmap, self.send_expr.paramMap)
        init = islInit_map(self.sendmap)
        return init, constraints
    def getState(self):
        return "CONST_NONE"



    def sendMap(self, key = 0):
        if key == 0:
            return self.sendmap
        elif key == 1:
            return self.sendref
        else:
            return self.sendmap, self.sendref

 
    def recvMap(self, key = 0):
        if key == 0:
            return self.sendmap
        elif key == 1:
            return self.sendref
        else:
            return self.sendmap, self.sendref

