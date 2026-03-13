import sys
import os
import ctypes
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QSizePolicy, QStackedWidget
from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QImage, QFont, QFontMetrics, QFontDatabase, QIcon
import pygame

# --- FORZAR IDENTIDAD DE APP (PARA LA BARRA DE TAREAS) ---
try:
    # Este ID debe ser único. Si no sale el logo, cámbiale una letra al ID y vuelve a compilar.
    myappid = 'studpro.final.v1' 
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except:
    pass

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    full_path = os.path.join(base_path, relative_path)
    if not os.path.exists(full_path):
        full_path = os.path.join(os.path.dirname(sys.executable), relative_path)
    return full_path

try: pygame.mixer.init()
except: pass

VOLUMEN_GENERAL = 0.3
COLOR_ESTETICO = "#dbc096"
COLOR_REINICIAR = "#faf6f0"
COLOR_CERRAR = "#ff3c3c"

def gestionar_musica(archivo, accion="play"):
    if not pygame.mixer.get_init(): return
    if accion == "pause": pygame.mixer.music.pause()
    elif accion == "unpause": pygame.mixer.music.unpause()
    elif accion == "stop": pygame.mixer.music.stop()
    elif archivo:
        ruta = resource_path(archivo)
        if os.path.exists(ruta):
            try:
                pygame.mixer.music.load(ruta)
                pygame.mixer.music.set_volume(VOLUMEN_GENERAL)
                pygame.mixer.music.play(-1)
            except: pass

def lanzar_alerta():
    try:
        pygame.mixer.music.stop()
        ruta = resource_path("alerta.mp3")
        if os.path.exists(ruta):
            s = pygame.mixer.Sound(ruta)
            s.set_volume(VOLUMEN_GENERAL + 0.2)
            s.play()
    except: pass

class EstudiometroWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ratio = 1.0
        self.tiempo_texto = "00:00"
        self.color_pro = QColor(COLOR_ESTETICO)

    def actualizar(self, ratio, texto):
        self.ratio = ratio
        self.tiempo_texto = texto
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        ancho, alto = self.width(), self.height()
        centro = QPointF(ancho / 2, alto / 2)
        diametro = min(ancho, alto) * 0.8
        rect_circulo = QRectF(centro.x() - diametro/2, centro.y() - diametro/2, diametro, diametro)
        pen = QPen(self.color_pro, diametro * 0.045, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(rect_circulo, 90 * 16, int(360 * self.ratio * 16))
        pts = int(diametro * 0.19)
        fuente = QFont("Kenao", pts, QFont.Weight.Bold)
        painter.setFont(fuente)
        metrics = QFontMetrics(fuente)
        ancho_num = metrics.horizontalAdvance("8")
        ancho_colon = metrics.horizontalAdvance(":")
        ancho_total = (ancho_num * 4) + ancho_colon
        x_start = centro.x() - (ancho_total / 2)
        y_centro_v = centro.y() + (metrics.capHeight() / 2) - 2 
        for i, char in enumerate(self.tiempo_texto):
            if i < 2: cur_x = x_start + (i * ancho_num); w_c = ancho_num
            elif i == 2: cur_x = x_start + (2 * ancho_num); w_c = ancho_colon
            else: cur_x = x_start + (2 * ancho_num) + ancho_colon + ((i-3) * ancho_num); w_c = ancho_num
            rect_celda = QRectF(cur_x, y_centro_v - metrics.height(), w_c, metrics.height() * 1.2)
            painter.drawText(rect_celda, Qt.AlignmentFlag.AlignCenter, char)

class StudPro(QWidget):
    def __init__(self):
        super().__init__()
        # NOMBRE CORREGIDO
        self.setWindowTitle("StudPro")
        self.setMinimumSize(800, 600)
        
        # LOGO DE VENTANA
        ruta_logo = resource_path("logo.ico")
        if os.path.exists(ruta_logo):
            self.setWindowIcon(QIcon(ruta_logo))
        
        if os.path.exists(resource_path("Kenao.otf")):
            QFontDatabase.addApplicationFont(resource_path("Kenao.otf"))

        self.fases = [
            ("ESTUDIO 1", 55, "estudio"), ("DESCANSO 1", 5, "descanso"),
            ("ESTUDIO 2", 50, "estudio"), ("DESCANSO 2", 10, "descanso"),
            ("ESTUDIO 3", 45, "estudio"), ("DESCANSO 3", 30, "descanso")
        ]
        self.idx = 0; self.estado = "inicio"; self.pausado = False
        self.img_inicio = QImage(resource_path("inicio.jpg"))
        self.img_estudio = QImage(resource_path("imagen_bonita.jpg"))
        self.img_descanso = QImage(resource_path("fondo_descanso.jpg"))

        self.init_ui()
        self.timer = QTimer(self); self.timer.timeout.connect(self.motor_cronometro)
        self.showMaximized()

    def init_ui(self):
        self.stacked = QStackedWidget(self)
        layout_main = QVBoxLayout(self); layout_main.setContentsMargins(0, 0, 0, 0); layout_main.addWidget(self.stacked)
        self.capa_inicio = QFrame(); lay_ini = QVBoxLayout(self.capa_inicio)
        self.lbl_welcome = QLabel("BIENVENIDO A STUDPRO"); self.lbl_ready = QLabel("Pulsa para empezar")
        self.btn_iniciar = QPushButton("INICIAR"); self.btn_iniciar.clicked.connect(self.arrancar_sesion)
        for lbl in [self.lbl_welcome, self.lbl_ready]: lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay_ini.addStretch(2); lay_ini.addWidget(self.lbl_welcome); lay_ini.addWidget(self.lbl_ready); lay_ini.addStretch(1)
        lay_ini.addWidget(self.btn_iniciar, 0, Qt.AlignmentFlag.AlignCenter); lay_ini.addStretch(2)
        self.stacked.addWidget(self.capa_inicio)
        self.capa_estudio = QFrame(); lay_est = QVBoxLayout(self.capa_estudio)
        self.lbl_fase = QLabel(""); self.lbl_fase.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.visual = EstudiometroWidget(); self.btn_pausa = QPushButton("PAUSA"); self.btn_pausa.clicked.connect(self.toggle_pausa)
        lay_est.addStretch(1); lay_est.addWidget(self.lbl_fase); lay_est.addStretch(1); lay_est.addWidget(self.visual, 20); lay_est.addStretch(1); lay_est.addWidget(self.btn_pausa, 0, Qt.AlignmentFlag.AlignCenter); lay_est.addStretch(1)
        self.stacked.addWidget(self.capa_estudio)
        self.capa_final = QFrame(); lay_fin = QVBoxLayout(self.capa_final)
        self.lbl_enhorabuena = QLabel("¡Enhorabuena, has finalizado la sesión de estudio!"); self.lbl_enhorabuena.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_volver = QLabel("Puedes volver a\nempezar con..."); self.lbl_finalizar = QLabel("O finalizar la sesión\ncon...")
        self.btn_reiniciar = QPushButton("REINICIAR"); self.btn_reiniciar.clicked.connect(self.reiniciar_todo); self.btn_cerrar = QPushButton("CERRAR"); self.btn_cerrar.clicked.connect(self.close)
        lay_h = QHBoxLayout(); col_izq = QVBoxLayout(); col_izq.addWidget(self.lbl_volver); col_izq.addWidget(self.btn_reiniciar, 0, Qt.AlignmentFlag.AlignCenter); col_der = QVBoxLayout(); col_der.addWidget(self.lbl_finalizar); col_der.addWidget(self.btn_cerrar, 0, Qt.AlignmentFlag.AlignCenter)
        lay_h.addStretch(1); lay_h.addLayout(col_izq); lay_h.addStretch(1); lay_h.addLayout(col_der); lay_h.addStretch(1)
        lay_fin.addStretch(2); lay_fin.addWidget(self.lbl_enhorabuena); lay_fin.addStretch(1); lay_fin.addLayout(lay_h); lay_fin.addStretch(2)
        self.stacked.addWidget(self.capa_final)

    def resizeEvent(self, event):
        escala = min(self.width(), self.height()); f = "Kenao"
        self.lbl_welcome.setFont(QFont(f, int(escala * 0.08), QFont.Weight.Bold)); self.lbl_ready.setFont(QFont(f, int(escala * 0.045)))
        self.lbl_fase.setFont(QFont(f, int(escala * 0.07))); self.lbl_enhorabuena.setFont(QFont(f, int(escala * 0.06), QFont.Weight.Bold))
        for lbl in [self.lbl_volver, self.lbl_finalizar]: lbl.setFont(QFont(f, int(escala * 0.045)))
        for lbl in [self.lbl_welcome, self.lbl_ready, self.lbl_fase, self.lbl_enhorabuena, self.lbl_volver, self.lbl_finalizar]: lbl.setStyleSheet(f"color: {COLOR_ESTETICO};")
        self.estilizar_btn(self.btn_iniciar, escala, COLOR_ESTETICO); self.estilizar_btn(self.btn_pausa, escala, COLOR_ESTETICO); self.estilizar_btn(self.btn_reiniciar, escala, COLOR_REINICIAR); self.estilizar_btn(self.btn_cerrar, escala, COLOR_CERRAR)

    def estilizar_btn(self, btn, escala, color):
        ancho = int(escala * 0.35); btn.setFixedSize(ancho, int(ancho * 0.35)); ref = "REANUDAR" if btn == self.btn_pausa else btn.text()
        pts = int(escala * 0.045); fuente = QFont("Kenao", pts, QFont.Weight.Bold); metrics = QFontMetrics(fuente)
        while metrics.horizontalAdvance(ref) > ancho * 0.85 and pts > 5: pts -= 1; fuente.setPointSize(pts); metrics = QFontMetrics(fuente)
        btn.setFont(fuente); btn.setStyleSheet(f"QPushButton {{ background: transparent; color: {color}; border: {max(3, int(escala*0.012))}px solid {color}; border-radius: {int(ancho*0.17)}px; }}")

    def paintEvent(self, event):
        painter = QPainter(self)
        img = self.img_inicio if self.estado in ["inicio", "final"] else (self.img_estudio if self.idx > 0 and self.fases[self.idx-1][2] == "estudio" else self.img_descanso)
        if not img.isNull():
            img_scaled = img.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            painter.drawImage(0, 0, img_scaled)

    def arrancar_sesion(self): self.estado = "study"; self.idx = 0; self.stacked.setCurrentIndex(1); QTimer.singleShot(150, self.comenzar_fase)
    def reiniciar_todo(self): self.idx = 0; self.arrancar_sesion()
    def comenzar_fase(self):
        if self.idx < len(self.fases):
            nombre, mins, tipo = self.fases[self.idx]; self.total_fase = mins * 60; self.segundos = self.total_fase; self.idx += 1
            self.lbl_fase.setText(nombre); gestionar_musica("ruido_blanco.mp3" if tipo == "estudio" else "piano.mp3", "play"); self.timer.start(1000); self.update()
        else: self.estado = "final"; self.stacked.setCurrentIndex(2); lanzar_alerta(); self.update()
    def motor_cronometro(self):
        if self.segundos > 0: self.segundos -= 1; m, s = divmod(self.segundos, 60); self.visual.actualizar(self.segundos / self.total_fase, f"{m:02}:{s:02}")
        else: self.timer.stop(); self.comenzar_fase()
    def toggle_pausa(self):
        if not self.pausado: self.timer.stop(); gestionar_musica(None, "pause"); self.btn_pausa.setText("REANUDAR")
        else: self.timer.start(1000); gestionar_musica(None, "unpause"); self.btn_pausa.setText("PAUSA")
        self.pausado = not self.pausado; self.estilizar_btn(self.btn_pausa, min(self.width(), self.height()), COLOR_ESTETICO)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = StudPro(); sys.exit(app.exec())