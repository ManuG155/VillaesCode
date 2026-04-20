"""
╔══════════════════════════════════════════════════════════╗
║       YouTube Transcript Extractor — v1.3                ║
║       Stack: CustomTkinter · youtube-transcript-api      ║
║              yt-dlp · pyperclip                          ║
╚══════════════════════════════════════════════════════════╝
"""

import re
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
import pyperclip
import yt_dlp
from youtube_transcript_api import (
    NoTranscriptFound,
    TranscriptsDisabled,
    YouTubeTranscriptApi,
)

# ──────────────────────────────────────────────────────────
#  Configuración global de tema
# ──────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Paleta de colores personalizados
COLORS = {
    "bg_primary":    "#0f0f0f",
    "bg_secondary":  "#1a1a1a",
    "bg_card":       "#1e1e1e",
    "accent":        "#ff4444",
    "accent_hover":  "#cc2222",
    "text_primary":  "#f5f5f5",
    "text_muted":    "#888888",
    "separator":     "#2e2e2e",
    "success":       "#22c55e",
    "entry_bg":      "#141414",
}


# ══════════════════════════════════════════════════════════
#  Utilidades de extracción
# ══════════════════════════════════════════════════════════

def extract_video_id(url: str) -> str | None:
    """Extrae el ID de 11 caracteres de cualquier variante de URL de YouTube."""
    patterns = [
        r"(?:v=)([0-9A-Za-z_-]{11})",
        r"(?:youtu\.be/)([0-9A-Za-z_-]{11})",
        r"(?:embed/)([0-9A-Za-z_-]{11})",
        r"(?:shorts/)([0-9A-Za-z_-]{11})",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


def get_video_title(video_id: str) -> str:
    """Obtiene el título del vídeo usando yt-dlp (silencioso)."""
    try:
        opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "extract_flat": True,
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(
                f"https://www.youtube.com/watch?v={video_id}", download=False
            )
            return info.get("title", "Título no disponible")
    except Exception:
        return "Título no disponible"


def format_transcript(entries: list, include_timestamps: bool) -> str:
    """Convierte la lista de entradas en texto formateado.

    CAMBIO v1.2: Sin marcas de tiempo, cada entrada va en su propia línea
    (antes se unían con espacio). El CTkTextbox se encarga del wrap.
    """
    if include_timestamps:
        lines = []
        for e in entries:
            total_secs = int(e["start"])
            m, s = divmod(total_secs, 60)
            h, m = divmod(m, 60)
            ts = f"[{h:02d}:{m:02d}:{s:02d}]" if h else f"[{m:02d}:{s:02d}]"
            text = e["text"].replace("\n", " ").strip()
            lines.append(f"{ts} {text}")
        return "\n".join(lines)
    else:
        # Cada entrada en su propia línea; el textbox hace el wrap automático
        return "\n".join(e["text"].replace("\n", " ").strip() for e in entries)


def format_txt_file(title: str, transcript: str) -> str:
    """Formatea el contenido para guardar como .txt plano."""
    border = "═" * 64
    title_block = f"{border}\n  {title.upper()}\n{border}\n\n"
    return title_block + transcript


def format_md_file(title: str, transcript: str) -> str:
    """Formatea el contenido para guardar como Markdown.

    NUEVO v1.2: título centrado con etiqueta HTML embebida en Markdown.
    """
    header = f'<h1 align="center">**{title}**</h1>\n\n'
    return header + transcript


def safe_filename(title: str, max_len: int = 60) -> str:
    """Sanitiza el título para usarlo como nombre de archivo."""
    sanitized = re.sub(r'[<>:"/\\|?*\n\r\t]', "", title)
    return sanitized[:max_len].strip()


# ══════════════════════════════════════════════════════════
#  Menú contextual reutilizable para CTkEntry
# ══════════════════════════════════════════════════════════

class ContextMenu:
    """
    Menú contextual de clic derecho con opciones Cortar / Copiar / Pegar.
    Compatible con CTkEntry (que internamente usa tk.Entry).
    """

    def __init__(self, entry_widget: ctk.CTkEntry, root: tk.Tk):
        self._entry = entry_widget
        self._menu = tk.Menu(root, tearoff=0, bg="#1e1e1e", fg="#f5f5f5",
                             activebackground="#ff4444", activeforeground="#f5f5f5",
                             font=("Segoe UI", 10), bd=0, relief="flat")
        self._menu.add_command(label="✂  Cortar",  command=self._cut)
        self._menu.add_command(label="⎘  Copiar",  command=self._copy)
        self._menu.add_separator()
        self._menu.add_command(label="⬇  Pegar",   command=self._paste)

        entry_widget.bind("<Button-3>", self._show)
        try:
            entry_widget._entry.bind("<Button-3>", self._show)
        except AttributeError:
            pass

    def _show(self, event):
        try:
            self._menu.tk_popup(event.x_root, event.y_root)
        finally:
            self._menu.grab_release()

    def _get_inner(self):
        """Devuelve el widget tk.Entry interno de CTkEntry."""
        try:
            return self._entry._entry
        except AttributeError:
            return self._entry

    def _cut(self):
        inner = self._get_inner()
        try:
            sel = inner.selection_get()
            pyperclip.copy(sel)
            inner.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            pass

    def _copy(self):
        inner = self._get_inner()
        try:
            sel = inner.selection_get()
            pyperclip.copy(sel)
        except tk.TclError:
            pyperclip.copy(inner.get())

    def _paste(self):
        inner = self._get_inner()
        try:
            try:
                inner.delete(tk.SEL_FIRST, tk.SEL_LAST)
            except tk.TclError:
                pass
            inner.insert(tk.INSERT, pyperclip.paste())
        except Exception:
            pass


# ══════════════════════════════════════════════════════════
#  Vista principal — Formulario de entrada
# ══════════════════════════════════════════════════════════

class MainView(ctk.CTkFrame):
    """
    Vista inicial con campo URL, switches de configuración y botón de acción.
    """

    def __init__(self, master, on_submit_callback):
        super().__init__(master, fg_color="transparent")
        self._on_submit = on_submit_callback
        self._build_ui()

    def _build_ui(self):
        # ── Cabecera ───────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(32, 0))

        ctk.CTkLabel(
            header,
            text="▶",
            font=ctk.CTkFont(size=36),
            text_color=COLORS["accent"],
        ).pack()

        ctk.CTkLabel(
            header,
            text="Extractor de Transcripciones",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS["text_primary"],
        ).pack(pady=(4, 2))

        ctk.CTkLabel(
            header,
            text="Obtén los subtítulos de cualquier vídeo de YouTube",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"],
        ).pack()

        # ── Tarjeta principal ──────────────────────────────
        card = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=16)
        card.pack(fill="x", padx=32, pady=24)

        # — Campo URL —
        ctk.CTkLabel(
            card,
            text="URL del vídeo de YouTube",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["text_muted"],
        ).pack(anchor="w", padx=20, pady=(18, 4))

        self.url_entry = ctk.CTkEntry(
            card,
            placeholder_text="https://www.youtube.com/watch?v=...",
            height=42,
            corner_radius=10,
            fg_color=COLORS["entry_bg"],
            border_color=COLORS["separator"],
            border_width=1,
            font=ctk.CTkFont(size=13),
        )
        self.url_entry.pack(fill="x", padx=20, pady=(0, 4))

        ctk.CTkLabel(
            card,
            text="💡 Clic derecho sobre el campo para pegar la URL",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_muted"],
        ).pack(anchor="w", padx=22, pady=(2, 0))

        # — Separador —
        ctk.CTkFrame(card, height=1, fg_color=COLORS["separator"]).pack(
            fill="x", padx=20, pady=16
        )

        # — Switches —
        switches_frame = ctk.CTkFrame(card, fg_color="transparent")
        switches_frame.pack(fill="x", padx=20, pady=(0, 18))

        self.ts_var   = ctk.BooleanVar(value=False)
        self.save_var = ctk.BooleanVar(value=False)

        ctk.CTkSwitch(
            switches_frame,
            text="Incluir marcas de tiempo  [00:00]",
            variable=self.ts_var,
            font=ctk.CTkFont(size=13),
            progress_color=COLORS["accent"],
        ).pack(anchor="w", pady=5)

        ctk.CTkSwitch(
            switches_frame,
            text="Guardar en archivo tras extraer",
            variable=self.save_var,
            font=ctk.CTkFont(size=13),
            progress_color=COLORS["accent"],
        ).pack(anchor="w", pady=5)

        # ── Botón acción ───────────────────────────────────
        self.action_btn = ctk.CTkButton(
            self,
            text="  Obtener Transcripción",
            height=48,
            corner_radius=12,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self._on_action,
        )
        self.action_btn.pack(fill="x", padx=32, pady=(0, 8))

        # ── Label de estado ────────────────────────────────
        self.status_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"],
        )
        self.status_label.pack()

        # ── Menú contextual ────────────────────────────────
        self._ctx_menu = ContextMenu(self.url_entry, self.winfo_toplevel())

    def _on_action(self):
        url = self.url_entry.get().strip()
        include_ts = self.ts_var.get()
        save_file  = self.save_var.get()
        self._on_submit(url, include_ts, save_file)

    def set_loading(self, loading: bool):
        if loading:
            self.action_btn.configure(
                state="disabled",
                text="⏳  Procesando, por favor espera…",
                fg_color="#555555",
            )
            self.status_label.configure(
                text="Conectando con YouTube y extrayendo subtítulos…"
            )
        else:
            self.action_btn.configure(
                state="normal",
                text="  Obtener Transcripción",
                fg_color=COLORS["accent"],
            )
            self.status_label.configure(text="")


