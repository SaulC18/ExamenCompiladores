import sys #interaccion con el sistema
import re #expresiones regulares

#interfaz grafica es otra alternativa a por ejemplo tkinter que es mas conocido pero a la vez mas simple
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, 
                             QHBoxLayout, QPushButton, QFileDialog, QMessageBox, QTextEdit)
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import Qt
from PyQt5.Qsci import QsciScintilla, QsciLexerCPP

variables = {} #diccionario para guardar las variables y su tipo, ver si ya estan declaradas y verr que valor se les podria asignar

errores = [] #para ir almacenando los errores y despues ponerlos en la parte de resultados al final

#para validaciones de datos, declaraciones etc
tipos_validos = r"(?:void|bool|char|wchar_t|char8_t|char16_t|char32_t|short|int|long|float|double|size_t|ptrdiff_t|auto|string)"

#validaciones
def validar_librerias(lineas):
    errores = []
    # Librerías válidas (puedes agregar más)
    librerias_validas = {
        # C++ Standard Libraries
        "iostream", "vector", "string", "map", "set", "algorithm",
        "fstream", "sstream", "iomanip", "limits", "queue", "stack",
        "list", "deque", "bitset", "array", "unordered_map", "unordered_set",
        # C Standard Libraries
        "stdio.h", "stdlib.h", "math.h", "time.h", "ctype.h", "string.h",
        "stdbool.h", "stdint.h", "errno.h", "locale.h",
        # C++11 and later
        "thread", "mutex", "future", "atomic", "condition_variable",
    }
    
    include_pattern = re.compile(r'#include\s*[<"](\w+(\.\w+)*)[>"]')
    
    seccion_includes = True
    
    for i, linea in enumerate(lineas, 1):
        linea_strip = linea.strip()
        
        # Ignorar líneas vacías o comentarios
        if not linea_strip or linea_strip.startswith("//"):
            continue
        
        if seccion_includes:
            if linea_strip.startswith("#include"):
                match = include_pattern.fullmatch(linea_strip)
                if not match:
                    errores.append(f"Error: Línea {i}, sintaxis incorrecta en la inclusión: {linea_strip}")
                else:
                    libreria = match.group(1)
                    if libreria not in librerias_validas:
                        errores.append(f"Error: Línea {i}, librería '{libreria}' no es válida.")
            else:
                seccion_includes = False
        else:
            if linea_strip.startswith("#include"):
                errores.append(f"Error: Línea {i}, include fuera de la sección inicial.")
    
    return errores

def validar_declaraciones(lineas):
    errores_decl = []

    #expresión regular general para declaraciones con asignación
    validacion = re.compile(
        r'^\s*' #espacios opcionales al inicio
        r'(' + tipos_validos + r')\s+' #tipo de dato válido
        r'([a-zA-Z_]\w*)\s*=\s*' #nombre de variable
        r'(.*?)' #valor asignado
        r'\s*;\s*$', #checamos que tenga punto y coma al final
        re.IGNORECASE
    )

    #expresión regular para asignaciones sin tipo (ya declaradas)
    asignacion = re.compile(
        r'^\s*([a-zA-Z_]\w*)\s*=\s*(.*?)\s*;\s*$',
        re.IGNORECASE
    )

    tipos_valores = { #para checar que el tipo del valor coincida con el tipo de la variable
        "int": r'^-?\d+$',
        "short": r'^-?\d+$',
        "long": r'^-?\d+$',
        "float": r'^-?\d+\.\d+$',
        "double": r'^-?\d+\.\d+$',
        "char": r"^'.{1}'$",
        "string": r'^".*"$',
        "bool": r'^(true|false)$',
    }

    for i, linea in enumerate(lineas, 1):
        linea_strip = linea.strip()
        if not linea_strip or linea_strip.startswith("//"):
            continue #ignorar líneas vacías o comentarios

        if any(linea_strip.startswith(estructura) for estructura in ["for", "if", "while", "switch"]):
            continue #ignorar si es un for o un if o un switch ya que esos se checan en otra parte y porque saca error

        if '=' in linea_strip: #si hay una declaracion en la linea
            match = validacion.match(linea_strip)
            if match:
                tipo, nom_var, valor = match.groups() #se separa el match
                tipo_valor = tipos_valores.get(tipo) #se hbusca que coincida con el diccionario

                if nom_var in variables:
                    errores_decl.append(f"Error: La variable '{nom_var}' ya fue declarada. Línea: {i}.")
                    continue

                if tipo_valor and not re.fullmatch(tipo_valor, valor.strip()):
                    errores_decl.append(f"Error: El valor '{valor.strip()}' no es válido para el tipo '{tipo}' en la línea: {i}.")
                else:
                    variables[nom_var] = {"tipo": tipo, "valor": valor} #guardar variable si todo está bien

            #puede que ya este declarada asi que se checa con la expresion para asignaciones ya declaradas
            else:
                match_asig = asignacion.match(linea_strip)
                if match_asig:
                    nom_var, valor = match_asig.groups()
                    valor = valor.strip()

                    if nom_var not in variables:
                        errores_decl.append(f"Error: La variable '{nom_var}' no ha sido declarada. Línea: {i}.")
                        continue

                    tipo = variables[nom_var]["tipo"]
                    tipo_valor = tipos_valores.get(tipo)

                    if tipo_valor and not re.fullmatch(tipo_valor, valor):
                        errores_decl.append(f"Error: El valor '{valor}' no es válido para el tipo '{tipo}' en la línea: {i}.")
                    else:
                        variables[nom_var]["valor"] = valor #actualizar valor si es válido
                else:
                    errores_decl.append(f"Error: Declaración/asignación inválida en la línea: {i}.")

    return errores_decl

