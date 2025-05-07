import sys
import re
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, 
                             QHBoxLayout, QPushButton, QFileDialog, QMessageBox, QTextEdit)
from PyQt5.QtGui import QColor, QFont, QTextCharFormat, QSyntaxHighlighter, QTextDocument
from PyQt5.QtCore import Qt, QRegExp
from PyQt5.Qsci import QsciScintilla, QsciLexerCPP

import subprocess
import os

os.environ["PATH"] += r";C:\MinGW\bin"

errores = [] #para ir almacenando los errores y despues ponerlos en la parte de resultados al final
def variable_valida(nombre, ln_code, ln_err): #variable aceptable
    # Expresión regular para nombres de variables válidos
    validacion = re.compile(r'^[a-zA-Z_]\w*$') #puede comenzar con letras o guin bajo y lo demas puede ser letras, guion bajo o nuemros
    #coincide la variable con la validacion?
    if not validacion.match(nombre):
        errores.append(f"Error: La variable '{nombre}' es inválida en la linea: {ln_err}.")

def validar_cadenas(lineas):#para checar que una cadena se cierre
    errores = [] #se van guardando los errores por si hay varios
    en_string = False #para saber si esta dentro de un string
    comilla_abierta = '' #guardar la comillla que se abrio " o '
    linea_inicio = 0 #en que linea se abrio la cadena

    for i, linea in enumerate(lineas, 1): #se recorre linea por linea
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
            en_string = False #ya no esta en un string

    return errores #se retorna lista de errores

class CodeEditor(QsciScintilla):
    def __init__(self):
        super().__init__()

        # Configuración básica del editor
        self.setUtf8(True)
        self.setAutoIndent(True)
        self.setMarginLineNumbers(1, True)
        self.setMarginWidth(1, "0000")
        self.setStyleSheet("background-color: #282a36; color: #f8f8f2;")

        # Configuración del lexer con colores Dracula
        lexer = QsciLexerCPP()
        font = QFont("Consolas", 11)
        lexer.setDefaultFont(font)

        lexer.setColor(QColor("#ff79c6"), 1)  # Palabras clave
        lexer.setColor(QColor("#8be9fd"), 2)  # Tipos
        lexer.setColor(QColor("#f1fa8c"), 3)  # Strings
        lexer.setColor(QColor("#bd93f9"), 4)  # Números
        lexer.setColor(QColor("#6272a4"), 5)  # Comentarios
        lexer.setColor(QColor("#ffb86c"), 10) # Operadores
        lexer.setColor(QColor("#f8f8f2"), 11) # Identificadores
        lexer.setColor(QColor("#ff5555"), 16) # Errores

        lexer.setFont(font) 
        self.setLexer(lexer)

        # Opcional: colores para fondo del texto seleccionado y cursor
        self.SendScintilla(QsciScintilla.SCI_SETCARETFORE, QColor("#f8f8f2"))
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QColor("#44475a"))

