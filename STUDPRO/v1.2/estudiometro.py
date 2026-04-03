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
        layout = QVBoxLayout(self); layout.setContentsMargins(20, 10, 20, 14); layout.setSpacing(6)

        header = QHBoxLayout(); header.addStretch(1)
        self.titulo = QLabel(f"POMODORO {numero}")
        self.titulo.setStyleSheet(f"border: none; background: transparent; color: {COLOR_ESTETICO}; font-family: Belgrano; font-size: 22px; font-weight: bold;")
        self.titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(self.titulo); header.addStretch(1)
        self.btn_trash = QPushButton(); self.btn_trash.setFixedSize(40, 40)
        ruta_trash = resource_path("trash.png")
        if os.path.exists(ruta_trash):
            self.btn_trash.setIcon(QIcon(ruta_trash)); self.btn_trash.setIconSize(QSize(28, 28))
        self.btn_trash.setStyleSheet("QPushButton { border: none; background: transparent; } QPushButton:hover { background-color: rgba(255,60,60,50); border-radius: 10px; }")
        self.btn_trash.clicked.connect(lambda: self.deleteRequested.emit(self.numero_actual))
        header.addWidget(self.btn_trash); layout.addLayout(header)

        controles = QHBoxLayout(); controles.setSpacing(16); controles.setContentsMargins(0, 0, 0, 0)
        for label_text, def_val in [("Estudio", estudio_def), ("Descanso", descanso_def)]:
            col = QVBoxLayout(); col.setSpacing(6)
            lbl = QLabel(label_text)
            lbl.setStyleSheet("border: none; background: transparent; color: white; font-family: Belgrano; font-size: 18px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            combo = QComboBox()
            combo.setStyleSheet(f"QComboBox {{ background-color: black; color: {COLOR_ESTETICO}; border: 2px solid {COLOR_ESTETICO}; border-radius: 10px; padding: 6px; font-family: Belgrano; font-size: 18px; min-height: 40px; }} QComboBox::drop-down {{ border: none; width: 0px; }}")
            view = QListView()
            view.setStyleSheet(f"background-color: black; color: {COLOR_ESTETICO}; selection-background-color: {COLOR_ESTETICO}; selection-foreground-color: black; font-family: Belgrano; font-size: 18px;")
            combo.setView(view); combo.setItemDelegate(CenteredDelegate())
            combo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            combo.addItems([f"{m} min" for m in range(5, 65, 5)])
            combo.setCurrentText(f"{def_val} min")
            combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            col.addWidget(lbl, 0, Qt.AlignmentFlag.AlignCenter)
            col.addWidget(combo)
            controles.addLayout(col, 1)
            if label_text == "Estudio": self.combo_est = combo
            else: self.combo_des = combo
        layout.addLayout(controles)

class StudPro(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StudPro")
        self.setMinimumSize(400, 300)
        QFontDatabase.addApplicationFont(resource_path("Kenao.otf"))
        QFontDatabase.addApplicationFont(resource_path("Belgrano-Regular.otf"))
        self.img_inicio  = QImage(resource_path("inicio.jpg"))
        self.img_bonita  = QImage(resource_path("imagen_bonita.jpg"))
        self.img_descanso = QImage(resource_path("fondo_descanso.jpg"))
        self.num_pomodoros = 1
        self.config_actual = [{"estudio": 55, "descanso": 5} for _ in range(10)]
        self.estado = "inicio"; self.pausado = False; self.w_lista = []
        self.init_ui()
        self.timer = QTimer(self); self.timer.timeout.connect(self.motor)
        self.showMaximized()

    def init_ui(self):
        self.stacked = QStackedWidget(self)
        layout_main = QVBoxLayout(self); layout_main.setContentsMargins(0,0,0,0)
        layout_main.addWidget(self.stacked)

        # --- PANTALLA INICIO ---
        self.capa_ini = QFrame(); self.lay_ini = QVBoxLayout(self.capa_ini)
        self.lbl_logo = QLabel(); self.lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ruta_logo = resource_path("logo.png")
        if os.path.exists(ruta_logo): self.pix_logo = QPixmap(ruta_logo)
        self.lbl_welcome = QLabel("BIENVENID@ A")
        self.lbl_welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_main = QLabel("STUDPRO")
        self.lbl_main.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.btn_ini  = QPushButton("INICIAR")
        self.btn_pers = QPushButton("PERSONALIZAR")
        self.btn_ini.clicked.connect(self.arrancar)
        self.btn_pers.clicked.connect(lambda: self.stacked.setCurrentIndex(1))
        self.stacked.addWidget(self.capa_ini)

        # --- PANTALLA CONFIGURACIÓN ---
        self.capa_cfg = QFrame()
        self.lay_cfg_h = QHBoxLayout(self.capa_cfg); self.lay_cfg_h.setSpacing(0)

        self.panel_lat = QFrame()
        self.panel_lat.setStyleSheet(f"background-color: {COLOR_NEGRO_ALPHA}; border-right: 2px solid {COLOR_ESTETICO};")
        lay_lat_outer = QVBoxLayout(self.panel_lat); lay_lat_outer.setContentsMargins(0,0,0,0); lay_lat_outer.setSpacing(0)
        self.lbl_q = QLabel("Cantidad de\nPomodoros:")
        self.lbl_q.setStyleSheet(f"color: {COLOR_ESTETICO}; font-family: Belgrano; font-size: 18px; font-weight: bold; background: transparent;")
        self.lbl_q.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay_lat_outer.addSpacing(15); lay_lat_outer.addWidget(self.lbl_q); lay_lat_outer.addSpacing(10)
        scroll_lat = QScrollArea(); scroll_lat.setWidgetResizable(True)
        scroll_lat.setStyleSheet("background: transparent; border: none;")
        scroll_lat.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        cont_btns = QWidget(); cont_btns.setStyleSheet("background: transparent;")
        self.lay_btns = QVBoxLayout(cont_btns)
        self.lay_btns.setSpacing(12); self.lay_btns.setContentsMargins(10,10,10,10)
        self.lay_btns.addStretch(1)
        self.btns_n = []
        for i in range(1, 11):
            b = QPushButton(str(i))
            b.clicked.connect(lambda ch, n=i: self.set_pomos(n))
            self.lay_btns.addWidget(b, 0, Qt.AlignmentFlag.AlignCenter)
            self.btns_n.append(b)
        self.lay_btns.addStretch(1)
        scroll_lat.setWidget(cont_btns)
        lay_lat_outer.addWidget(scroll_lat); lay_lat_outer.addSpacing(10)

        panel_der = QVBoxLayout(); panel_der.setContentsMargins(30,30,30,30)
        self.tit_cfg = QLabel("CONFIGURACIÓN")
        self.tit_cfg.setStyleSheet(f"color: {COLOR_ESTETICO}; font-family: Kenao; font-size: 50px; background: transparent; font-weight: bold;")
        self.tit_cfg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        panel_der.addWidget(self.tit_cfg); panel_der.addSpacing(15)
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: transparent; border: none;")
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.cont = QWidget(); self.cont.setStyleSheet("background: transparent;")
        self.lay_p = QVBoxLayout(self.cont); self.lay_p.setSpacing(20)
        self.scroll.setWidget(self.cont); panel_der.addWidget(self.scroll)
        panel_der.addSpacing(15)
        self.btn_guardar = QPushButton("GUARDAR")
        self.btn_guardar.clicked.connect(self.guardar_y_volver)
        panel_der.addWidget(self.btn_guardar, 0, Qt.AlignmentFlag.AlignCenter)
        self.lay_cfg_h.addWidget(self.panel_lat); self.lay_cfg_h.addLayout(panel_der)
        self.stacked.addWidget(self.capa_cfg)

        # --- PANTALLA MOTOR ---
        self.capa_mot = QFrame()
        lay_m = QVBoxLayout(self.capa_mot); lay_m.setContentsMargins(20,20,20,20)
        self.lbl_f = QLabel(""); self.lbl_f.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.vis = EstudiometroWidget(self)
        self.vis.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.btn_pausa   = QPushButton("PAUSA");    self.btn_pausa.clicked.connect(self.toggle_pausa)
        self.btn_regresar = QPushButton("REGRESAR"); self.btn_regresar.clicked.connect(self.volver_menu)
        self.btn_row_widget = QWidget()
        btn_row = QHBoxLayout(self.btn_row_widget)
        btn_row.addStretch(1); btn_row.addWidget(self.btn_pausa)
        btn_row.addSpacing(40); btn_row.addWidget(self.btn_regresar); btn_row.addStretch(1)
        lay_m.addStretch(1)
        lay_m.addWidget(self.lbl_f, 0, Qt.AlignmentFlag.AlignCenter)
        lay_m.addWidget(self.vis, 10)
        lay_m.addWidget(self.btn_row_widget, 0, Qt.AlignmentFlag.AlignCenter)
        lay_m.addStretch(1)
        self.stacked.addWidget(self.capa_mot)
        self.set_pomos(1)

    def set_pomos(self, n):
        for i, w in enumerate(self.w_lista):
            self.config_actual[i] = {
                "estudio":  int(w.combo_est.currentText().split(" ")[0]),
                "descanso": int(w.combo_des.currentText().split(" ")[0])
            }
        self.num_pomodoros = max(1, n)
        while self.lay_p.count():
            item = self.lay_p.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self.lay_p.addStretch(1); self.w_lista = []
        for i in range(self.num_pomodoros):
            w = ItemConfiguracion(i+1, self.config_actual[i]["estudio"], self.config_actual[i]["descanso"])
            w.deleteRequested.connect(self.eliminar_pomodoro)
            self.lay_p.addWidget(w); self.w_lista.append(w)
        self.lay_p.addStretch(1); self.actualizar_botones()

    def guardar_y_volver(self):
        for i, w in enumerate(self.w_lista):
            self.config_actual[i] = {"estudio": int(w.combo_est.currentText().split(" ")[0]),
                                     "descanso": int(w.combo_des.currentText().split(" ")[0])}
        self.stacked.setCurrentIndex(0)

    def eliminar_pomodoro(self, n_eliminar):
        if self.num_pomodoros > 1:
            idx = n_eliminar - 1
            for i in range(idx, 9): self.config_actual[i] = self.config_actual[i+1]
            self.config_actual[9] = {"estudio": 55, "descanso": 5}
            self.set_pomos(self.num_pomodoros - 1)

    def actualizar_botones(self):
        tam = max(40, min(60, int(self.height() * 0.06)))
        font_s = max(14, int(tam * 0.40))
        for i, b in enumerate(self.btns_n):
            b.setFixedSize(tam, tam)
            estilo_base = f"border-radius: {tam//2}px; font-family: Belgrano; font-size: {font_s}px; font-weight: bold;"
            if i < self.num_pomodoros:
                b.setStyleSheet(f"QPushButton {{ background-color: {COLOR_ESTETICO}; color: black; border: 2px solid {COLOR_ESTETICO}; {estilo_base} }} QPushButton:hover {{ background-color: white; }}")
            else:
                b.setStyleSheet(f"QPushButton {{ background-color: transparent; color: {COLOR_ESTETICO}; border: 2px solid {COLOR_ESTETICO}; {estilo_base} }} QPushButton:hover {{ background-color: {COLOR_ESTETICO}; color: black; }}")

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

    def volver_menu(self):
        self.timer.stop(); pygame.mixer.music.stop()
        self.pausado = False; self.btn_pausa.setText("PAUSA")
        self.estado = "inicio"; self.stacked.setCurrentIndex(0)

    def arrancar(self):
        self.fases = []
        for i in range(self.num_pomodoros):
            config = self.config_actual[i]
            self.fases.append((f"ESTUDIO {i+1}", config["estudio"], "estudio"))
            self.fases.append((f"DESCANSO {i+1}", config["descanso"], "descanso"))
        self.idx = 0; self.estado = "study"; self.stacked.setCurrentIndex(2); self.next_fase()

    def next_fase(self):
        if self.idx < len(self.fases):
            if self.idx > 0: self.play_sound("alerta.mp3")
            n, m, t = self.fases[self.idx]; self.total_ms = m*60*1000; self.rem_ms = self.total_ms; self.idx += 1
            self.lbl_f.setText(n)
            self.timer.start(50)
            if t == "estudio": self.play_sound("ruido_blanco.mp3", -1)
            else: self.play_sound("piano.mp3", -1)
        else: self.play_sound("alerta.mp3"); self.stacked.setCurrentIndex(0); self.estado = "inicio"

    def motor(self):
        if self.rem_ms > 0:
            self.rem_ms -= 50; seg_t = self.rem_ms // 1000; m, s = divmod(seg_t, 60)
            self.vis.actualizar(self.rem_ms/self.total_ms, f"{m:02}:{s:02}")
        else: self.timer.stop(); self.next_fase()

    def paintEvent(self, event):
        pa = QPainter(self); img = self.img_inicio
        if self.stacked.currentIndex() == 1: img = self.img_bonita
        elif self.estado == "study": img = self.img_bonita if "ESTUDIO" in self.lbl_f.text() else self.img_descanso
        if not img.isNull(): pa.drawImage(0, 0, img.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))

    def resizeEvent(self, event):
        w = self.width(); h = self.height(); e = min(w, h)

        mostrar_panel_lat  = w >= 700
        mostrar_tit_cfg    = h >= 400
        mostrar_logo       = e >= 500
        mostrar_textos_ini = e >= 380
        mostrar_btns_ini   = e >= 300
        mostrar_lbl_fase   = e >= 280
        mostrar_btns_mot   = e >= 350

        font_btn  = max(14, int(e * 0.038))
        min_w_btn = max(160, int(e * 0.22))
        pad_btn   = max(12, int(e * 0.018))
        st_btn = (f"QPushButton {{ background-color: transparent; color: {COLOR_ESTETICO}; "
                  f"border: 3px solid {COLOR_ESTETICO}; border-radius: 20px; padding: {pad_btn}px; "
                  f"font-family: Kenao; font-size: {font_btn}px; min-width: {min_w_btn}px; }} "
                  f"QPushButton:hover {{ background-color: {COLOR_ESTETICO}; color: black; }}")

        if mostrar_panel_lat:
            ancho_lat = max(130, int(w * 0.15))
            self.panel_lat.setFixedWidth(ancho_lat)
            self.panel_lat.setVisible(True)
            font_q = max(12, int(ancho_lat * 0.11))
            self.lbl_q.setStyleSheet(f"color: {COLOR_ESTETICO}; font-family: Belgrano; font-size: {font_q}px; font-weight: bold; background: transparent;")
        else:
            self.panel_lat.setVisible(False)

        font_tit_cfg = max(22, int(e * 0.045))
        self.tit_cfg.setStyleSheet(f"color: {COLOR_ESTETICO}; font-family: Kenao; font-size: {font_tit_cfg}px; background: transparent; font-weight: bold;")
        self.tit_cfg.setVisible(mostrar_tit_cfg)

        font_fase = max(22, int(e * 0.058))
        self.lbl_f.setStyleSheet(f"color: {COLOR_ESTETICO}; font-family: Kenao; font-size: {font_fase}px; font-weight: bold; background: transparent;")
        self.lbl_f.setVisible(mostrar_lbl_fase)
        self.btn_row_widget.setVisible(mostrar_btns_mot)

        if hasattr(self, 'pix_logo'):
            tam_logo = max(100, int(e * 0.32))
            self.lbl_logo.setPixmap(self.pix_logo.scaled(tam_logo, tam_logo,
                Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

        font_welcome = max(14, int(e * 0.040))
        font_main    = max(30, int(e * 0.13))
        self.lbl_welcome.setStyleSheet(f"color: {COLOR_ESTETICO}; font-family: Kenao; font-size: {font_welcome}px; background: transparent;")
        self.lbl_main.setStyleSheet(f"color: {COLOR_ESTETICO}; font-family: Kenao; font-size: {font_main}px; font-weight: bold; background: transparent;")

        for btn in [self.btn_ini, self.btn_pers, self.btn_guardar, self.btn_pausa, self.btn_regresar]:
            btn.setStyleSheet(st_btn)

        for i in reversed(range(self.lay_ini.count())):
            item = self.lay_ini.itemAt(i)
            if item.widget(): item.widget().setParent(None)
            elif item.spacerItem(): self.lay_ini.removeItem(item)
        self.lay_ini.addStretch(3)
        if mostrar_logo:
            self.lay_ini.addWidget(self.lbl_logo, 0, Qt.AlignmentFlag.AlignCenter)
            self.lay_ini.addSpacing(12)
        if mostrar_textos_ini:
            self.lay_ini.addWidget(self.lbl_welcome, 0, Qt.AlignmentFlag.AlignCenter)
            self.lay_ini.addWidget(self.lbl_main, 0, Qt.AlignmentFlag.AlignCenter)
        self.lay_ini.addStretch(2)
        if mostrar_btns_ini:
            self.lay_ini.addWidget(self.btn_ini,  0, Qt.AlignmentFlag.AlignCenter)
            self.lay_ini.addSpacing(28)
            self.lay_ini.addWidget(self.btn_pers, 0, Qt.AlignmentFlag.AlignCenter)
        self.lay_ini.addStretch(3)

        self.actualizar_botones()

class EstudiometroWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ratio = 1.0; self.txt = "00:00"
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def actualizar(self, ratio, t):
        self.ratio = ratio; self.txt = t; self.update()

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        ancho, alto = self.width(), self.height()
        d = min(ancho, alto) * 0.85
        r = QRectF((ancho-d)/2, (alto-d)/2, d, d)
        p.setPen(QPen(QColor(COLOR_ESTETICO), d*0.038, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawArc(r, 90*16, int(360*self.ratio*16))
        font_size = max(12, int(d * 0.18))
        p.setFont(QFont("Kenao", font_size, QFont.Weight.Bold))
        p.setPen(QColor(COLOR_ESTETICO))
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.txt)

if __name__ == "__main__":
    app = QApplication(sys.argv); ex = StudPro(); sys.exit(app.exec())