def validar_for(lineas): #fors aceptables
    errores_for = [] #se van guardando los errores por si hay varios

    validacion = re.compile(
        r'for\s*\(\s*' #for(
        r'(?:(' + tipos_validos + r')\s+)?' #tipo opcional
        r'([a-zA-Z_]\w*)\s*=\s*([^;]*?)\s*;\s*' #var = valor
        r'([^;]*?)\s*;\s*' #condición
        r'([^)]*?)\s*\)\s*\{', #incremento
        re.IGNORECASE
    )

    tipos_valores = { #para checar que el tipo del valor coincida con el tipo de la variable
        "int": r'^-?\d+$',
        "short": r'^-?\d+$',
        "long": r'^-?\d+$',
        "float": r'^-?\d+\.\d+$',
        "double": r'^-?\d+\.\d+$',
        "char": r"^'.{1}'$",
        "string": r'^".*"$',
        "bool": r'^(true|false)$',
    }

    for i, linea in enumerate(lineas, 1): #se recorre linea por linea comenzando en el 1
        linea_strip = linea.strip()
        if linea_strip.startswith("for"): #solo analiza si comienza con for
            m = validacion.match(linea_strip)
            if not m:
                errores_for.append(f"Error: La expresión for es incorrecta en la línea: {i}.")
                continue

            type, var, val, cond, incre = m.groups() #se separa el match

            if type: #es declaración
                if var in variables:
                    errores_for.append(f"Error: La variable '{var}' ya fue declarada. Línea :{i}.")
                elif not re.fullmatch(tipos_valores.get(type, r'.*'), val.strip()):
                    errores_for.append(f"Error: El valor '{val.strip()}' no es válido para '{type}' (línea {i}).")
                else:
                    variables[var] = {"tipo": type, "valor": val}
            else: #si en si no hay un tipo entonces significa que usamos una variable ya declarada y estamos haciendo una asignacion
                if var not in variables:
                    errores_for.append(f"Error: La variable '{var}' no ha sido declarada (línea {i}).")
                else:
                    tipo_var = variables[var]["tipo"]
                    if not re.fullmatch(tipos_valores.get(tipo_var, r'.*'), val.strip()):
                        errores_for.append(f"Error: Tipo incompatible en asignación a '{var}' (línea {i}).")
                    else:
                        variables[var]["valor"] = val

            def checar_uso(expr):#se checa la parte del incremento
                for token in re.findall(r'\b[a-zA-Z_]\w*\b', expr):
                    if token not in variables and token not in ["true","false"]:
                        errores_for.append(f"Error: La variable '{token}' no ha sido declarada. Línea: {i}.")
            checar_uso(cond) #se checa si en la parte de condicion del for se uso una variable no valida
            checar_uso(incre) #se checa lo mismo pero con la parte del incremento


    return errores_for

