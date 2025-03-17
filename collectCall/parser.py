from ply import yacc
from scanner import *
from basicBlocks import *
from functions import *
from barrier import *
import re
from rcollect import *
from acollect import *
from move import *
from z3Gen import *
from loop import *
from ifstmt import *
from assertExpr import *
from Copystmt import *
### dict/hashMap
paramMap = {}
tensorMap = {}
commMap = {}
pexprMap = {}
cmds = []

def p_program(p):
    ''' program : cmds '''

def p_cmds(p):
    ''' cmds : cmd
             | cmd cmds
    '''

def p_cmd(p):
    ''' cmd : dcmd
            | wcmd
    '''

#def p_dcmds(p):
 #   ''' dcmds : dcmd
  #             | dcmd dcmds'''

#def p_wcmds(p):
 #   ''' wcmds : wcmd
  # | wcmd wcmds'''


def p_dcmd(p):
    ''' dcmd : param SEMICOLON
              | tensor SEMICOLON
              | grid SEMICOLON
              | part SEMICOLON
              | place SEMICOLON
              | comm SEMICOLON'''
def p_wcmd(p):
    ''' wcmd : rcollect SEMICOLON
              | move SEMICOLON
              | loop 
              | ifstmt 
              | assert SEMICOLON
              | copy SEMICOLON
              | acollect SEMICOLON''' 
    
    cmds.append(p[1])

def p_ifstmt(p):
    ''' ifstmt : IF ifcond ifbody ENDIF'''
    p[0] = ifstmt(p.lineno(1) , p[2], p[3])

def p_ifbody(p):
    '''ifbody : iffuncs
                | iffuncs ifbody'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[2]

def p_ifFunctions(p):
    ''' iffuncs : rcollect SEMICOLON
                  | move SEMICOLON
                  | assert SEMICOLON
                  | copy SEMICOLON
                  | barrier SEMICOLON'''
    p[0] = p[1]

def p_ifcond(p):
    ''' ifcond : booloperation ifcond
                | booloperation 
                | equality_cond'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = p[1] + p[2]
def p_equality_cond(p):
    ''' equality_cond : ID EQUALS phiexpr'''
    
    p[0] = equals(commMap.get(p[1]), p[3]) 
def p_loop(p):
    '''loop : LOOP ID IN LPAREN  operation COLON operation RPAREN loopbody ENDLOOP'''
    p[0] = Loop(p.lineno(1), p[2], p[5] , p[7], p[9], paramMap) 


def p_loopbody(p):
    '''loopbody : loopfuncs
                | loopfuncs loopbody'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[2]

def p_loopFunctions(p):
    ''' loopfuncs : rcollect SEMICOLON
              | move SEMICOLON
              | assert SEMICOLON
              | copy SEMICOLON
              | ifstmt'''
    p[0] = p[1]

def p_barrier(p):
    ''' barrier : BARRIER gexpr
                | BARRIER ID'''
    if isinstance(p[2] , list):
       gexpr1 = Grid(f"comm_{p.lineno(1)}", p[2],paramMap,commMap)
       p[0] = barrier(p.lineno(1) , gexpr1)
    else:
        p[0] = barrier(p.lineno(1) , commMap.get(p[2]))


def p_assert(p):
    ''' assert : ASSERT pexpr AT gexpr
                |  ASSERT pexpr AT  ID
                | ASSERT gexpr IN gexpr
                | ASSERT gexpr IN ID'''
    if p[3] == 'At':
        gexpr = ''
        if isinstance(p[4], list):
            gexpr = Grid(p.lineno(1),p[4] ,paramMap,commMap)
            commMap[gexpr.gName] = gexpr
        else:
            gexpr = commMap.get(p[4])
        p[0] = Assert(p.lineno(1), p[2] , gexpr, 1)

    else:
       gexpr1 = Grid("L" + str(p.lineno(1)) ,p[2] ,paramMap,commMap)
       gexpr2 = ''
       print(p[4], commMap)
       if  not isinstance(p[4], list) and p[4] in commMap:
           gexpr2 = commMap.get(p[4])
       else:
           gexpr2 = Grid("R" + str(p.lineno(1)) ,p[4] ,paramMap,commMap)
       p[0] = Assert(p.lineno(1), gexpr1 , gexpr2, 0)



def p_move(p):
    ''' move : MOVE pexpr AT G_GRID LBRAC wdims RBRAC TO pexpr AT G_GRID LBRAC wdims RBRAC'''
    gexpr1 = Grid(f"SEND{p.lineno(1)}", p[6],paramMap,commMap)
    gexpr2 = Grid(f"RECV{p.lineno(1)}", p[13],paramMap,commMap)
    commMap[gexpr1.gName] = gexpr1
    commMap[gexpr2.gName] = gexpr2
    p[0] = move(p.lineno(1), p[2], gexpr1, p[9], gexpr2)

def p_copy(p):
    ''' copy : COPY pexpr AT G_GRID LBRAC wdims RBRAC TO pexpr AT G_GRID LBRAC wdims RBRAC'''
    gexpr1 = Grid(f"SEND{p.lineno(1)}", p[6],paramMap,commMap)
    gexpr2 = Grid(f"RECV{p.lineno(1)}", p[13],paramMap,commMap)
    commMap[gexpr1.gName] = gexpr1
    commMap[gexpr2.gName] = gexpr2
    p[0] = Copy(p.lineno(1), p[2], gexpr1, p[9], gexpr2)

def p_rcollect(p):
    ''' rcollect : RCOLLECTID pexpr TO pexpr AT G_GRID LBRAC wdims RBRAC
                | RCOLLECTID pexpr TO pexpr AT G_GRID LBRAC wdims RBRAC USING ID'''
    gexpr = Grid(p.lineno(1), p[8],paramMap,commMap)
    commMap[gexpr.gName] = gexpr 
    p[0] = rcollect(p.lineno(1),p[1] , p[2] , p[4], gexpr)
    if len(p) > 10:
        p[0].setCommunicator(commMap.get(p[11]))

def p_acollect(p):
    ''' acollect : ACOLLECTID pexpr TO pexpr USING gexpr 
                  | ACOLLECTID pexpr TO pexpr USING ID'''
    gexpr = ''
    if isinstance(p[6], list):
        gexpr = Grid(p.lineno(1), p[6],paramMap,commMap)
        commMap[gexpr.gName] = gexpr 
    else: 
        gexpr = commMap.get(p[6])

    p[0] = acollect(p.lineno(1),p[1] , p[2] , p[4], gexpr)

def p_place(p):
    ''' place : PLACE pexpr AT G_GRID LBRAC wdims RBRAC'''
    gexpr = Grid(p.lineno(1), p[6],paramMap,commMap)
    commMap[gexpr.gName] = gexpr
    p[0] = Place(p[2] , gexpr)

def p_part(p):
    ''' part : PARTITION pexpr WITH pList'''
    p[0] = Part(p[2] , p[4])#, tensorMap.get(p[2].getTensorName()))

def p_pexpr(p): # pi(ID)[sth ,sth]
    ''' pexpr : PI LPAREN ID RPAREN LBRAC wdims RBRAC'''
    p[0] = pexpr(tensorMap.get(p[3]), p[6],paramMap)
    if p[3] in pexprMap:
        pexprMap[p[3]].append(p[0])
    else:
        pexprMap[p[3]] = [p[0]]

def p_pList(p): ## p, p+1 , 5 
    ''' pList : operation 
               | operation COMMA pList'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]
