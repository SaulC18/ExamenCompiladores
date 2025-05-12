import sys #interaccion con el sistema
import re #expresiones regulares

#interfaz grafica es otra alternativa a por ejemplo tkinter que es mas conocido pero a la vez mas simple
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, 
                             QHBoxLayout, QPushButton, QFileDialog, QMessageBox, QTextEdit)
from PyQt5.QtGui import QColor, QFont, QTextCharFormat, QSyntaxHighlighter, QTextDocument
from PyQt5.QtCore import Qt, QRegExp
from PyQt5.Qsci import QsciScintilla, QsciLexerCPP



errores = [] #para ir almacenando los errores y despues ponerlos en la parte de resultados al final


#validaciones

def variable_valida(nombre, ln_err): #variable aceptable, se le manda la variable o lo que se pueda considerar como una y la linea donde se encuentra 
    #expresión regular para nombres de variables válidos
    validacion = re.compile(r'^[a-zA-Z_]\w*$') #puede comenzar con letras o guin bajo y lo demas puede ser letras, guion bajo o nuemros
    
    #coincide la variable con la validacion?
    if nombre and nombre.strip() and not validacion.match(nombre):
        errores.append(f"Error: {ln_err} La variable '{nombre}' es inválida en la linea: {ln_err}.")

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
        
        errores.clear() #limpia la lista de errores por la misma razon de los contadores

        #se checa el codigo linea por linea para saber en que linea se encuentran los errores de codigo
        lineas = codigo.split('\n')

        errores_cadenas, lineas = validar_cadenas(lineas)#se manda a llamar la funcion que checa si hay cadenas sin cerrar
        errores.extend(errores_cadenas)#se añaden las lineas de error que se encontraron

        excepciones = ('if', 'for', 'while', 'switch', 'else')#cosas que en teoria no acaban en ;
        for numero_linea, linea in enumerate(lineas, 1):

            #Se checa que las lineas finalicen correctamente
            linea_strip = linea.strip()#elimina espacios al principio y al final
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