def validar_if(lineas):#para validar los if
    errores_if = []

    validacion = re.compile(
        r'if\s*\(\s*('
        r'[a-zA-Z_]\w*'  # una sola variable también es válida
        r'(\s*(==|!=|<=|>=|<|>)\s*[^(){};]+)?'  # posible comparación
        r'(\s*(\&\&|\|\|)\s*[a-zA-Z_]\w*(\s*(==|!=|<=|>=|<|>)\s*[^(){};]+)?)?'  # combinación lógica
        r')\s*\)\s*\{',
        re.IGNORECASE
    )

    for i, linea in enumerate(lineas, 1):
        linea_strip = linea.strip()
        if linea_strip.startswith("if"): #debe comenzar con if la linea
            m = validacion.match(linea_strip)
            if not m:
                errores_if.append(f"Error: La expresión if es incorrecta en la línea: {i}.")
                continue
            condicion = m.group(1)
            for token in re.findall(r'\b[a-zA-Z_]\w*\b', condicion):
                if token not in variables and token not in ["true","false"]:
                    errores_if.append(f"Error: La variable '{token}' no está declaradaaa, línea :{i}.")
    return errores_if

def validar_while(lineas): #para validar los while
    errores_while = []

    validacion = re.compile(
        r'while\s*\(\s*(.+?)\s*\)\s*\{',
        re.IGNORECASE
    )

    for i, linea in enumerate(lineas, 1):
        linea_strip = linea.strip()
        if linea_strip.startswith("while"): #debe comenzar con while la linea
            m = validacion.match(linea_strip)
            if not m:
                errores_while.append(f"Error: La expresión while es incorrecta en la línea: {i}.")
                continue
            condicion = m.group(1)
            for token in re.findall(r'\b[a-zA-Z_]\w*\b', condicion):
                if token not in variables and token not in ["true","false"]:
                    errores_while.append(f"Error: La variable '{token}' no está declarada, línea: {i}.")
    return errores_while
    

def variable_valida(nombre, ln_err): #variable aceptable, se le manda la variable o lo que se pueda considerar como una y la linea donde se encuentra 
    #expresión regular para nombres de variables válidos
    validacion = re.compile(r'^[a-zA-Z_]\w*$') #puede comenzar con letras o guin bajo y lo demas puede ser letras, guion bajo o nuemros
    
    #coincide la variable con la validacion?
    if nombre and nombre.strip() and not validacion.match(nombre):
        errores.append(f"Error: La variable '{nombre}' es inválida en la linea: {ln_err}.")

def validar_cadenas(lineas):#para checar que una cadena se cierre
    errores = [] #se van guardando los errores por si hay varios
    en_string = False #para saber si esta dentro de un string
    comilla_abierta = '' #guardar la comillla que se abrio " o '
    linea_inicio = 0 #en que linea se abrio la cadena

    for i, linea in enumerate(lineas, 1): #se recorre linea por linea comenzando en el 1
        j = 0 #para recorrer caracter por caracter
        while j < len(linea):
            char = linea[j] #se consigue el caracter

            if not en_string: #si aun no estamos en un string se checa si se abrio uno
                if char in ('"', "'"): #se checa si comenzo con " o '
                    comilla_abierta = char #se guarda el " o '
                    en_string = True #ahora estamos dentro de un string por lo que ya no entarra a este if si no al else
                    linea_inicio = i #se guarda la linea
            else:
                if char == comilla_abierta: #se checa que se este cerrando con un caracter igual
                    if j == 0 or linea[j - 1] != '\\': #se checa que la comilla no este escapada para poder contarla como la finalizacion del strimng
                        en_string = False #ya no esta en un string
                        comilla_abierta = '' #se inicializa
            j += 1 #cambia de caracter

        #si no se ha cerrado el string
        if en_string and not linea.rstrip().endswith('\\'): #si no se cerro la cadna checamos que no sea un string multilinea y eso se checa viendo si al final de la linea tenemos un slash invertido
            errores.append(f"Error: Cadena no cerro, inicia en: {linea_inicio}") #si hay un error se añade a la lista de errores misma que se retronara al final
            #eliminamos la linea para que no nos muestre mas errores sobre esa misma linea si ya sabemos que no se cerro el string no necesitamos saber si por ejemplo no esta cerrado con ;
            lineas[linea_inicio-1] = "" #reemplazamos la línea completa por vacio
            en_string = False #ya no esta en un string

    return errores, lineas #se retorna lista de errores

