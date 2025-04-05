import re

contRes, contVar, contVal, contDel, contSig, contOp = 0, 0, 0, 0, 0, 0

reservadas = ['int','float','char','string','bool','include','iostream','using','namespace','std',
              'main','if','else','for','while','do','switch','case','cin','cout','endl','return',
              'printf','scanf']
valores = ['true','false']
operadores = ['+','-','*','/','++','--','#','<','>','<<','>>','=','==','!=']
delimitadores = [';',',','.']
signos = ['{','}','(',')']

with open('pruebaPython.cpp', 'r') as archivo:
    contenido = archivo.read()
    palabras = contenido.split()

    tokens = re.findall(r'"[^"]*"|\'[^\']*\'|<<|>>|\+\+|--|==|\w+|[^\w\s]', contenido, re.UNICODE)

    for llave in tokens:
        if llave in reservadas:
            contRes += 1
        elif llave in signos:
            contSig += 1
        elif llave in operadores:
            contOp += 1
        elif llave in delimitadores:
            contDel += 1
        elif re.fullmatch(r'"[^"]*"|\'[^\']*\'', llave):  # strings
            contVal += 1
        elif llave in valores:  # booleanos
            contVal += 1
        elif re.fullmatch(r'[-+]?\d*\.\d+|[-+]?\d+', llave):  # numéricos
            contVal += 1
        else:
            contVar += 1  # Todo lo que no entra arriba lo asumimos como variable (opcional)
    
    print(f'Total de palabras reservadas: {contRes}')
    print(f'Total de variables: {contVar}')
    print(f'Total de valores: {contVal}')
    print(f'Total de operadores: {contOp}')
    print(f'Total de delimitadores: {contDel}')
    print(f'Total de parentesis/llaves: {contSig}')
    print(tokens)