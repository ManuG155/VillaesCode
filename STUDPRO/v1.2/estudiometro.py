import sys
import os
import ctypes
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
                             QPushButton, QFrame, QStackedWidget, QComboBox, QScrollArea,
                             QSizePolicy, QStyledItemDelegate, QListView, QSlider,
                             QGraphicsOpacityEffect, QStyleOptionComboBox, QStyle)
from PyQt6.QtCore import (Qt, QTimer, QRectF, pyqtSignal, QSize, QPropertyAnimation,
                          QEasingCurve, QRect, QPointF, pyqtProperty)
from PyQt6.QtGui import (QPainter, QColor, QPen, QImage, QFont, QFontDatabase,
                         QIcon, QPixmap, QFontMetrics)
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


class CenteredComboBox(QComboBox):
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect()
        painter.setBrush(QColor(0, 0, 0))
        painter.setPen(QPen(QColor(COLOR_ESTETICO), 2))
        painter.drawRoundedRect(r.adjusted(1,1,-1,-1), 10, 10)
        painter.setPen(QColor(COLOR_ESTETICO))
        font = QFont("Belgrano", 18)
        painter.setFont(font)
        painter.drawText(r, Qt.AlignmentFlag.AlignCenter, self.currentText())


class CenteredDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = Qt.AlignmentFlag.AlignCenter


class VolumeControlWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self._volumen_antes_mute = 80
        self._muteado = False
        self._slider_visible = False
        self.icon_size = 36
        self.slider_len = 120
        self.setStyleSheet("background: transparent; border: none;")
        self._build_ui()
        self._setup_animation()
        self.actualizar_icono()
        self._colapsar_inmediato()

    def _build_ui(self):
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(8, 8, 8, 8)
        self.lay.setSpacing(6)
        self.lay.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.btn_icon = QPushButton()
        self.btn_icon.setStyleSheet("QPushButton { border: none; background: transparent; }"
                                    "QPushButton:hover { background: rgba(219,192,150,20); border-radius: 18px; }")
        self.btn_icon.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_icon.clicked.connect(self.toggle_mute)
        self.lay.addWidget(self.btn_icon, 0, Qt.AlignmentFlag.AlignHCenter)
        self.slider_container = QWidget()
        self.slider_container.setStyleSheet("background: transparent;")
        sc_lay = QVBoxLayout(self.slider_container)
        sc_lay.setContentsMargins(0, 0, 0, 0)
        sc_lay.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.slider = QSlider(Qt.Orientation.Vertical)
        self.slider.setRange(0, 100)
        self.slider.setValue(80)
        self.slider.setInvertedAppearance(True)
        self.slider.setInvertedControls(True)
        self.slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self._aplicar_estilo_slider()
        self.slider.valueChanged.connect(self._on_volume_changed)
        sc_lay.addWidget(self.slider, 0, Qt.AlignmentFlag.AlignHCenter)
        self.lay.addWidget(self.slider_container, 0, Qt.AlignmentFlag.AlignHCenter)

    def _aplicar_estilo_slider(self):
        self.slider.setStyleSheet(f"""
            QSlider::groove:vertical {{
                background: rgba(219,192,150,60);
                width: 6px; border-radius: 3px;
            }}
            QSlider::handle:vertical {{
                background: {COLOR_ESTETICO};
                border: 2px solid {COLOR_ESTETICO};
                height: 16px; width: 16px;
                margin: 0 -5px; border-radius: 8px;
            }}
            QSlider::sub-page:vertical {{
                background: {COLOR_ESTETICO};
                width: 6px; border-radius: 3px;
            }}
        """)

    def _setup_animation(self):
        self.anim = QPropertyAnimation(self.slider_container, b"maximumHeight")
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.setDuration(250)

    def _colapsar_inmediato(self):
        self.slider_container.setMaximumHeight(0)
        self.slider_container.setVisible(False)
        self._slider_visible = False

    def _desplegar(self):
        if self._slider_visible: return
        self._slider_visible = True
        self.slider_container.setVisible(True)
        self.anim.stop()
        self.anim.setStartValue(0)
        self.anim.setEndValue(self.slider_len)
        self.anim.start()

    def _colapsar(self):
        if not self._slider_visible: return
        self._slider_visible = False
        self.anim.stop()
        self.anim.setStartValue(self.slider_container.height())
        self.anim.setEndValue(0)
        self.anim.finished.connect(self._ocultar_slider)
        self.anim.start()

    def _ocultar_slider(self):
        try: self.anim.finished.disconnect(self._ocultar_slider)
        except: pass
        if not self._slider_visible:
            self.slider_container.setVisible(False)

    def enterEvent(self, event):
        self._desplegar(); super().enterEvent(event)

    def leaveEvent(self, event):
        self._colapsar(); super().leaveEvent(event)

    def _on_volume_changed(self, val):
        try: pygame.mixer.music.set_volume(val / 100.0)
        except: pass
        try:
            parent = self.parent()
            if parent and hasattr(parent, "canal_alerta") and parent.canal_alerta:
                parent.canal_alerta.set_volume(val / 100.0)
        except:
            pass
        if val > 0:
            self._muteado = False
            self._volumen_antes_mute = val
        else:
            self._muteado = True
        self.actualizar_icono()

    def toggle_mute(self):
        if self._muteado or self.slider.value() == 0:
            self.slider.setValue(self._volumen_antes_mute if self._volumen_antes_mute > 0 else 80)
            self._muteado = False
        else:
            self._volumen_antes_mute = self.slider.value()
            self.slider.setValue(0)
            self._muteado = True
        self.actualizar_icono()

    def actualizar_icono(self):
        es_mute = self._muteado or self.slider.value() == 0
        nombre = "altavoz_mute.png" if es_mute else "altavoz_sonido.png"
        ruta = resource_path(nombre)
        if os.path.exists(ruta):
            pix = QPixmap(ruta).scaled(self.icon_size, self.icon_size,
                Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.btn_icon.setIcon(QIcon(pix))
            self.btn_icon.setIconSize(QSize(self.icon_size, self.icon_size))
        self.btn_icon.setFixedSize(self.icon_size + 8, self.icon_size + 8)

    def actualizar_tamano(self, icon_size, slider_len):
        self.icon_size = icon_size
        self.slider_len = slider_len
        self.slider.setFixedHeight(slider_len)
        self.actualizar_icono()
        if self._slider_visible:
            self.slider_container.setMaximumHeight(slider_len)


class StudProSwitch(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, parent=None, checked=True):
        super().__init__(parent)
        self._checked = checked
        self._thumb_pos = 1.0 if checked else 0.0
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(74, 38)
        self.anim = QPropertyAnimation(self, b"thumb_pos")
        self.anim.setDuration(200)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def isChecked(self):
        return self._checked

    def setChecked(self, checked, animated=False):
        checked = bool(checked)
        if self._checked == checked and not animated:
            self.update()
            return
        self._checked = checked
        destino = 1.0 if checked else 0.0
        self.anim.stop()
        if animated:
            self.anim.setStartValue(self._thumb_pos)
            self.anim.setEndValue(destino)
            self.anim.start()
        else:
            self._thumb_pos = destino
            self.update()
        self.toggled.emit(self._checked)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self._checked, animated=True)
            event.accept()
            return
        super().mousePressEvent(event)

    def get_thumb_pos(self):
        return self._thumb_pos

    def set_thumb_pos(self, value):
        self._thumb_pos = max(0.0, min(1.0, float(value)))
        self.update()

    thumb_pos = pyqtProperty(float, fget=get_thumb_pos, fset=set_thumb_pos)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)
        color_fondo = QColor(COLOR_ESTETICO if self._checked else "#333333")
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color_fondo)
        painter.drawRoundedRect(rect, rect.height() / 2, rect.height() / 2)

        margen = 4
        diametro = rect.height() - (margen * 2)
        recorrido = rect.width() - diametro - (margen * 2)
        x_thumb = rect.x() + margen + (recorrido * self._thumb_pos)
        thumb_rect = QRectF(x_thumb, rect.y() + margen, diametro, diametro)
        painter.setBrush(QColor("#151515"))
        painter.drawEllipse(thumb_rect)


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
            combo = CenteredComboBox()
            combo.setStyleSheet(f"CenteredComboBox {{ min-height: 40px; }} CenteredComboBox::drop-down {{ border: none; width: 0px; }}")
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
        self.img_inicio   = QImage(resource_path("inicio.jpg"))
        self.img_bonita   = QImage(resource_path("imagen_bonita.jpg"))
        self.img_descanso = QImage(resource_path("fondo_descanso.jpg"))
        self.num_pomodoros = 1
        self.config_actual = [{"estudio": 55, "descanso": 5} for _ in range(10)]
        self.alerta_activa = True
        self.sonido_alerta = None
        self.canal_alerta = None
        self._inicializar_audio_alerta()
        self.estado = "inicio"; self.pausado = False; self.w_lista = []
        self.init_ui()
        self.timer = QTimer(self); self.timer.timeout.connect(self.motor)
        self.showMaximized()

    def _inicializar_audio_alerta(self):
        try:
            pygame.mixer.set_num_channels(8)
            ruta_alerta = resource_path("alerta.mp3")
            if os.path.exists(ruta_alerta):
                self.sonido_alerta = pygame.mixer.Sound(ruta_alerta)
                self.canal_alerta = pygame.mixer.Channel(1)
        except:
            self.sonido_alerta = None
            self.canal_alerta = None

    def _posicionar_vol(self):
        """Posiciona y muestra el widget de volumen. Llamado tras arrancar()."""
        w = self.width(); h = self.height(); e = min(w, h)
        icon_size  = max(28, int(e * 0.032))
        slider_len = max(80, int(e * 0.18))
        self.vol_widget.actualizar_tamano(icon_size, slider_len)
        margen    = max(10, int(e * 0.012))
        ancho_vol = icon_size + 24
        alto_vol  = icon_size + 24 + slider_len + 20
        self.vol_widget.setGeometry(w - ancho_vol - margen, margen, ancho_vol, alto_vol)
        self.vol_widget.setVisible(True)
        self.vol_widget.raise_()

    def _crear_toggle_alerta(self):
        self.box_alerta_cfg = QWidget(self.capa_cfg)
        self.box_alerta_cfg.setStyleSheet("background: transparent;")
        lay_alerta = QHBoxLayout(self.box_alerta_cfg)
        lay_alerta.setContentsMargins(0, 0, 0, 0)
        lay_alerta.setSpacing(14)
        self.lbl_alerta_cfg = QLabel("¿Te aviso cuando acabe tu sesión?")
        self.lbl_alerta_cfg.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        self.lbl_alerta_cfg.setStyleSheet(f"color: {COLOR_ESTETICO}; font-family: Belgrano; background: transparent;")
        self.switch_alerta = StudProSwitch(self.box_alerta_cfg, checked=self.alerta_activa)
        self.switch_alerta.toggled.connect(self._actualizar_alerta_activa)
        lay_alerta.addWidget(self.lbl_alerta_cfg)
        lay_alerta.addWidget(self.switch_alerta, 0, Qt.AlignmentFlag.AlignVCenter)
        self.box_alerta_cfg.raise_()

    def _actualizar_alerta_activa(self, estado):
        self.alerta_activa = bool(estado)

    def _posicionar_toggle_alerta(self):
        if not hasattr(self, "box_alerta_cfg"):
            return
        ancho_cfg = self.capa_cfg.width()
        alto_cfg = self.capa_cfg.height()
        escala = min(ancho_cfg, alto_cfg)
        margen_top = max(18, int(alto_cfg * 0.035))
        margen_der = max(20, int(ancho_cfg * 0.03))
        font_alerta = max(12, int(escala * 0.026))
        ancho_label = min(max(180, int(ancho_cfg * 0.24)), 330)
        self.lbl_alerta_cfg.setFixedWidth(ancho_label)
        self.lbl_alerta_cfg.setWordWrap(True)
        self.lbl_alerta_cfg.setStyleSheet(
            f"color: {COLOR_ESTETICO}; font-family: Belgrano; font-size: {font_alerta}px; background: transparent;"
        )
        switch_w = max(64, int(escala * 0.11))
        switch_h = max(32, int(escala * 0.056))
        self.switch_alerta.setFixedSize(switch_w, switch_h)
        self.box_alerta_cfg.adjustSize()
        x = ancho_cfg - self.box_alerta_cfg.width() - margen_der
        self.box_alerta_cfg.move(max(10, x), margen_top)
        self.box_alerta_cfg.raise_()

    def _reproducir_ambiente(self, file, loop=-1):
        try:
            path = resource_path(file)
            if os.path.exists(path):
                pygame.mixer.music.stop()
                pygame.mixer.music.load(path)
                pygame.mixer.music.play(loop, fade_ms=250)
                pygame.mixer.music.set_volume(self.vol_widget.slider.value() / 100.0)
        except:
            pass

    def _reproducir_alerta_superpuesta(self):
        if not self.alerta_activa or not self.sonido_alerta:
            return
        try:
            volumen = self.vol_widget.slider.value() / 100.0 if hasattr(self, "vol_widget") else 0.8
            if self.canal_alerta:
                self.canal_alerta.set_volume(volumen)
                self.canal_alerta.play(self.sonido_alerta)
            else:
                canal = self.sonido_alerta.play()
                if canal:
                    canal.set_volume(volumen)
        except:
            pass

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
        self._crear_toggle_alerta()
        self.stacked.addWidget(self.capa_cfg)

        # --- PANTALLA MOTOR ---
        self.capa_mot = QFrame()
        lay_m = QVBoxLayout(self.capa_mot); lay_m.setContentsMargins(20,20,20,20)
        self.lbl_f = QLabel(""); self.lbl_f.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.vis = EstudiometroWidget(self)
        self.vis.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.btn_pausa    = QPushButton("PAUSA");    self.btn_pausa.clicked.connect(self.toggle_pausa)
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

        # vol_widget hijo de self, oculto hasta arrancar()
        self.vol_widget = VolumeControlWidget(self)
        self.vol_widget.setVisible(False)

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
            base = f"border-radius: {tam//2}px; font-family: Belgrano; font-size: {font_s}px; font-weight: bold;"
            if i < self.num_pomodoros:
                b.setStyleSheet(f"QPushButton {{ background-color: {COLOR_ESTETICO}; color: black; border: 2px solid {COLOR_ESTETICO}; {base} }} QPushButton:hover {{ background-color: white; }}")
            else:
                b.setStyleSheet(f"QPushButton {{ background-color: transparent; color: {COLOR_ESTETICO}; border: 2px solid {COLOR_ESTETICO}; {base} }} QPushButton:hover {{ background-color: {COLOR_ESTETICO}; color: black; }}")

    def play_sound(self, file, loop=0):
        try:
            pygame.mixer.music.stop()
            path = resource_path(file)
            if os.path.exists(path):
                pygame.mixer.music.load(path)
                pygame.mixer.music.play(loop)
                pygame.mixer.music.set_volume(self.vol_widget.slider.value() / 100.0)
        except: pass

    def toggle_pausa(self):
        if not self.pausado:
            self.timer.stop(); pygame.mixer.music.pause()
            if self.canal_alerta and self.canal_alerta.get_busy(): self.canal_alerta.pause()
            self.btn_pausa.setText("REANUDAR")
        else:
            self.timer.start(50); pygame.mixer.music.unpause()
            if self.canal_alerta: self.canal_alerta.unpause()
            self.btn_pausa.setText("PAUSA")
        self.pausado = not self.pausado

    def volver_menu(self):
        self.timer.stop(); pygame.mixer.music.stop()
        if self.canal_alerta: self.canal_alerta.stop()
        self.pausado = False; self.btn_pausa.setText("PAUSA")
        self.estado = "inicio"
        self.vol_widget.setVisible(False)
        self.stacked.setCurrentIndex(0)

    def arrancar(self):
        self.fases = []
        for i in range(self.num_pomodoros):
            config = self.config_actual[i]
            self.fases.append((f"ESTUDIO {i+1}", config["estudio"], "estudio"))
            self.fases.append((f"DESCANSO {i+1}", config["descanso"], "descanso"))
        self.idx = 0; self.estado = "study"
        self.stacked.setCurrentIndex(2)
        # Posicionar y mostrar volumen ahora que el motor está visible
        self._posicionar_vol()
        self.next_fase()

    def next_fase(self):
        if self.idx < len(self.fases):
            n, m, t = self.fases[self.idx]; self.total_ms = m*60*1000; self.rem_ms = self.total_ms; self.idx += 1
            self.lbl_f.setText(n)
            self.timer.start(50)
            if t == "estudio": self._reproducir_ambiente("ruido_blanco.mp3", -1)
            else: self._reproducir_ambiente("piano.mp3", -1)
            if self.idx > 1: self._reproducir_alerta_superpuesta()
        else:
            pygame.mixer.music.stop()
            if self.alerta_activa: self._reproducir_alerta_superpuesta()
            self.vol_widget.setVisible(False); self.stacked.setCurrentIndex(0); self.estado = "inicio"

    def motor(self):
        if self.rem_ms > 0:
            self.rem_ms -= 50; seg_t = self.rem_ms // 1000; m, s = divmod(seg_t, 60)
            self.vis.actualizar(self.rem_ms/self.total_ms, f"{m:02d}", f"{s:02d}")
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

        # Reubicar volumen si está visible
        if self.vol_widget.isVisible():
            icon_size  = max(28, int(e * 0.032))
            slider_len = max(80, int(e * 0.18))
            self.vol_widget.actualizar_tamano(icon_size, slider_len)
            margen    = max(10, int(e * 0.012))
            ancho_vol = icon_size + 24
            alto_vol  = icon_size + 24 + slider_len + 20
            self.vol_widget.setGeometry(w - ancho_vol - margen, margen, ancho_vol, alto_vol)
            self.vol_widget.raise_()

        self._posicionar_toggle_alerta()
        self.actualizar_botones()


class EstudiometroWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ratio = 1.0
        self.mins = "00"; self.segs = "00"
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def actualizar(self, ratio, mins, segs):
        self.ratio = ratio; self.mins = mins; self.segs = segs; self.update()

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        ancho, alto = self.width(), self.height()
        d = min(ancho, alto) * 0.85
        cx = ancho / 2; cy = alto / 2

        # Círculo de progreso
        r = QRectF(cx - d/2, cy - d/2, d, d)
        p.setPen(QPen(QColor(COLOR_ESTETICO), d*0.038, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawArc(r, 90*16, int(360*self.ratio*16))

        font_size = max(12, int(d * 0.18))
        font = QFont("Kenao", font_size, QFont.Weight.Bold)
        p.setFont(font)
        p.setPen(QColor(COLOR_ESTETICO))
        fm = QFontMetrics(font)

        # Ancho fijo usando "00" como referencia para evitar desplazamiento
        ancho_ref  = fm.horizontalAdvance("00")
        ancho_sep  = fm.horizontalAdvance(":")
        ancho_total = ancho_ref * 2 + ancho_sep
        x_inicio = cx - ancho_total / 2

        # Dibujar MM centrado en su bloque fijo
        rect_mins = QRect(int(x_inicio), int(cy - fm.height()/2), ancho_ref, fm.height())
        p.drawText(rect_mins, Qt.AlignmentFlag.AlignCenter, self.mins)

        # Dibujar separador ":"
        rect_sep = QRect(int(x_inicio + ancho_ref), int(cy - fm.height()/2), ancho_sep, fm.height())
        p.drawText(rect_sep, Qt.AlignmentFlag.AlignCenter, ":")

        # Dibujar SS centrado en su bloque fijo
        rect_segs = QRect(int(x_inicio + ancho_ref + ancho_sep), int(cy - fm.height()/2), ancho_ref, fm.height())
        p.drawText(rect_segs, Qt.AlignmentFlag.AlignCenter, self.segs)


if __name__ == "__main__":
    app = QApplication(sys.argv); ex = StudPro(); sys.exit(app.exec())