def validar_main(lineas):
    errores_main = []   #Lista para almacenar errores encontrados en la declaración de main
    conteo_main_validos = 0  # Contador de declaraciones válidas de main

    validacion_main = re.compile(
        r'^\s*(int|void)\s+main\s*\(\s*(int\s+\w+\s*,\s*char\s*\*\s*\w+\[\])?\s*\)\s*\{?\s*$'
    )

    for i, linea in enumerate(lineas, 1):
        if 'main' in linea:
            if validacion_main.match(linea.strip()):
                conteo_main_validos += 1
                if conteo_main_validos > 1:
                    errores_main.append(f"Error: Declaración duplicada de la función 'main' en la línea {i}.")
            else:
                errores_main.append(f"Error: Declaración inválida de la función 'main' en la línea {i}.")

    # Si no se encontró ninguna declaración válida
    if conteo_main_validos == 0:
        errores_main.append("Error: No se encontró una función 'main' válida.")

    return errores_main

def validar_printf(lineas):
    errores_printf = []
    # printf correctamente escrito con paréntesis y punto y coma
    validacion_printf = re.compile(
        r'^\s*printf\s*\(\s*"[^"]*"(?:\s*,\s*[^)]*)?\s*\)\s*;\s*$'
    )

    for i, linea in enumerate(lineas, 1):
        linea_strip = linea.strip()

        # Detección de errores ortográficos comunes como print, prinf, prntf, pritnf
        if 'print' in linea_strip or 'prinf' in linea_strip or 'prntf' in linea_strip or 'pritnf' in linea_strip or 'ptinf' in linea_strip or 'prinft' in linea_strip:
            if 'printf' not in linea_strip:
                errores_printf.append(f"Error: ¿Quisiste decir 'printf'? Revisión de posible error ortográfico en la línea {i}.")

        # Validación de sintaxis correcta del printf
        if 'printf' in linea_strip:
            if not validacion_printf.match(linea_strip):
                # Revisión específica para ayudar al usuario a saber qué falta
                if not linea_strip.endswith(';'):
                    errores_printf.append(f"Error: Falta ';' al final del printf en la línea {i}.")
                elif ')' not in linea_strip:
                    errores_printf.append(f"Error: Falta paréntesis de cierre ')' en printf en la línea {i}.")
                elif '(' not in linea_strip:
                    errores_printf.append(f"Error: Falta paréntesis de apertura '(' en printf en la línea {i}.")
                elif '"' not in linea_strip:
                    errores_printf.append(f"Error: Falta cadena de texto entre comillas en printf en la línea {i}.")
                else:
                    errores_printf.append(f"Error: Uso inválido de 'printf' en la línea {i}.")

    return errores_printf

#esta clase simplemente crea la inetrfaz y la personaliza
class CodeEditor(QsciScintilla):
    def __init__(self):
        super().__init__()

        #Configuración básica del editor
        self.setUtf8(True)
        self.setAutoIndent(True)
        self.setMarginLineNumbers(1, True)
        self.setMarginWidth(1, "0000")
        self.setStyleSheet("background-color: #282a36; color: #f8f8f2;")

        #Configuración del lexer con colores Dracula
        lexer = QsciLexerCPP()
        font = QFont("Consolas", 11)
        lexer.setDefaultFont(font)

        lexer.setColor(QColor("#ff79c6"), 1) #palabras clave
        lexer.setColor(QColor("#8be9fd"), 2) #tipos
        lexer.setColor(QColor("#f1fa8c"), 3) #strings
        lexer.setColor(QColor("#bd93f9"), 4) #números
        lexer.setColor(QColor("#6272a4"), 5) #comentarios
        lexer.setColor(QColor("#ffb86c"), 10) #operadores
        lexer.setColor(QColor("#f8f8f2"), 11) #identificadores
        lexer.setColor(QColor("#ff5555"), 16) #errores

        lexer.setFont(font) 
        self.setLexer(lexer)

        #Colores para fondo del texto seleccionado y cursor en si no son necesarios pero mejoran la apariencia del "compilador"
        self.SendScintilla(QsciScintilla.SCI_SETCARETFORE, QColor("#f8f8f2"))
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QColor("#44475a"))