# ══════════════════════════════════════════════════════════
#  Vista de transcripción — Resultado
# ══════════════════════════════════════════════════════════

class TranscriptView(ctk.CTkFrame):
    """
    Vista que muestra el título del vídeo y la transcripción completa.
    El textbox es editable. Barra superior con botones de volver,
    guardar como (.txt/.md) y copiar al portapapeles.
    """

    def __init__(self, master, title: str, transcript: str, on_back_callback):
        super().__init__(master, fg_color="transparent")
        self._title      = title
        self._transcript = transcript
        self._on_back    = on_back_callback
        self._build_ui()

    def _build_ui(self):
        # ── Barra superior ─────────────────────────────────
        topbar = ctk.CTkFrame(self, fg_color="transparent")
        topbar.pack(fill="x", padx=20, pady=(16, 0))

        # Botón ← Volver (izquierda)
        ctk.CTkButton(
            topbar,
            text="← Volver",
            width=110,
            height=38,
            corner_radius=8,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["separator"],
            font=ctk.CTkFont(size=13),
            command=self._on_back,
        ).pack(side="left")

        # Botón 📋 Copiar todo (derecha, extremo)
        ctk.CTkButton(
            topbar,
            text="📋  Copiar todo",
            width=130,
            height=38,
            corner_radius=8,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["separator"],
            font=ctk.CTkFont(size=13),
            command=self._copy_all,
        ).pack(side="right", padx=(6, 0))

        # Botón 💾 Guardar como... (derecha, antes de copiar)
        ctk.CTkButton(
            topbar,
            text="💾  Guardar como...",
            width=150,
            height=38,
            corner_radius=8,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["separator"],
            font=ctk.CTkFont(size=13),
            command=self._save_as,
        ).pack(side="right")

        # ── Encabezado del título ──────────────────────────
        title_card = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=12)
        title_card.pack(fill="x", padx=20, pady=(10, 0))

        ctk.CTkLabel(
            title_card,
            text="▶",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["accent"],
        ).pack(pady=(14, 0))

        ctk.CTkLabel(
            title_card,
            text=self._title,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=COLORS["text_primary"],
            wraplength=640,
            justify="center",
        ).pack(padx=20, pady=(2, 14))

        # ── Cuerpo de la transcripción ─────────────────────
        ctk.CTkLabel(
            self,
            text="TRANSCRIPCIÓN",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=COLORS["text_muted"],
        ).pack(anchor="w", padx=22, pady=(14, 4))

        self.textbox = ctk.CTkTextbox(
            self,
            wrap="word",
            font=ctk.CTkFont(family="Consolas", size=13),
            fg_color=COLORS["bg_card"],
            corner_radius=12,
            border_color=COLORS["separator"],
            border_width=1,
            scrollbar_button_color=COLORS["separator"],
        )
        self.textbox.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        self.textbox.insert("end", self._transcript)
        # Sin .configure(state="disabled") → el textbox queda completamente editable

    def _copy_all(self):
        """Copia el contenido actual del textbox (puede haber sido editado)."""
        current_text = self.textbox.get("1.0", "end-1c")
        pyperclip.copy(current_text)
        self._show_copy_feedback()

    def _save_as(self):
        """Abre un diálogo de guardado con soporte para .txt y .md."""
        filename = safe_filename(self._title) or "transcripcion"

        path = filedialog.asksaveasfilename(
            title="Guardar transcripción como…",
            defaultextension=".txt",
            filetypes=[
                ("Archivo de texto", "*.txt"),
                ("Markdown", "*.md"),
                ("Todos los archivos", "*.*"),
            ],
            initialfile=f"{filename}.txt",
        )

        if not path:
            return  # Usuario canceló

        # Leemos el textbox en vivo por si el usuario editó el texto
        current_text = self.textbox.get("1.0", "end-1c")

        if path.endswith(".md"):
            content = format_md_file(self._title, current_text)
        else:
            content = format_txt_file(self._title, current_text)

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo(
                "✅ Guardado correctamente",
                f"La transcripción se ha guardado en:\n\n{path}",
            )
        except OSError as e:
            messagebox.showerror("Error al guardar", f"No se pudo guardar el archivo:\n\n{e}")

    def _show_copy_feedback(self):
        """Muestra un popup verde temporal de confirmación."""
        popup = ctk.CTkToplevel(self)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)

        self.update_idletasks()
        x = self.winfo_rootx() + self.winfo_width() // 2 - 130
        y = self.winfo_rooty() + 60
        popup.geometry(f"260x44+{x}+{y}")

        ctk.CTkFrame(popup, fg_color=COLORS["success"], corner_radius=8).place(
            relwidth=1, relheight=1
        )
        ctk.CTkLabel(
            popup,
            text="✓  Transcripción copiada al portapapeles",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#ffffff",
        ).place(relx=0.5, rely=0.5, anchor="center")

        popup.after(1800, popup.destroy)


