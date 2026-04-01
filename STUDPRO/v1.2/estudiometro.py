import sys
import os
import ctypes
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QFrame, QStackedWidget, QComboBox, QScrollArea, 
                             QSizePolicy, QStyledItemDelegate, QListView)
from PyQt6.QtCore import Qt, QTimer, QRectF, pyqtSignal, QSize
from PyQt6.QtGui import QPainter, QColor, QPen, QImage, QFont, QFontDatabase, QIcon, QPixmap
import pygame

# --- IDENTIDAD STUDPRO V1.2 ---
try:
    myappid = 'studpro.v1.2' 
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except: pass

def resource_path(relative_path):
    base_path = os.path.dirname(os.path.abspath(__file__))
    rutas = [os.path.join(base_path, relative_path), os.path.join(base_path, "dist", relative_path),
             os.path.join(sys._MEIPASS, relative_path) if hasattr(sys, "_MEIPASS") else relative_path]
    for r in rutas:
        if os.path.exists(r): return r
    return relative_path

try: pygame.mixer.init()
except: pass

COLOR_ESTETICO = "#dbc096"
COLOR_NEGRO_ALPHA = "rgba(0, 0, 0, 225)"

class CenteredDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = Qt.AlignmentFlag.AlignCenter

class ItemConfiguracion(QFrame):
    deleteRequested = pyqtSignal(int)
    def __init__(self, numero, estudio_def, descanso_def, parent=None):
        super().__init__(parent)
        self.numero_actual = numero
        self.setStyleSheet(f"QFrame {{ background-color: {COLOR_NEGRO_ALPHA}; border-radius: 20px; border: 2px solid {COLOR_ESTETICO}; }}")
        self.setFixedHeight(180)
        layout = QVBoxLayout(self); layout.setContentsMargins(25, 10, 25, 15)
        header = QHBoxLayout(); header.addStretch(1)
        self.titulo = QLabel(f"POMODORO {numero}")
        self.titulo.setStyleSheet(f"border: none; background: transparent; color: {COLOR_ESTETICO}; font-family: Belgrano; font-size: 26px; font-weight: bold;")
        header.addWidget(self.titulo); header.addStretch(1)
        self.btn_trash = QPushButton()
        self.btn_trash.setFixedSize(50, 50)
        ruta_trash = resource_path("trash.png")
        if os.path.exists(ruta_trash):
            self.btn_trash.setIcon(QIcon(ruta_trash))
            self.btn_trash.setIconSize(QSize(40, 40))
        self.btn_trash.setStyleSheet("QPushButton { border: none; background: transparent; } QPushButton:hover { background-color: rgba(255, 60, 60, 50); border-radius: 12px; }")
        self.btn_trash.clicked.connect(lambda: self.deleteRequested.emit(self.numero_actual))
        header.addWidget(self.btn_trash); layout.addLayout(header)
        controles = QHBoxLayout()
        for label_text, def_val in [("Estudio", estudio_def), ("Descanso", descanso_def)]:
            col = QVBoxLayout()
            lbl = QLabel(label_text); lbl.setStyleSheet("border: none; background: transparent; color: white; font-family: Belgrano; font-size: 20px;")
            combo = QComboBox()
            combo.setStyleSheet(f"QComboBox {{ background-color: black; color: {COLOR_ESTETICO}; border: 2px solid {COLOR_ESTETICO}; border-radius: 10px; padding: 5px; padding-left: 105px; font-family: Belgrano; font-size: 22px; min-height: 45px; }} QComboBox::drop-down {{ border: none; width: 0px; }}")
            view = QListView(); view.setStyleSheet(f"background-color: black; color: {COLOR_ESTETICO}; selection-background-color: {COLOR_ESTETICO}; selection-foreground-color: black; font-family: Belgrano; font-size: 20px;")
            combo.setView(view); combo.setItemDelegate(CenteredDelegate())
            combo.setFocusPolicy(Qt.FocusPolicy.NoFocus); combo.addItems([f"{m} min" for m in range(5, 65, 5)])
            combo.setCurrentText(f"{def_val} min")
            col.addWidget(lbl, 0, Qt.AlignmentFlag.AlignCenter); col.addWidget(combo)
            controles.addLayout(col)
            if label_text == "Estudio": self.combo_est = combo; controles.addSpacing(60)
            else: self.combo_des = combo
        layout.addLayout(controles)