def p_wdims(p):
    ''' wdims : operation
                | WILDCARD
                | operation COMMA wdims 
                | WILDCARD COMMA wdims'''
    
    p[0] = []
    for i in range(1,len(p)):
        if isinstance(p[i],list):
            p[0] += p[i]
        else:
            if p[i] != ',':
                p[0].append(p[i])

def p_grid(p):
    ''' grid : GRID gexpr'''
    p[0] = Grid(p.lineno(0), p[2],paramMap,commMap)
    commMap[p[0].gName] = p[0]
def p_gexpr(p):
    ''' gexpr : G_GRID LBRAC wdims RBRAC'''
    p[0] = p[3]  
def p_phi(p):
    ''' phiexpr : PHI LPAREN gexpr COMMA TYPE COMMA LBRAC ndims RBRAC RPAREN'''
    p[0] = phi(p.lineno(1), p[3] , p[5],p[8], paramMap, commMap)
    #commMap[p[0].gName] = p[0]
def p_communicator(p):
    ''' comm : COMMUNICATOR ID EQUAL phiexpr
               | COMMUNICATOR ID EQUAL gexpr'''

    if isinstance(p[4], list):
        commMap[p[2]] =  Grid(p.lineno(1), p[4] ,paramMap,commMap) 
    else:
        commMap[p[2]] = p[4]
def p_ndims(p):
    ''' ndims : NUMBER
                | NUMBER COMMA ndims'''
    p[0] = []
    for i in range(1,len(p)):
        if isinstance(p[i],list):
            p[0] += int(p[i])
        else:
            if p[i] != ',':
                p[0].append(int(p[i]))
   

def p_tensor(p): #declare tensor
    ''' tensor : TENSOR ID LBRAC dims RBRAC'''
    p[0] = Tensor(p[2], p[4],paramMap)
    tensorMap[p[2]] = p[0]

def p_dims(p): ## dimensions definition without wild cards [x,y,1,z,9]
    ''' dims : operation 
              | operation COMMA dims'''
    p[0] = []
    for i in range(1,len(p)):
        if isinstance(p[i],list):
            p[0] += p[i]
        else:
            if p[i] != ',':
                p[0].append(p[i])

def p_parameter(p): #declare parameter
    ''' param :  PARAMETER paramExpr''' 
    name = re.split((r'[><]=?|[!=]='),p[2][0])[0]
    p[0] = Parameter(name, p[2], paramMap) ## first of string the name
    paramMap[name] = p[0]

def p_paramExpr(p): ## logical expression mainly for parameters
    ''' paramExpr : operation LOGIC operation
                    | operation LOGIC operation COMMA paramExpr'''
    if len(p) == 4:
        p[0] = [p[1] + p[2] + p[3]]
    else:
        p[0] = [p[1] + p[2] + p[3]] + p[5] 
    """
    p[0] = []
    for i in range(1,len(p)):
        if isinstance(p[i],list):
            p[0] += p[i]
        else:
            p[0].append(p[i])
    """
def p_booloperation(p):
    ''' booloperation : operation LOGIC operation 
                        | operation EQUAL operation'''
    p[0] =  p[1] + p[2] + p[3]

def p_operation(p): # variable or equation
    ''' operation : varConst MATHOP operation
                    | varConst '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = p[1] + p[2] + p[3]
def p_variableOrconst(p): ## constant(number) or variable
    ''' varConst : NUMBER
                   | ID '''
    p[0] = p[1] 
def p_error(p):
    print("ERROR : ")
    if p:
        print(f"Syntax error at line number {p.lineno} at token={p.type} and value={p.value}")

    sys.exit(1)


parser = yacc.yacc()
if len(sys.argv) < 2:
    print("Input format: Source File")
    exit(1)

inputFile = sys.argv[1]
data = input_code()
lexer.input(data)
result = parser.parse(data, lexer=lexer)#,debug = True)

z3Obj = z3Gen(cmds)
def input_code():
    f = open(inputFile,"r")
    return f