class CompiladorVSCode(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("👾 Compilador ")
        self.setGeometry(100, 100, 1000, 800)
        
        # Contadores (los mismos de tu código original)
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
        self.operadores = ['+','-','*','/','++','--','#','<','>','<<','>>','=','==','!=']
        self.delimitadores = [';',',','.']
        self.signos = ['{','}','(',')']

        # Editor de código
        self.editor = CodeEditor()
        
        # Panel de resultados (con scroll y tema oscuro)    
        self.resultados = QTextEdit()
        self.resultados.setReadOnly(True)
        self.resultados.setStyleSheet("""
            background-color: #1e1e1e; 
            color: #d4d4d4; 
            font-family: Consolas;
            font-size: 11pt;
        """)
        
        # Botones
        self.btn_abrir = QPushButton("📂 Abrir Archivo")
        self.btn_analizar = QPushButton("🔍 Analizar Código")
        self.btn_limpiar = QPushButton("🧹 Limpiar")
        
        # Estilo de botones
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
        
        # Diseño
        central_widget = QWidget()
        layout = QVBoxLayout()
        
        # Barra de botones
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
        self.setCentralWidget(central_widget)
        
        # Conexiones
        self.btn_abrir.clicked.connect(self.abrir_archivo)
        self.btn_analizar.clicked.connect(self.analizar_codigo)
        self.btn_limpiar.clicked.connect(self.limpiar_pantalla)
        
        # Tema oscuro para toda la aplicación
        self.setStyleSheet("""
            QMainWindow { background-color: #252525; }
            QLabel { color: #d4d4d4; font-size: 11pt; }
        """)

    def abrir_archivo(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Abrir archivo", "", "C++ Files (*.cpp);;All Files (*)")
        if filepath:
            with open(filepath, 'r', encoding='utf-8') as file:
                self.editor.setText(file.read())
            self.ruta_archivo = filepath

    def analizar_codigo(self):
        codigo = self.editor.text()
        if not codigo.strip():
            QMessageBox.warning(self, "Advertencia", "No hay código para analizar")
            return
        
        # Guardar los cambios del editor al archivo antes de compilar
        with open(self.ruta_archivo, 'w', encoding='utf-8') as f:
            f.write(codigo)

        # Generar nombre del ejecutable a partir del nombre base del archivo
        direc = os.path.dirname(self.ruta_archivo)
        nombre_base = os.path.splitext(os.path.basename(self.ruta_archivo))[0]
        ejecutable = os.path.join(direc, nombre_base + '.exe')

        # Compilar el código C++
        resultado_compilacion = subprocess.run(
            [r'C:\MinGW\bin\g++.exe', self.ruta_archivo, '-o', ejecutable],
            cwd=direc,
            capture_output=True,
            text=True,
            shell=True  # Puedes quitar shell=True si no es necesario
        )
        
        # Reiniciar contadores
        self.contRes = self.contVar = self.contVal = self.contOp = self.contDel = self.contSig = 0
        
        # Procesar tokens (igual que tu código original)
        tokens = re.findall(r'"[^"\n]*"|\'[^\'\n]*\'|'        # Strings
                    r'-?\d+\.\d+|-?\d+|'              # Números
                    r'\+\+|--|==|!=|<=|>=|<<|>>|'     # Operadores dobles
                    r'[+\-*/#<>=]'                    # Operadores simples
                    r'|[a-zA-Z_]\w*|'                 # Identificadores válidos
                    r'[;:,.\[\]{}()\\]'               # Delimitadores y signos
                    r'|[^\s]', codigo, re.UNICODE)
        
        #Generar HTML para colorear los resultados
        html_output = ""
        errores.clear() #limpia la lista de errores por la misma razon de los contadores
         #se checa el codigo linea por linea para saber en que linea se encuentran los errores de codigo
        lineas = codigo.split('\n')
        errores.extend(validar_cadenas(lineas))#se manda a llamar la funcion que checa si hay cadenas sin cerrar

        for token in tokens:
            if token in self.reservadas:
                self.contRes += 1
                html_output += f'<span style="color: #ff5555;">{token}</span> '
            elif token in self.valores or re.fullmatch(r'"[^"]*"|\'[^\']*\'|[-+]?\d*\.\d+|[-+]?\d+', token):
                self.contVal += 1
                html_output += f'<span style="color: #55ff55;">{token}</span> '
            elif token in self.operadores:
                self.contOp += 1
                html_output += f'<span style="color: #ffff55;">{token}</span> '
            elif token in self.delimitadores:
                self.contDel += 1
                html_output += f'<span style="color: #ff55ff;">{token}</span> '
            elif token in self.signos:
                self.contSig += 1
                html_output += f'<span style="color: #55ffff;">{token}</span> '
            else:
                self.contVar += 1
                html_output += f'<span style="color: #5555ff;">{token}</span> '
        
        # Mostrar resultados con formato HTML
        resumen = f"""
        <h3>=== RESUMEN ===</h3>
        <p><span style="color: #ff5555;">Palabras reservadas: {self.contRes}</span></p>
        <p><span style="color: #5555ff;">Variables: {self.contVar}</span></p>
        <p><span style="color: #55ff55;">Valores: {self.contVal}</span></p>
        <p><span style="color: #ffff55;">Operadores: {self.contOp}</span></p>
        <p><span style="color: #ff55ff;">Delimitadores: {self.contDel}</span></p>
        <p><span style="color: #55ffff;">Signos/Llaves: {self.contSig}</span></p>
        <p><strong>Total de tokens: {len(tokens)}</strong></p>
        """
        
        self.resultados.setHtml(f"{html_output}<br><br>{resumen}")


        if resultado_compilacion.returncode != 0:
            errores_compilacion = resultado_compilacion.stderr.splitlines()

            for linea_error in errores_compilacion:
                match = re.search(r'[^:]+:(\d+):\d+: (error|warning): (.+)', linea_error)
                if match:
                    linea = match.group(1)
                    tipo = match.group(2).capitalize()
                    descripcion = match.group(3).strip()
                    errores.append(f"{tipo} en línea {linea}: {descripcion}")

            # Guardar errores en archivo
            ruta_errores = os.path.join(direc, 'errores_compilacion.txt')
            with open(ruta_errores, 'w', encoding='utf-8') as f:
                f.write("\n".join(errores))

            # Mostrar errores en la interfaz
            errores_html = f"<hr><h3>Errores de compilación:</h3><ul>"
            for err in errores:
                errores_html += f"<li>{err}</li>"
            errores_html += "</ul>"
            self.resultados.append(errores_html)
        else:
            self.resultados.append("<hr><h3>Compilación exitosa (sin ejecutar el programa).</h3>")

    def limpiar_pantalla(self):
        self.editor.clear()
        self.resultados.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Configurar tema oscuro global
    app.setStyle("Fusion")
    dark_palette = app.palette()
    dark_palette.setColor(dark_palette.Window, QColor(53, 53, 53))
    dark_palette.setColor(dark_palette.WindowText, Qt.white)
    dark_palette.setColor(dark_palette.Base, QColor(30, 30, 30))
    dark_palette.setColor(dark_palette.Text, Qt.white)
    app.setPalette(dark_palette)
    
    ventana = CompiladorVSCode()
    ventana.show()
    sys.exit(app.exec_())