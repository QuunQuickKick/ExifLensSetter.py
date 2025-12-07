# --------------------------------------------------------------------------------------
# ExifLensSetter.py (Standalone Exif Writer)
# 
# 本コード ExifLensSetter.py は、MITライセンスのもとで公開されます。
# Copyright (c) 2025 QQK / QuunQuickKick
# All Rights Reserved.
# 
# 本コードは、以下のオープンソースライブラリを使用して開発されています。
# - customtkinter: MIT License
# - tkinterdnd2: MIT License
# 
# 本ソフトウェアは、ExifTool (Artistic License 1.0) の外部コマンド実行を前提としています。
# ExifToolは、別途インストールまたは実行ファイルが本アプリケーションと同じディレクトリに必要です。
# --------------------------------------------------------------------------------------

import customtkinter as ctk
import subprocess
import json
import os
import ctypes
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from pathlib import Path

# --- 【解決策】DPIスケーリング設定の追加 ---
# Windows環境でのみ実行し、DPIスケーリングをシステムに任せるための設定
try:
    if os.name == 'nt': # Windows環境かチェック
        # Windows 8.1以降の高DPI設定を有効にする
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass
# ---------------------------------------------

# --- アプリケーション設定 ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

PRESET_FILE = "presets.json"

# ctk.CTkの代わりに、DND機能を持つTkinterDnD.Tkを継承します
class LensTaggerApp(TkinterDnD.Tk): 
    def __init__(self):
        super().__init__()
        
        # 【削除済み】TkinterDnD.DnDWrapper(self) は継承により不要となりました
        
        # --- ルートウィンドウの背景色をダークモードに設定 ---
        # 標準のCTkダークモードの背景色であるダークグレー(#242424)を明示的に指定します。
        self.configure(background="#242424") 
        # -------------------------------------------------------

        # --- ウィンドウサイズ調整 ---
        self.title("ExifLensSetter.py")
        self.geometry("1200x1200")

        # グリッドレイアウト設定
        self.grid_columnconfigure(0, weight=1) 
        self.grid_columnconfigure(1, weight=2) 
        self.grid_rowconfigure(0, weight=1)

        self.presets = {}
        self.selected_files = []
        self.selected_preset_name = None

        # --- 左パネル：プリセットリスト ---
        self.left_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.lbl_presets = ctk.CTkLabel(self.left_frame, text="保存済みレンズ", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_presets.pack(pady=(10, 10))

        #self.scroll_frame = ctk.CTkScrollableFrame(self.left_frame, label_text="リスト")
        self.scroll_frame = ctk.CTkScrollableFrame(self.left_frame)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # --- 右パネル：入力と操作 ---
        self.right_frame = ctk.CTkFrame(self, corner_radius=0)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.lbl_title = ctk.CTkLabel(self.right_frame, text="レンズ情報入力", font=ctk.CTkFont(size=20, weight="bold"))
        self.lbl_title.pack(pady=10)

        # 入力フィールド群
        self.input_frame = ctk.CTkFrame(self.right_frame)
        self.input_frame.pack(fill="x", padx=10, pady=10)

        # レンズ名
        self.entry_lens = self.create_input_field(self.input_frame, "レンズモデル名 (例: Super Takumar 55mm F1.8)")
        # 焦点距離
        self.entry_focal = self.create_input_field(self.input_frame, "焦点距離 (mm) (例: 55)")
        # 開放F値 (MaxApertureValue)
        self.entry_aperture = self.create_input_field(self.input_frame, "開放F値 (MaxApertureValue) (例: 1.8)")
        # 撮影時のF値
        self.entry_actual_aperture = self.create_input_field(self.input_frame, "撮影時のF値 (F-Number) (例: 5.6)")

        # プリセット操作ボタン
        self.preset_btn_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.preset_btn_frame.pack(fill="x", padx=10, pady=5)
        
        self.btn_save_preset = ctk.CTkButton(self.preset_btn_frame, text="プリセット保存", command=self.save_preset, fg_color="green")
        self.btn_save_preset.pack(side="left", expand=True, padx=5)
        
        self.btn_del_preset = ctk.CTkButton(self.preset_btn_frame, text="プリセット削除", command=self.delete_preset, fg_color="firebrick")
        self.btn_del_preset.pack(side="right", expand=True, padx=5)

        ctk.CTkLabel(self.right_frame, text="--------------------------------------------------").pack(pady=10)

        # ファイル選択エリア (ドラッグ＆ドロップ対応)
        self.lbl_files = ctk.CTkLabel(self.right_frame, text="対象画像ファイル (D&Dまたはボタンで選択)", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_files.pack(pady=5)

        self.file_textbox = ctk.CTkTextbox(self.right_frame, height=200) 
        self.file_textbox.pack(fill="x", padx=10, pady=5)
        self.file_textbox.configure(state="disabled")

        # D&Dのバインド設定は変更なし
        self.file_textbox.drop_target_register(DND_FILES)
        self.file_textbox.dnd_bind('<<Drop>>', self.handle_drop)
        self.file_textbox.dnd_bind('<<DragEnter>>', lambda e: self.status_label.configure(text="ドロップOK！", text_color="yellow"))
        self.file_textbox.dnd_bind('<<DragLeave>>', lambda e: self.status_label.configure(text="準備完了", text_color="gray"))
        
        #self.btn_select_files = ctk.CTkButton(self.right_frame, text="ファイルを選択する...", command=self.select_files)
        #self.btn_select_files.pack(pady=5)
        
        # --- ファイル操作ボタンを格納するフレーム ---
        self.file_control_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.file_control_frame.pack(fill="x", padx=10, pady=5)
        # 既存の選択ボタンを左寄せに配置
        self.btn_select_files = ctk.CTkButton(self.file_control_frame, text="ファイルを選択する...", command=self.select_files)
        self.btn_select_files.pack(side="left", expand=True, padx=5)
        # 新規のクリアボタンを右寄せに配置
        self.btn_clear_files = ctk.CTkButton(self.file_control_frame, 
                                            text="リストをクリア", 
                                            command=self.clear_selected_files, 
                                            fg_color="gray50") # 目立つように色を変更
        self.btn_clear_files.pack(side="right", expand=True, padx=5)
        # --------------------------------------------
        
        
        # --- オプション機能チェックボックス ---
        # --- オリジナルのバックアップを残す機能 ---
        self.backup_var = ctk.BooleanVar(value=False) # デフォルトはバックアップを残さない(False)
        self.chk_backup = ctk.CTkCheckBox(
            self.right_frame, 
            text="オリジナルのバックアップを残す (XXX_original)", 
            variable=self.backup_var,
            onvalue=True,
            offvalue=False
        )
        self.chk_backup.pack(pady=(10, 5), padx=20, anchor="w")
        # ---------------------------------------------
        
        
        # 実行エリア
        self.status_label = ctk.CTkLabel(self.right_frame, text="準備完了", text_color="gray")
        self.status_label.pack(pady=(20, 5))

        self.btn_run = ctk.CTkButton(self.right_frame, text="書き込み実行 (ExifTool)", command=self.run_exiftool, height=50, font=ctk.CTkFont(size=18, weight="bold"))
        self.btn_run.pack(fill="x", padx=20, pady=(0, 20))

        # 初期化処理
        self.load_presets()

    def create_input_field(self, parent, placeholder):
        entry = ctk.CTkEntry(parent, placeholder_text=placeholder, height=35)
        entry.pack(fill="x", padx=10, pady=5)
        return entry

    # --- D&D処理 ---
    def handle_drop(self, event):
        paths_str = event.data
        
        if paths_str.startswith('{') and paths_str.endswith('}'):
            self.selected_files = [p.strip('{}') for p in paths_str.split('} {')]
        elif ';' in paths_str: 
            self.selected_files = paths_str.split(';')
        else:
             self.selected_files = paths_str.split()
        
        self.selected_files = [p for p in self.selected_files if p and os.path.exists(p)]
        
        if self.selected_files:
            self.update_file_list_display()
            self.status_label.configure(text=f"{len(self.selected_files)}件のファイルをドロップしました", text_color="white")
        else:
            self.status_label.configure(text="有効なファイルがありません", text_color="red")


    # --- ロジック部分 ---

    def select_files(self):
        filetypes = (('画像ファイル', '*.jpg *.jpeg *.tif *.tiff *.dng *.arw *.cr2 *.nef *.raf *.orf'), ('すべてのファイル', '*.*'))
        filenames = filedialog.askopenfilenames(title='画像を選択', filetypes=filetypes)
        
        if filenames:
            self.selected_files = filenames
            self.update_file_list_display()

    def update_file_list_display(self):
        self.file_textbox.configure(state="normal")
        self.file_textbox.delete("0.0", "end")
        count = len(self.selected_files)
        self.file_textbox.insert("end", f"【選択数: {count}枚】\n")
        for f in self.selected_files:
            self.file_textbox.insert("end", f"{os.path.basename(f)}\n")
        self.file_textbox.configure(state="disabled")

    def save_preset(self):
        lens_name = self.entry_lens.get()
        if not lens_name:
            messagebox.showwarning("エラー", "レンズ名が入力されていません。")
            return
        
        data = {
            "lens": lens_name,
            "focal": self.entry_focal.get(),
            "aperture": self.entry_aperture.get(),
            "actual_aperture": self.entry_actual_aperture.get() 
        }
        
        self.presets[lens_name] = data
        self.write_presets_to_file()
        self.refresh_preset_list()
        self.status_label.configure(text=f"プリセット '{lens_name}' を保存しました", text_color="cyan")

    def delete_preset(self):
        if self.selected_preset_name and self.selected_preset_name in self.presets:
            del self.presets[self.selected_preset_name]
            self.write_presets_to_file()
            self.refresh_preset_list()
            self.clear_inputs()
            self.status_label.configure(text="プリセットを削除しました", text_color="orange")

    def write_presets_to_file(self):
        with open(PRESET_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.presets, f, ensure_ascii=False, indent=4)

    def load_presets(self):
        if os.path.exists(PRESET_FILE):
            try:
                with open(PRESET_FILE, 'r', encoding='utf-8') as f:
                    self.presets = json.load(f)
            except:
                self.presets = {}
        self.refresh_preset_list()

    def refresh_preset_list(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        for name in self.presets.keys():
            btn = ctk.CTkButton(
                self.scroll_frame, 
                text=name, 
                command=lambda n=name: self.apply_preset(n),
                fg_color="transparent", 
                border_width=1,
                text_color=("gray10", "gray90")
            )
            btn.pack(fill="x", padx=5, pady=2)

    def apply_preset(self, name):
        self.selected_preset_name = name
        data = self.presets[name]
        
        self.clear_inputs()
        self.entry_lens.insert(0, data.get("lens", ""))
        self.entry_focal.insert(0, data.get("focal", ""))
        self.entry_aperture.insert(0, data.get("aperture", ""))
        self.entry_actual_aperture.insert(0, data.get("actual_aperture", ""))
        
        self.status_label.configure(text=f"プリセット '{name}' を読み込みました", text_color="white")

    def clear_inputs(self):
        self.entry_lens.delete(0, "end")
        self.entry_focal.delete(0, "end")
        self.entry_aperture.delete(0, "end")
        self.entry_actual_aperture.delete(0, "end") 

    def clear_selected_files(self):
        """選択されているファイルリストをリセットし、表示をクリアします。"""
        self.selected_files = []
        self.update_file_list_display() # テキストボックスを空にする
        self.status_label.configure(text="ファイルリストをクリアしました", text_color="orange")

    def run_exiftool(self):
        if not self.selected_files:
            messagebox.showwarning("エラー", "画像ファイルが選択されていません。")
            return

        lens = self.entry_lens.get()
        focal = self.entry_focal.get()
        aperture = self.entry_aperture.get()
        actual_aperture = self.entry_actual_aperture.get()

        if not lens:
            messagebox.showwarning("エラー", "レンズモデル名は必須です。")
            return

        cmd = ["exiftool", "-P"]
        
        # --- バックアップ設定の確認 ---
        if not self.backup_var.get():
            # チェックボックスがOFFの場合 (バックアップを残さない場合) のみ、上書きフラグを使用
            cmd.append("-overwrite_original")
        # --------------------------------------
        
        cmd.extend([f"-LensModel={lens}", f"-Lens={lens}"])
        
        if focal:
            cmd.extend([f"-FocalLength={focal}"])
        
        if aperture:
            cmd.extend([f"-MaxApertureValue={aperture}"])
        
        if actual_aperture:
            cmd.extend([f"-FNumber={actual_aperture}", f"-ApertureValue={actual_aperture}"])
        
        cmd.extend(self.selected_files)

        self.status_label.configure(text="書き込み中...", text_color="yellow")
        self.update()

        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            subprocess.run(cmd, check=True, startupinfo=startupinfo)
            
            self.status_label.configure(text="書き込み完了！", text_color="green")
            messagebox.showinfo("成功", f"{len(self.selected_files)}枚の画像に情報を書き込みました。")
            
        except FileNotFoundError:
            messagebox.showerror("エラー", "ExifToolが見つかりません。\n'exiftool' がパスに通っているか、同じフォルダに exiftool.exe を置いてください。")
            self.status_label.configure(text="ExifTool未検出", text_color="red")
        except subprocess.CalledProcessError as e:
            self.status_label.configure(text="書き込みエラー", text_color="red")
            messagebox.showerror("エラー", f"書き込み中にエラーが発生しました。\n{e}")

if __name__ == "__main__":
    app = LensTaggerApp()
    app.mainloop()