import re
# Cervantes Candia Saúl - 177927
# Cuenca Esquivel Ana Karen - 177932
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    END = '\033[0m'

contRes = contVar = contVal = contOp = contDel = contSig = 0

reservadas = ['int','float','char','string','bool','include','iostream','using','namespace','std',
              'main','if','else','for','while','do','switch','case','cin','cout','endl','return',
              'printf','scanf']
valores = ['true','false']
operadores = ['+','-','*','/','++','--','#','<','>','<<','>>','=','==','!=']
delimitadores = [';',',','.']
signos = ['{','}','(',')']

with open('martes.cpp', 'r') as archivo:
    contenido = archivo.read()
    tokens = re.findall(r'"[^"]*"|\'[^\']*\'|<<|>>|\+\+|--|==|\w+|[^\w\s]', contenido, re.UNICODE)

    for token in tokens:
        if token in reservadas:
            contRes += 1
            print(f"{Colors.RED}{token}{Colors.END}", end=" ")
        elif token in valores or re.fullmatch(r'"[^"]*"|\'[^\']*\'|[-+]?\d*\.\d+|[-+]?\d+', token):# strings, boolean, numericos
            contVal += 1
            print(f"{Colors.GREEN}{token}{Colors.END}", end=" ")
        elif token in operadores:
            contOp += 1
            print(f"{Colors.YELLOW}{token}{Colors.END}", end=" ")
        elif token in delimitadores:
            contDel += 1
            print(f"{Colors.MAGENTA}{token}{Colors.END}", end=" ")
        elif token in signos:
            contSig += 1
            print(f"{Colors.CYAN}{token}{Colors.END}", end=" ")
        else:
            contVar += 1
            print(f"{Colors.BLUE}{token}{Colors.END}", end=" ") # Todo lo que no entra arriba lo asumimos como variable (opcional)

print("\n\n=== RESUMEN ===")
print(f"Palabras reservadas: {Colors.RED}{contRes}{Colors.END}")
print(f"Variables: {Colors.BLUE}{contVar}{Colors.END}")
print(f"Valores: {Colors.GREEN}{contVal}{Colors.END}")
print(f"Operadores: {Colors.YELLOW}{contOp}{Colors.END}")
print(f"Delimitadores: {Colors.MAGENTA}{contDel}{Colors.END}")
print(f"Signos/Llaves: {Colors.CYAN}{contSig}{Colors.END}")
print(f"\nTotal de tokens: {len(tokens)}")
