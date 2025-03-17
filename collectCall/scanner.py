import ply.lex as lex
import sys 

reserved = { 
        'Parameter' : 'PARAMETER',
        'Tensor' : 'TENSOR',
        'G' : 'G_GRID',
        'Grid' : 'GRID',
        'pi' : 'PI',
        'Place' : 'PLACE',
        'At' : 'AT',
        'With' : 'WITH',
        'Partition' : 'PARTITION',
  #      'Bcast' : 'BCAST',
        'To' : 'TO',
        'Phi' : 'PHI',
        'Communicator' : 'COMMUNICATOR',
        'Move' : 'MOVE',
        'Loop': 'LOOP',
        'in' : 'IN',
        'endloop': 'ENDLOOP',
        'If' : 'IF', 
        'endif' : 'ENDIF',
        'Assert' : 'ASSERT',
        'At' : 'AT',
        'Copy': 'COPY',
        'Using' : 'USING',
        'Barrier' : 'BARRIER',
        'equals' : 'EQUALS',
        }

tokens =  list(reserved.values()) + [
    'ACOLLECTID',
    'RCOLLECTID',
    'ID',
    'LPAREN',
    'RPAREN',
    'COMMA',
    'SEMICOLON',
    'COMMENT',
    'NUMBER',
    'TYPE',
    'MATHOP',
    'EQUAL',
    'LBRAC',
    'RBRAC',
    'CLBRAC',
    'CRBRAC',
    'COLON',
    'TABE',
    'TWODOT',
    'DOT',
    'HASH',
    'QUOTE',
    #'BOOL',
    'LOGIC',
    'LAND',
    'WILDCARD',

]# + list(reserved.values())


def t_ACOLLECTID(t):
    r'\b(?:All-gather|All-to-all|All-reduce)\b'
    return t

def t_RCOLLECTID(t):
    r'\b(?:Gather|Bcast|Reduce|Scatter)\b'
    return t

def t_LAND(t):
    r'&&'
    return t

def t_LOGIC(t):
    r'[><]=?|[!=]='
    return t

def t_BOOL(t):
    r'true|false'
    #print(t)
    return t

def t_COMMENT(t):
    r'(//.*)'
    pass
def t_WILDCARD(t):
    r'\*|\.'
    return t

def t_MATHOP(t):
    r'%|/|\+|\-|\* '
    return t

def t_TYPE(t):
    r'\b(?:Even|Odd|Wrap|Next)\b'
    return t


def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, 'ID')
    return t
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    
def t_error(t):
    print(f"Illegal character '{t.value[0]}'")
    t.lexer.skip(1)

t_DOT = r'\.'
t_HASH = '\#'
t_CLBRAC = r'\{'
t_CRBRAC = r'\}'
t_COMMA = r'(,)'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_SEMICOLON = r';'
t_NUMBER = r'\d+'
t_ignore = ' \t'
t_EQUAL = r'\='
t_LBRAC = r'\['
t_RBRAC = r'\]'
t_COLON = r'\:'
#t_TABE = r'\t'
t_QUOTE = r'\"'


lexer = lex.lex()
inputFile = sys.argv[1] 
def input_code():
    f = open(inputFile,'r')
    return f.read()

"""
code = input_code()
lexer.input(code)


while True:
    tok = lexer.token()
    if not tok:
        break
    print(tok)

"""