class StudPro(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StudPro")
        self.setMinimumSize(1200, 900)
        QFontDatabase.addApplicationFont(resource_path("Kenao.otf"))
        QFontDatabase.addApplicationFont(resource_path("Belgrano-Regular.otf"))
        self.img_inicio = QImage(resource_path("inicio.jpg"))
        self.img_bonita = QImage(resource_path("imagen_bonita.jpg"))
        self.img_descanso = QImage(resource_path("fondo_descanso.jpg"))
        self.num_pomodoros = 1
        self.config_actual = [{"estudio": 55, "descanso": 5} for _ in range(10)]
        self.estado = "inicio"; self.pausado = False
        self.w_lista = []  # ← NUEVO: inicializado antes de init_ui
        self.init_ui()
        self.timer = QTimer(self); self.timer.timeout.connect(self.motor)
        self.showMaximized()

    def init_ui(self):
        self.stacked = QStackedWidget(self)
        layout_main = QVBoxLayout(self); layout_main.setContentsMargins(0, 0, 0, 0); layout_main.addWidget(self.stacked)
        self.capa_ini = QFrame(); self.lay_ini = QVBoxLayout(self.capa_ini)
        self.lbl_logo = QLabel(); self.lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ruta_logo = resource_path("logo.png")
        if os.path.exists(ruta_logo): self.pix_logo = QPixmap(ruta_logo)
        self.lbl_welcome = QLabel("BIENVENID@ A"); self.lbl_main = QLabel("STUDPRO")
        self.btn_ini = QPushButton("INICIAR"); self.btn_pers = QPushButton("PERSONALIZAR")
        self.btn_ini.clicked.connect(self.arrancar); self.btn_pers.clicked.connect(lambda: self.stacked.setCurrentIndex(1))
        self.stacked.addWidget(self.capa_ini)
        self.capa_cfg = QFrame(); lay_cfg_h = QHBoxLayout(self.capa_cfg); lay_cfg_h.setSpacing(0)
        panel_lat = QFrame(); panel_lat.setFixedWidth(280); panel_lat.setStyleSheet(f"background-color: {COLOR_NEGRO_ALPHA}; border-right: 2px solid {COLOR_ESTETICO};")
        lay_lat = QVBoxLayout(panel_lat); lay_lat.addStretch(1)
        lbl_q = QLabel("Cantidad de\nPomodoros:"); lbl_q.setStyleSheet(f"color: {COLOR_ESTETICO}; font-family: Belgrano; font-size: 22px; font-weight: bold; background: transparent;")
        lbl_q.setAlignment(Qt.AlignmentFlag.AlignCenter); lay_lat.addWidget(lbl_q); lay_lat.addSpacing(25)
        self.btns_n = []
        for i in range(1, 11):
            b = QPushButton(str(i)); b.setFixedSize(55, 55); b.clicked.connect(lambda ch, n=i: self.set_pomos(n))
            lay_lat.addWidget(b, 0, Qt.AlignmentFlag.AlignCenter); self.btns_n.append(b)
        lay_lat.addStretch(1)
        panel_der = QVBoxLayout(); panel_der.setContentsMargins(40, 40, 40, 40)
        tit = QLabel("CONFIGURACIÓN"); tit.setStyleSheet(f"color: {COLOR_ESTETICO}; font-family: Kenao; font-size: 55px; background: transparent; font-weight: bold;")
        panel_der.addWidget(tit, 0, Qt.AlignmentFlag.AlignCenter); panel_der.addSpacing(20)
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True); self.scroll.setStyleSheet("background: transparent; border: none;")
        self.cont = QWidget(); self.cont.setStyleSheet("background: transparent;")
        self.lay_p = QVBoxLayout(self.cont); self.lay_p.setSpacing(25); self.scroll.setWidget(self.cont); panel_der.addWidget(self.scroll)
        panel_der.addSpacing(20); self.btn_guardar = QPushButton("GUARDAR")
        self.btn_guardar.clicked.connect(self.guardar_y_volver); panel_der.addWidget(self.btn_guardar, 0, Qt.AlignmentFlag.AlignCenter)
        lay_cfg_h.addWidget(panel_lat); lay_cfg_h.addLayout(panel_der); self.stacked.addWidget(self.capa_cfg)
        self.capa_mot = QFrame(); lay_m = QVBoxLayout(self.capa_mot); self.lbl_f = QLabel(""); self.vis = EstudiometroWidget(self)
        self.btn_pausa = QPushButton("PAUSA"); self.btn_pausa.clicked.connect(self.toggle_pausa)
        lay_m.addStretch(1); lay_m.addWidget(self.lbl_f, 0, Qt.AlignmentFlag.AlignCenter); lay_m.addWidget(self.vis, 4); lay_m.addWidget(self.btn_pausa, 0, Qt.AlignmentFlag.AlignCenter); lay_m.addStretch(1)
        self.stacked.addWidget(self.capa_mot); self.set_pomos(1)

    def set_pomos(self, n):
        # ← NUEVO: guardar valores actuales antes de destruir los widgets
        for i, w in enumerate(self.w_lista):
            self.config_actual[i] = {
                "estudio": int(w.combo_est.currentText().split(" ")[0]),
                "descanso": int(w.combo_des.currentText().split(" ")[0])
            }
        self.num_pomodoros = max(1, n)
        while self.lay_p.count():
            item = self.lay_p.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self.lay_p.addStretch(1)
        self.w_lista = []
        for i in range(self.num_pomodoros):
            w = ItemConfiguracion(i+1, self.config_actual[i]["estudio"], self.config_actual[i]["descanso"])
            w.deleteRequested.connect(self.eliminar_pomodoro)
            self.lay_p.addWidget(w)
            self.w_lista.append(w)
        self.lay_p.addStretch(1)
        self.actualizar_botones()

    def guardar_y_volver(self):
        for i, w in enumerate(self.w_lista):
            self.config_actual[i] = {"estudio": int(w.combo_est.currentText().split(" ")[0]), "descanso": int(w.combo_des.currentText().split(" ")[0])}
        self.stacked.setCurrentIndex(0)

    def eliminar_pomodoro(self, n_eliminar):
        if self.num_pomodoros > 1:
            idx = n_eliminar - 1
            for i in range(idx, 9): self.config_actual[i] = self.config_actual[i+1]
            self.config_actual[9] = {"estudio": 55, "descanso": 5}; self.set_pomos(self.num_pomodoros - 1)

    def actualizar_botones(self):
        for i, b in enumerate(self.btns_n):
            b.setFixedSize(55, 55)
            if i < self.num_pomodoros: b.setStyleSheet(f"background-color: {COLOR_ESTETICO}; color: black; border: 2px solid {COLOR_ESTETICO}; border-radius: 27px; font-family: Belgrano; font-size: 22px; font-weight: bold;")
            else: b.setStyleSheet(f"background-color: transparent; color: {COLOR_ESTETICO}; border: 2px solid {COLOR_ESTETICO}; border-radius: 27px; font-family: Belgrano; font-size: 22px; font-weight: bold;")

    def play_sound(self, file, loop=0):
        try:
            pygame.mixer.music.stop()
            path = resource_path(file)
            if os.path.exists(path): pygame.mixer.music.load(path); pygame.mixer.music.play(loop)
        except: pass

    def toggle_pausa(self):
        if not self.pausado: self.timer.stop(); pygame.mixer.music.pause(); self.btn_pausa.setText("REANUDAR")
        else: self.timer.start(50); pygame.mixer.music.unpause(); self.btn_pausa.setText("PAUSA")
        self.pausado = not self.pausado

    def arrancar(self):
        self.fases = []
        for i in range(self.num_pomodoros):
            config = self.config_actual[i]; self.fases.append((f"ESTUDIO {i+1}", config["estudio"], "estudio")); self.fases.append((f"DESCANSO {i+1}", config["descanso"], "descanso"))
        self.idx = 0; self.estado = "study"; self.stacked.setCurrentIndex(2); self.next_fase()

    def next_fase(self):
        if self.idx < len(self.fases):
            if self.idx > 0: self.play_sound("alerta.mp3")
            n, m, t = self.fases[self.idx]; self.total_ms = m*60*1000; self.rem_ms = self.total_ms; self.idx += 1
            self.lbl_f.setText(n); self.lbl_f.setStyleSheet(f"color: {COLOR_ESTETICO}; font-family: Kenao; font-size: 75px; font-weight: bold; background: transparent;")
            self.timer.start(50)
            if t == "estudio": self.play_sound("ruido_blanco.mp3", -1)
            else: self.play_sound("piano.mp3", -1)
        else: self.play_sound("alerta.mp3"); self.stacked.setCurrentIndex(0); self.estado = "inicio"

    def motor(self):
        if self.rem_ms > 0:
            self.rem_ms -= 50; seg_t = self.rem_ms // 1000; m, s = divmod(seg_t, 60); self.vis.actualizar(self.rem_ms/self.total_ms, f"{m:02}:{s:02}")
        else: self.timer.stop(); self.next_fase()

    def paintEvent(self, event):
        pa = QPainter(self); img = self.img_inicio
        if self.stacked.currentIndex() == 1: img = self.img_bonita
        elif self.estado == "study": img = self.img_bonita if "ESTUDIO" in self.lbl_f.text() else self.img_descanso
        if not img.isNull(): pa.drawImage(0, 0, img.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))

    def resizeEvent(self, event):
        e = min(self.width(), self.height())
        st_btn = f"QPushButton {{ background-color: transparent; color: {COLOR_ESTETICO}; border: 3px solid {COLOR_ESTETICO}; border-radius: 18px; padding: 15px; font-family: Kenao; font-size: {int(e*0.035)}px; min-width: {int(e*0.35)}px; }} QPushButton:hover {{ background-color: {COLOR_ESTETICO}; color: black; }}"
        if hasattr(self, 'pix_logo'): self.lbl_logo.setPixmap(self.pix_logo.scaled(int(e*0.42), int(e*0.42), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.lbl_welcome.setStyleSheet(f"color: {COLOR_ESTETICO}; font-family: Kenao; font-size: {int(e*0.05)}px; background: transparent;")
        self.lbl_main.setStyleSheet(f"color: {COLOR_ESTETICO}; font-family: Kenao; font-size: {int(e*0.17)}px; font-weight: bold; background: transparent;")
        for i in reversed(range(self.lay_ini.count())): 
            item = self.lay_ini.itemAt(i)
            if item.widget(): item.widget().setParent(None)
            elif item.spacerItem(): self.lay_ini.removeItem(item)
        self.lay_ini.addStretch(4); self.lay_ini.addWidget(self.lbl_logo, 0, Qt.AlignmentFlag.AlignCenter); self.lay_ini.addSpacing(20)
        self.lay_ini.addWidget(self.lbl_welcome, 0, Qt.AlignmentFlag.AlignCenter); self.lay_ini.addWidget(self.lbl_main, 0, Qt.AlignmentFlag.AlignCenter)
        self.lay_ini.addStretch(3); self.btn_ini.setStyleSheet(st_btn); self.btn_pers.setStyleSheet(st_btn); self.btn_guardar.setStyleSheet(st_btn); self.btn_pausa.setStyleSheet(st_btn)
        self.lay_ini.addWidget(self.btn_ini, 0, Qt.AlignmentFlag.AlignCenter); self.lay_ini.addSpacing(40)
        self.lay_ini.addWidget(self.btn_pers, 0, Qt.AlignmentFlag.AlignCenter); self.lay_ini.addStretch(4)
        self.actualizar_botones()

class EstudiometroWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ratio = 1.0; self.txt = "00:00"
    def actualizar(self, ratio, t):
        self.ratio = ratio; self.txt = t; self.update()
    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        ancho, alto = self.width(), self.height(); d = min(ancho, alto) * 0.90
        r = QRectF((ancho-d)/2, (alto-d)/2, d, d)
        p.setPen(QPen(QColor(COLOR_ESTETICO), d*0.040, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawArc(r, 90*16, int(360*self.ratio*16))
        p.setFont(QFont("Kenao", int(d*0.20), QFont.Weight.Bold))
        p.setPen(QColor(COLOR_ESTETICO))
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.txt)

if __name__ == "__main__":
    app = QApplication(sys.argv); ex = StudPro(); sys.exit(app.exec())