class CompiladorVSCode(QMainWindow):
    def __init__(self):
        super().__init__()

        #titulo de la ventana
        self.setWindowTitle("👾 Compilador ")
        self.setGeometry(100, 100, 1000, 800)
        
        self.caracteres_repetidos = [';', ',', '.', '(', ')', '{', '}']
        #contadores para registrar el numero de tokens de cada clase
        self.contRes = self.contVar = self.contVal = self.contOp = self.contDel = self.contSig = 0
        self.reservadas = [
            #C++
            'alignas', 'alignof', 'and', 'and_eq', 'asm', 'auto', 'bitand', 'bitor',
            'bool', 'break', 'case', 'catch', 'char', 'char8_t', 'char16_t', 'char32_t',
            'class', 'compl', 'concept', 'const', 'const_cast', 'consteval', 'constexpr',
            'continue', 'do', 'double', 'dynamic_cast', 'else', 'enum', 'explicit',
            'extern', 'endl', 'float', 'for', 'friend', 'goto', 'if', 'include', 'inline', 'int',
            'long', 'main', 'mutable', 'namespace', 'new', 'noexcept', 'not', 'not_eq', 'nullptr',
            'operator', 'or', 'or_eq', 'private', 'protected', 'public', 'register',
            'reinterpret_cast', 'requires', 'return', 'short', 'signed', 'sizeof',
            'static', 'static_assert', 'static_cast', 'std', 'struct', 'switch', 'template',
            'this', 'thread_local', 'throw', 'try', 'typedef', 'typeid',
            'typename', 'union', 'unsigned', 'using', 'virtual', 'void', 'volatile',
            'wchar_t', 'while', 'xor', 'xor_eq', 'cout', 'cin', 'iostream',

            #C algunas no estan porque ya las pusimos en las de C++
            'stdio', 'stdio.h', 'stdlib', 'stdlib.h', 'string', 'string.h', 'math.h',
            'ctype.h', 'time.h', 'stdbool.h', 'stdint.h', 'assert.h',
            'printf', 'scanf', 'fopen', 'fclose', 'fread', 'fwrite', 'fseek', 'ftell',
            'malloc', 'calloc', 'realloc', 'free', 'exit', 'abort', 'atoi', 'atof', 'atol', 'perror'
        ]
        self.valores = ['true','false']
        #self.operadores = ['+','-','*','/','++','--','#','<','>','<<','>>','=','==','!=']
        self.operadores = [ #lista para que agarre por orden, bueno si consigue uno doble ya no cuenta uno simple y asi
            ">>=", "<<=", "->*", ".*", "++", "--", "==", "!=", "<=", ">=", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "->", "<<", ">>", "&&", "||", "##",
            "+", "-", "*", "/", "%", "=", "<", ">", "!", "&", "|", "^", "~", ".", "?", ":", "#", "[", "]"
        ]
        self.delimitadores = [';',',','.']
        self.signos = ['{','}','(',')']

        self.librerias_metodos = {
            'stdio.h': ['printf', 'scanf', 'fopen', 'fclose', 'fread', 'fwrite', 'fseek', 'ftell', 
                        'fprintf', 'fscanf', 'sprintf', 'sscanf', 'getchar', 'putchar', 'gets', 'puts',
                        'perror', 'remove', 'rename', 'tmpfile', 'tmpnam', 'setvbuf', 'setbuf', 'fflush'],
            'stdlib.h': ['malloc', 'calloc', 'realloc', 'free', 'exit', 'abort', 'atexit', 'system',
                        'atoi', 'atof', 'atol', 'strtol', 'strtoul', 'rand', 'srand', 'qsort', 'bsearch',
                        'abs', 'labs', 'div', 'ldiv'],
            'string.h': ['strcpy', 'strncpy', 'strcat', 'strncat', 'strcmp', 'strncmp', 'strchr',
                        'strrchr', 'strstr', 'strtok', 'strlen', 'strerror', 'memcpy', 'memmove',
                        'memcmp', 'memchr', 'memset'],
            'math.h': ['sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'atan2', 'sinh', 'cosh', 'tanh',
                    'exp', 'log', 'log10', 'pow', 'sqrt', 'ceil', 'floor', 'fabs', 'ldexp', 'frexp',
                    'modf', 'fmod'],
            'iostream': ['cin', 'cout', 'cerr', 'clog', 'endl', 'flush', 'ws', 'hex', 'dec', 'oct'],
            'vector': ['vector', 'push_back', 'pop_back', 'size', 'empty', 'clear', 'begin', 'end'],
            # Puedes agregar más librerías y sus métodos aquí
        }

        self.librerias_incluidas = set()  # Para rastrear qué librerías se han incluido

        #creacion del area donde se pone el codigo ditor de código
        self.editor = CodeEditor()
        
        #Panel de resultados (con scroll y tema oscuro) usando html si te fijas bien usa formato tipo css
        self.resultados = QTextEdit()
        self.resultados.setReadOnly(True)
        self.resultados.setStyleSheet("""
            background-color: #1e1e1e; 
            color: #d4d4d4; 
            font-family: Consolas;
            font-size: 11pt;
        """)
        
        #creacion de los botones
        self.btn_abrir = QPushButton("📂 Abrir Archivo") #para que te redirija a la funcion abrir_archivo
        self.btn_analizar = QPushButton("🔍 Analizar Código")
        self.btn_limpiar = QPushButton("🧹 Limpiar")
        
        #estilo de los botones igual mente con estilo css 
        btn_style = """
            QPushButton {
                background-color: #3e3e3e; 
                color: white; 
                border: 1px solid #5e5e5e;
                padding: 5px;
                font-size: 11pt;
            }
            QPushButton:hover { background-color: #4e4e4e; }
        """
        self.btn_abrir.setStyleSheet(btn_style)
        self.btn_analizar.setStyleSheet(btn_style)
        self.btn_limpiar.setStyleSheet(btn_style)
        
        #diseño de la ventana y el como se acomodan los objetos en esta como los botones
        central_widget = QWidget()
        layout = QVBoxLayout()
        
        #barra de botones, añade los botones a la ventana
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btn_abrir)
        btn_layout.addWidget(self.btn_analizar)
        btn_layout.addWidget(self.btn_limpiar)
        
        layout.addLayout(btn_layout)
        layout.addWidget(QLabel("Editor de Código (C++):"))
        layout.addWidget(self.editor)
        layout.addWidget(QLabel("Resultados:"))
        layout.addWidget(self.resultados)
        
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget) #centra los objetos
        
        #conexiones de botones con funciones o mas bien de la accion hacer click en un boton con cada funcion
        self.btn_abrir.clicked.connect(self.abrir_archivo)
        self.btn_analizar.clicked.connect(self.analizar_codigo)
        self.btn_limpiar.clicked.connect(self.limpiar_pantalla)
        
        #tema oscuro para toda la aplicación
        self.setStyleSheet("""
            QMainWindow { background-color: #252525; }
            QLabel { color: #d4d4d4; font-size: 11pt; }
        """)

    def abrir_archivo(self): #sirve para que se abra el explorador de archivos y busques por tu cuenta el archivo, modificado para que pueda tambien aceptar archivos tipo .c
        filepath, _ = QFileDialog.getOpenFileName(self, "Abrir archivo", "", "Archivos C/C++ (*.c *.cpp);;All Files (*)")
        if filepath:
            with open(filepath, 'r', encoding='utf-8') as file: #se abre el archivo en mdoo r de lectura
                self.editor.setText(file.read()) #se llena el espacio para codigo con el codigo extraido del archivo

    def analizar_codigo(self): #funcion principal del programa ya que es la que cuenta los tokens
        codigo = self.editor.text() #obtiene el codigo que se escribio en el espacio para codigo
        if not codigo.strip():
            QMessageBox.warning(self, "Advertencia", "No hay código para analizar") #si no consiguio nada de self.editor significa que no se cargo nada y se muestra un menjsae de error
            return
        
        #Reiniciar contadores
        self.contRes = self.contVar = self.contVal = self.contOp = self.contDel = self.contSig = 0 #por si se sube un  nuevo codigo o algo o bien se analiza de nuevo el codigo no se sumen a lo contado anteriormente
        #inicializacion de conteo de llaves y parentesis
        llaves_abiertas = 0
        parentesis_abiertos = 0
        self.librerias_incluidas.clear()
        
        #Estado para comentarios multilínea
        en_comentario_multilinea = False
        errores.clear() #limpia la lista de errores por la misma razon de los contadores
        variables.clear()#limpio las variables que se guardaron

        #se checa el codigo linea por linea para saber en que linea se encuentran los errores de codigo
        lineas = codigo.split('\n')

        errores_cadenas, lineas = validar_cadenas(lineas)#se manda a llamar la funcion que checa si hay cadenas sin cerrar
        errores.extend(errores_cadenas)#se añaden las lineas de error que se encontraron

        errores.extend(validar_declaraciones(lineas))#se buscan las malas declaraciones de variables

        errores.extend(validar_for(lineas))#se buscan los for mal hechos

        errores.extend(validar_if(lineas))#se buscan los if mal hechos

        errores.extend(validar_while(lineas))#se buscan los if mal hechos

        errores.extend(validar_main(lineas))

        errores.extend(validar_printf(lineas))
      
        usa_namespace_std = any('using namespace std' in linea for linea in lineas)

        # Lista de identificadores que requieren std si no hay using
        std_identificadores = ['cout', 'cin', 'endl', 'cerr', 'clog']

        excepciones = ('if', 'for', 'while', 'switch', 'else')#cosas que en teoria no acaban en ;
        for numero_linea, linea in enumerate(lineas, 1):

            for identificador in std_identificadores:
                # si no hay using y se usa cout sin std::cout
                if not usa_namespace_std and re.search(rf'\b{identificador}\b', linea) and f'std::{identificador}' not in linea:
                    errores.append(f"Error: Se usa '{identificador}' sin 'std::' y sin 'using namespace std;' en la línea {numero_linea}.")
            
            #Se checa que las lineas finalicen correctamente
            linea_strip = linea.strip()#elimina espacios al principio y al final
            if linea_strip.startswith('#include'):
                # Extraer el nombre de la librería
                match = re.search(r'#include\s*[<"](.+?)[>"]', linea_strip)
                if match:
                    libreria = match.group(1)
                    if libreria in self.librerias_metodos:
                        self.librerias_incluidas.add(libreria)
                    else:
                        errores.append(f"Advertencia: Librería '{libreria}' no reconocida en línea {numero_linea}")

            if en_comentario_multilinea:
                if '*/' in linea_strip:
                    en_comentario_multilinea = False
                continue
            
            if '/*' in linea_strip:
                if '*/' not in linea_strip:
                    en_comentario_multilinea = True
                continue
                
            linea_limpia = re.sub(r'//.*|#.*', '', linea_strip).strip()
            if not linea_limpia:
                continue
            
            for char in self.caracteres_repetidos:
                if char*2 in linea_limpia:  # Busca dos caracteres iguales seguidos
                    # Excepciones para casos válidos como ::, ->, etc.
                    if not (char == ':' and '::' in linea_limpia) and \
                    not (char == '-' and '->' in linea_limpia) and \
                    not (char == '*' and '/*' in linea_strip) and \
                    not (char == '*' and '*/' in linea_strip):
                        errores.append(f"Error: Carácter '{char}' repetido en línea {numero_linea}")


            if (linea_strip and not linea_strip.startswith('#') and not linea_strip.startswith('import') and 
                not linea_strip.endswith('{') and not linea_strip.endswith('}')): #si es importacion, comentario o termian con llaves no se espera que tengan un ; al final
                #si termina en ')' y no en ';'
                if re.match(r'.*\)\s*$', linea_strip) and not linea_strip.endswith(';'):
                    #se ignora solo si es una estructura de control como un if (las cuales manejaremos como excepciones) o posible declaración de función
                    if any(linea_strip.startswith(e + '(') or linea_strip.startswith(e + ' ') for e in excepciones):
                        pass
                    elif re.match(r'^\w+\s+\w+\s*\(.*\)', linea_strip): #ejemplo: "string funcion_saludar(...)" o "void main(...)"
                        pass
                    else:
                        errores.append(f"Error: Falta ; al final de la línea:{numero_linea}")
                elif not linea_strip.endswith(';'):
                    errores.append(f"Error: Falta ; al final de la línea:{numero_linea}")

            tokens_linea = re.findall(r'"[^"]*"|\'[^\']*\'|<<|>>|\+\+|--|==|\w+|[^\w\s]', linea_strip, re.UNICODE)
            print(tokens_linea)
            """
            "[^"]*  -> todo lo que esta entre comillas (strings)
            '[^'/']* -> igual pero comillas simples el slash lo cambio porque si no es un simbolo de escape y no cuenta como comentario
            << >> -> desplazamientos
            /+/+ -> para el de incremento
            -- -> decremento
            == igualdad
            /w+ -> cualquier palabra
            ^/w/s cualquier otro caracter que no sea letra ni numero para que se encuentren los operadores

            al final separa todo en una lista ejemplo: ['main', '(', ')', ...] y asi con casa token
            """


            for token in tokens_linea:
                # Verificar si es un método de librería no incluida
                metodo_no_incluido = False
                for libreria, metodos in self.librerias_metodos.items():
                    if token in metodos and libreria not in self.librerias_incluidas:
                        errores.append(f"Error: Función '{token}' requiere librería '{libreria}' no incluida en la línea {numero_linea}")
                        metodo_no_incluido = True
                        break
                
                if metodo_no_incluido:
                    continue  # Saltar este token para evitar contarlo como variable

                if token not in self.reservadas:  # Si no es palabra reservada
                    # validación de los demás tokens para su conteo
                    if token in self.operadores:
                        self.contOp += 1
                    elif token in self.delimitadores:
                        self.contDel += 1
                    elif token in self.signos:
                        self.contSig += 1
                    elif re.fullmatch(r'"[^"]*"|\'[^\']*\'|[-+]?\d*\.\d+|[-+]?\d+', token): #para valores (números o cadenas)
                        self.contVal += 1
                    else:
                        print("variable: ", token)
                        self.contVar += 1  # se cuenta como variable
                        variable_valida(token, numero_linea) #usamos token limpio para la validación de variable
                else:
                    self.contRes += 1  #si es palabra reservada, se cuenta como reservada

            #chequeo de llaves y parentesis abiertos
            llaves_abiertas += linea_strip.count('{')#se suma si se abre
            llaves_abiertas -= linea_strip.count('}')#se resta si se cierra
            parentesis_abiertos += linea_strip.count('(')#se suma si se abre
            parentesis_abiertos -= linea_strip.count(')')#se resta si se cierra

            #se checa si hay mas cierres de los que deberia
            if llaves_abiertas < 0:
                errores.append(f"Error: Llave de cierre extra en la linea: {numero_linea}.")
                llaves_abiertas = 0 #se inicializa el contador para que no vuelva a salir un error

            if parentesis_abiertos < 0:
                errores.append(f"Error: Paréntesis de cierre extra en la línea: {numero_linea}.")
                parentesis_abiertos = 0 #se inicializa el contador para que no vuelva a salir un error

        if llaves_abiertas > 0: #chequeo final, puede que al final existan llaves o parentesis abiertos que no se cerraron nunca
            errores.append(f"Error: Llaves no cerradas hasta la línea: {numero_linea}.")
        if parentesis_abiertos > 0:
            errores.append(f"Error: Paréntesis no cerrados hasta la línea: {numero_linea}.")
        
        #mostrar resultados con formato HTML
        resumen = f"""
        <h3>=== RESUMEN ===</h3>
        <p><span style="color: #ff5555;">Palabras reservadas: {self.contRes}</span></p>
        <p><span style="color: #5555ff;">Variables: {self.contVar}</span></p>
        <p><span style="color: #55ff55;">Valores: {self.contVal}</span></p>
        <p><span style="color: #ffff55;">Operadores: {self.contOp}</span></p>
        <p><span style="color: #ff55ff;">Delimitadores: {self.contDel}</span></p>
        <p><span style="color: #55ffff;">Signos/Llaves: {self.contSig}</span></p>
        <h3>=== ERRORES ===</h3>
        """

        if errores:#si hubo errores
            resumen += "<ul>"
            for error in errores:
                resumen += f"<li>{error}</li>"
            resumen += "</ul>"
        else:
            resumen += "<p>No se encontraron errores en el codigo.</p>" #el codigo esta perfecto :)
        
        self.resultados.setHtml(f"{resumen}")

    def limpiar_pantalla(self):#limpia la ventana
        self.editor.clear()#limpia lo que muestra el codigo
        self.resultados.clear()#limpia lo que muestra los resultados

if __name__ == "__main__":#si se abrio programa.py osea este archivo en concreto
    app = QApplication(sys.argv)#inicializa la ventana
    
    # Configurar tema oscuro global
    app.setStyle("Fusion")
    dark_palette = app.palette()
    dark_palette.setColor(dark_palette.Window, QColor(53, 53, 53))
    dark_palette.setColor(dark_palette.WindowText, Qt.white)
    dark_palette.setColor(dark_palette.Base, QColor(30, 30, 30))
    dark_palette.setColor(dark_palette.Text, Qt.white)
    app.setPalette(dark_palette)
    
    ventana = CompiladorVSCode()
    ventana.show()#muestra la ventana
    sys.exit(app.exec_())#se mete en un bucle que permite que la ventana siga activa y no se cierre de una al correr el programa