# ══════════════════════════════════════════════════════════
#  Ventana principal — App
# ══════════════════════════════════════════════════════════

class App(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("YouTube Transcript Extractor")
        self.geometry("720x560")
        self.minsize(620, 480)
        self.configure(fg_color=COLORS["bg_primary"])

        self._container = ctk.CTkFrame(self, fg_color="transparent")
        self._container.pack(fill="both", expand=True)

        self._show_main()

    # ── Navegación entre vistas ────────────────────────────

    def _clear_container(self):
        for widget in self._container.winfo_children():
            widget.destroy()

    def _show_main(self):
        self._clear_container()
        self.geometry("720x560")
        self._main_view = MainView(self._container, on_submit_callback=self._handle_submit)
        self._main_view.pack(fill="both", expand=True)

    def _show_transcript(self, title: str, transcript: str):
        self._clear_container()
        self.geometry("760x620")
        TranscriptView(
            self._container,
            title=title,
            transcript=transcript,
            on_back_callback=self._show_main,
        ).pack(fill="both", expand=True)

    # ── Lógica de extracción ───────────────────────────────

    def _handle_submit(self, url: str, include_ts: bool, save_file: bool):
        if not url:
            messagebox.showerror("URL vacía", "Por favor, introduce una URL de YouTube.")
            return

        video_id = extract_video_id(url)
        if not video_id:
            messagebox.showerror(
                "URL inválida",
                "No se pudo reconocer el enlace. Asegúrate de que sea una URL\n"
                "válida de YouTube (youtube.com o youtu.be).",
            )
            return

        self._main_view.set_loading(True)

        threading.Thread(
            target=self._worker,
            args=(video_id, include_ts, save_file),
            daemon=True,
        ).start()

    def _worker(self, video_id: str, include_ts: bool, save_file: bool):
        """Hilo secundario: extrae título + transcripción y llama al hilo principal."""
        # 1. Transcripción — nueva API: instancia + .fetch()
        try:
            api = YouTubeTranscriptApi()
            fetched = api.fetch(
                video_id,
                languages=["es", "en", "a.es", "a.en", "es-419"],
            )
            entries = [{"start": s.start, "text": s.text} for s in fetched]
        except TranscriptsDisabled:
            self.after(0, lambda: self._on_error(
                "Subtítulos desactivados",
                "El propietario del vídeo ha desactivado los subtítulos."
            ))
            return
        except NoTranscriptFound:
            self.after(0, lambda: self._on_error(
                "Sin subtítulos",
                "No se encontraron subtítulos disponibles para este vídeo.\n"
                "Prueba con un vídeo que tenga subtítulos en español o inglés."
            ))
            return
        except Exception as exc:
            self.after(0, lambda: self._on_error(
                "Error de extracción",
                f"Ocurrió un error al obtener los subtítulos:\n\n{exc}"
            ))
            return

        # 2. Título
        title      = get_video_title(video_id)
        transcript = format_transcript(entries, include_ts)

        # 3. Resultado en el hilo principal
        if save_file:
            self.after(0, lambda: self._save_file(title, transcript))
        else:
            self.after(0, lambda: self._show_transcript(title, transcript))

    def _on_error(self, title: str, message: str):
        self._main_view.set_loading(False)
        messagebox.showerror(title, message)

    def _save_file(self, title: str, transcript: str):
        """Guardado desde el formulario principal: soporta .txt y .md."""
        self._main_view.set_loading(False)

        filename = safe_filename(title) or "transcripcion"
        path = filedialog.asksaveasfilename(
            title="Guardar transcripción como…",
            defaultextension=".txt",
            filetypes=[
                ("Archivo de texto", "*.txt"),
                ("Markdown", "*.md"),
                ("Todos los archivos", "*.*"),
            ],
            initialfile=f"{filename}.txt",
        )

        if not path:
            return

        content = format_md_file(title, transcript) if path.endswith(".md") else format_txt_file(title, transcript)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo(
                "✅ Guardado correctamente",
                f"La transcripción se ha guardado en:\n\n{path}",
            )
        except OSError as e:
            messagebox.showerror("Error al guardar", f"No se pudo guardar el archivo:\n\n{e}")


# ══════════════════════════════════════════════════════════
#  Punto de entrada
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = App()
    app.mainloop()