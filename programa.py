import sys
import re
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, 
                             QHBoxLayout, QPushButton, QFileDialog, QMessageBox, QTextEdit)
from PyQt5.QtGui import QColor, QFont, QTextCharFormat, QSyntaxHighlighter, QTextDocument
from PyQt5.QtCore import Qt, QRegExp
from PyQt5.Qsci import QsciScintilla, QsciLexerCPP

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
        self.setWindowTitle("Compilador - VSCode Style")
        self.setGeometry(100, 100, 1000, 800)
        
        # Contadores (los mismos de tu código original)
        self.contRes = self.contVar = self.contVal = self.contOp = self.contDel = self.contSig = 0
        self.reservadas = ['int','float','char','string','bool','include','iostream','using','namespace','std',
                         'main','if','else','for','while','do','switch','case','cin','cout','endl','return',
                         'printf','scanf']
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

    def analizar_codigo(self):
        codigo = self.editor.text()
        if not codigo.strip():
            QMessageBox.warning(self, "Advertencia", "No hay código para analizar")
            return
        
        # Reiniciar contadores
        self.contRes = self.contVar = self.contVal = self.contOp = self.contDel = self.contSig = 0
        
        # Procesar tokens (igual que tu código original)
        tokens = re.findall(r'"[^"]*"|\'[^\']*\'|<<|>>|\+\+|--|==|\w+|[^\w\s]', codigo, re.UNICODE)
        
        # Generar HTML para colorear los resultados
        html_output = ""
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