import tkinter as tk
from tkinter import filedialog, messagebox
import os
import pandas as pd
from PIL import Image, ImageTk

class ManualBeeAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title(" Analysys of beeswax foundations 4.0 ")
        self.root.geometry("1200x800")

        # --- Dátové premenné ---
        self.file_paths = []
        self.current_index = 0
        self.results_data = []
        
        # Body pre polygóny
        self.frame_points = []   # Modrá (Rámik)
        self.built_points = []   # Zelená (Vystavané)
        self.honey_points = []   # Červená (Med)
        self.brood_points = []   # Oranžová (Plod) - NOVÉ
        
        # Stav aplikácie
        # Postupnosť: FRAME -> BUILT -> HONEY -> BROOD -> DONE
        self.stage = 'FRAME' 
        
        self.img_scale = 1.0
        self.original_image = None
        self.tk_image = None

        # --- GUI ELEMENTY ---
        
        # 1. Horný panel (Ovládanie)
        control_frame = tk.Frame(root, bg="#f0f0f0", pady=5, padx=5)
        control_frame.pack(fill=tk.X)

        # Ľavá strana
        self.btn_load = tk.Button(control_frame, text="1. Načítať obrázky", command=self.load_files, bg="#dddddd", font=("Arial", 10))
        self.btn_load.pack(side=tk.LEFT, padx=5)

        self.lbl_status = tk.Label(control_frame, text="Čakám na súbory...", font=("Arial", 11, "bold"), bg="#f0f0f0")
        self.lbl_status.pack(side=tk.LEFT, padx=15)

        # Pravá strana (Tlačidlá akcií - ukladajú sa sprava doľava)
        
        self.btn_next = tk.Button(control_frame, text="Potvrdiť a Ďalší >>", command=self.confirm_and_next, state=tk.DISABLED, bg="#ccffcc", font=("Arial", 10, "bold"))
        self.btn_next.pack(side=tk.RIGHT, padx=5)

        self.btn_undo = tk.Button(control_frame, text="Späť", command=self.undo_last_point, state=tk.DISABLED, bg="#ffcccc")
        self.btn_undo.pack(side=tk.RIGHT, padx=5)
        
        # Tlačidlo 100%
        self.btn_full_built = tk.Button(control_frame, text="Je to 100%", command=self.set_full_built, state=tk.DISABLED, bg="#aaffaa")
        self.btn_full_built.pack(side=tk.RIGHT, padx=10)

        # Tlačidlo 0%
        self.btn_zero_built = tk.Button(control_frame, text="Je to 0% (Prázdne)", command=self.set_zero_built, state=tk.DISABLED, bg="#ffd0d0")
        self.btn_zero_built.pack(side=tk.RIGHT, padx=5)

        # 2. Canvas (Obrázok)
        self.canvas_frame = tk.Frame(root)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="gray")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<Button-3>", self.on_right_click)

        # 3. Dolný panel (Inštrukcie)
        self.lbl_instruction = tk.Label(root, text="", bg="yellow", font=("Arial", 12), pady=5)
        self.lbl_instruction.pack(fill=tk.X)

    # --- LOGIKA APLIKÁCIE ---

    def load_files(self):
        files = filedialog.askopenfilenames(title="Vyber fotografie", filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.HEIC")])
        if files:
            self.file_paths = files
            self.current_index = 0
            self.results_data = []
            self.load_current_image()

    def load_current_image(self):
        if self.current_index >= len(self.file_paths):
            self.finish_analysis()
            return

        file_path = self.file_paths[self.current_index]
        filename = os.path.basename(file_path)
        
        self.frame_points = []
        self.built_points = []
        self.honey_points = []
        self.brood_points = []
        self.stage = 'FRAME'
        
        try:
            image = Image.open(file_path)
        except Exception as e:
            print(f"Chyba pri otváraní {filename}: {e}")
            self.current_index += 1
            self.load_current_image()
            return

        max_w, max_h = 1100, 700
        orig_w, orig_h = image.size
        ratio = min(max_w/orig_w, max_h/orig_h)
        new_size = (int(orig_w * ratio), int(orig_h * ratio))
        
        self.img_scale = ratio 
        self.original_image = image.resize(new_size, Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(self.original_image)

        self.canvas.delete("all")
        self.canvas.config(width=new_size[0], height=new_size[1])
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

        self.lbl_status.config(text=f"Obrázok {self.current_index + 1} / {len(self.file_paths)}: {filename}")
        self.update_ui_state()

    def update_ui_state(self):
        """Aktualizuje texty a dostupnosť tlačidiel"""
        self.btn_undo.config(state=tk.NORMAL if (self.frame_points or self.built_points or self.honey_points or self.brood_points) else tk.DISABLED)
        
        self.btn_full_built.config(state=tk.DISABLED)
        self.btn_zero_built.config(state=tk.DISABLED)

        if self.stage == 'FRAME':
            pts = len(self.frame_points)
            self.lbl_instruction.config(text=f"KROK 1 (MODRÁ): Klikni na 4 rohy vnútornej plochy rámika. ({pts}/4)", bg="#ccccff")
            self.btn_next.config(state=tk.DISABLED)

        elif self.stage == 'BUILT':
            pts = len(self.built_points)
            self.lbl_instruction.config(text=f"KROK 2 (ZELENÁ): Obkresli vystavanú časť. Pravý klik ukončí.", bg="#ccffcc")
            if pts == 0:
                self.btn_full_built.config(state=tk.NORMAL)
                self.btn_zero_built.config(state=tk.NORMAL)
            self.btn_next.config(state=tk.DISABLED)

        elif self.stage == 'HONEY':
            pts = len(self.honey_points)
            self.lbl_instruction.config(text=f"KROK 3 (ČERVENÁ): Máš tam med? Obkresli ho. Ak nie, potvrdi.", bg="#ffcccc")
            if pts == 0:
                 self.btn_next.config(state=tk.NORMAL, text="Nemám med (Ďalej) >>")
            else:
                 self.btn_next.config(state=tk.DISABLED)

        elif self.stage == 'BROOD': # NOVÝ KROK
            pts = len(self.brood_points)
            self.lbl_instruction.config(text=f"KROK 4 (ORANŽOVÁ): Máš tam PLOD? Obkresli ho. Ak nie, potvrdi.", bg="#ffe4b5")
            if pts == 0:
                 self.btn_next.config(state=tk.NORMAL, text="Nemám plod (Dokončiť) >>")
            else:
                 self.btn_next.config(state=tk.DISABLED)

        elif self.stage == 'DONE':
            self.lbl_instruction.config(text="HOTOVO: Skontroluj a pokračuj.", bg="#ffffff")
            self.btn_next.config(state=tk.NORMAL, text="Potvrdiť a Ďalší >>")

    # --- KRESLENIE ---

    def redraw_overlays(self):
        self.canvas.delete("overlay")
        
        # 1. Rámik (Modrá)
        self._draw_polygon(self.frame_points, "blue", closed=(len(self.frame_points)==4))

        # 2. Vystavané (Zelená)
        green_closed = (self.stage in ['HONEY', 'BROOD', 'DONE'])
        if self.built_points:
            self._draw_polygon(self.built_points, "#00ff00", closed=green_closed, fill_color="green")

        # 3. Med (Červená)
        red_closed = (self.stage in ['BROOD', 'DONE'])
        if self.honey_points:
            self._draw_polygon(self.honey_points, "red", closed=red_closed, fill_color="red")

        # 4. Plod (Oranžová) - NOVÉ
        brood_closed = (self.stage == 'DONE')
        if self.brood_points:
            self._draw_polygon(self.brood_points, "orange", closed=brood_closed, fill_color="orange")

    def _draw_polygon(self, points, color, closed=False, fill_color=None):
        if not points: return
        for i in range(len(points)):
            p = points[i]
            self.canvas.create_oval(p[0]-3, p[1]-3, p[0]+3, p[1]+3, fill=color, tags="overlay")
            if i < len(points) - 1:
                self.canvas.create_line(points[i], points[i+1], fill=color, width=2, tags="overlay")
        
        if closed and len(points) > 2:
            self.canvas.create_line(points[-1], points[0], fill=color, width=2, tags="overlay")
            if fill_color:
                self.canvas.create_polygon(points, outline=color, fill=fill_color, stipple="gray25", width=2, tags="overlay")

    # --- INTERAKCIA ---

    def on_left_click(self, event):
        x, y = event.x, event.y
        
        if self.stage == 'FRAME':
            if len(self.frame_points) < 4:
                self.frame_points.append((x, y))
                if len(self.frame_points) == 4:
                    self.stage = 'BUILT'
                self.redraw_overlays()
                self.update_ui_state()

        elif self.stage == 'BUILT':
            self.built_points.append((x, y))
            self.redraw_overlays()
            self.update_ui_state()

        elif self.stage == 'HONEY':
            self.honey_points.append((x, y))
            self.redraw_overlays()
            self.update_ui_state()

        elif self.stage == 'BROOD': # NOVÉ
            self.brood_points.append((x, y))
            self.redraw_overlays()
            self.update_ui_state()

    def on_right_click(self, event):
        if self.stage == 'BUILT' and len(self.built_points) > 2:
            self.stage = 'HONEY'
            self.redraw_overlays()
            self.update_ui_state()
            
        elif self.stage == 'HONEY' and len(self.honey_points) > 2:
            self.stage = 'BROOD' # Prechod na plod
            self.redraw_overlays()
            self.update_ui_state()

        elif self.stage == 'BROOD' and len(self.brood_points) > 2:
            self.stage = 'DONE' # Prechod na koniec
            self.redraw_overlays()
            self.update_ui_state()

    def set_full_built(self):
        """100% Vystavané -> Skopíruje rámik, prejde na Med"""
        if self.stage == 'BUILT' and len(self.frame_points) == 4:
            self.built_points = list(self.frame_points)
            self.stage = 'HONEY'
            self.redraw_overlays()
            self.update_ui_state()

    def set_zero_built(self):
        """0% Vystavané -> Žiadne body, prejde rovno na KONIEC"""
        if self.stage == 'BUILT':
            self.built_points = []
            self.honey_points = []
            self.brood_points = []
            self.stage = 'DONE'
            self.redraw_overlays()
            self.update_ui_state()

    def undo_last_point(self):
        """Inteligentné tlačidlo Späť"""
        if self.stage == 'DONE':
            if not self.built_points: # Ak bolo 0% empty
                self.stage = 'BUILT'
            else:
                self.stage = 'BROOD' # Vraciame sa do plodu

        elif self.stage == 'BROOD':
            if self.brood_points:
                self.brood_points.pop()
            else:
                self.stage = 'HONEY' # Vraciame sa do medu

        elif self.stage == 'HONEY':
            if self.honey_points:
                self.honey_points.pop()
            else:
                self.stage = 'BUILT'
                if self.built_points == self.frame_points: # Ak to bolo auto-100%
                    self.built_points = []
        
        elif self.stage == 'BUILT':
            if self.built_points:
                self.built_points.pop()
            else:
                self.stage = 'FRAME'
                if self.frame_points:
                    self.frame_points.pop()
        
        elif self.stage == 'FRAME':
            if self.frame_points:
                self.frame_points.pop()

        self.redraw_overlays()
        self.update_ui_state()

    # --- VÝPOČTY A EXPORT ---

    def calculate_polygon_area(self, points):
        n = len(points)
        if n < 3: return 0.0
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += points[i][0] * points[j][1]
            area -= points[j][0] * points[i][1]
        return abs(area) / 2.0

    def parse_filename(self, filename):
        base_name = os.path.splitext(filename)[0]
        code = base_name[:5].upper()
        data = {
            "Original_Name": filename, "Kod": code,
            "Cislo_Ula": None, "Typ": None, "Lokacia": None, 
            "Parafin_Percento": None, "Strana": None
        }
        try:
            if len(code) == 5 and code[0].isdigit() and code[3].isdigit() and code[4].isdigit():
                data["Cislo_Ula"] = int(code[0])
                data["Typ"] = "Parafin" if code[1] == 'P' else code[1]
                loc_map = {'D': "Plodisko", 'H': "Medník"}
                data["Lokacia"] = loc_map.get(code[2], code[2])
                data["Parafin_Percento"] = int(code[3]) * 10
                data["Strana"] = "Predná" if int(code[4]) == 0 else "Zadná"
        except: pass
        return data

    def confirm_and_next(self):
        # 1. Ak užívateľ klikol tlačidlo "Nemám plod/med", musíme posunúť stage
        if self.stage == 'HONEY':
            self.stage = 'BROOD'
            self.update_ui_state()
            return
        elif self.stage == 'BROOD':
            self.stage = 'DONE'
            self.update_ui_state()
            return

        # Výpočty (len ak sme v DONE)
        area_frame = self.calculate_polygon_area(self.frame_points)
        area_built = self.calculate_polygon_area(self.built_points)
        area_honey = self.calculate_polygon_area(self.honey_points)
        area_brood = self.calculate_polygon_area(self.brood_points)

        pct_built = (area_built / area_frame * 100) if area_frame > 0 else 0
        pct_honey = (area_honey / area_frame * 100) if area_frame > 0 else 0
        pct_brood = (area_brood / area_frame * 100) if area_frame > 0 else 0

        # Ošetrenie pretečenia
        if pct_built > 100: pct_built = 100.0
        if pct_honey > 100: pct_honey = 100.0
        if pct_brood > 100: pct_brood = 100.0

        filename = os.path.basename(self.file_paths[self.current_index])
        row = self.parse_filename(filename)
        
        row.update({
            "Vystavane_Percent": round(pct_built, 2),
            "Med_Percent": round(pct_honey, 2),
            "Plod_Percent": round(pct_brood, 2), # NOVÝ STĹPEC
            "Plocha_Ramika_px": int(area_frame),
            "Plocha_Vystavane_px": int(area_built),
            "Plocha_Medu_px": int(area_honey),
            "Plocha_Plodu_px": int(area_brood)
        })
        
        self.results_data.append(row)
        print(f"Uložené: {filename} -> Vyst:{pct_built:.1f}%, Med:{pct_honey:.1f}%, Plod:{pct_brood:.1f}%")

        self.current_index += 1
        self.load_current_image()

    def finish_analysis(self):
        if not self.results_data:
            self.root.destroy()
            return
            
        response = messagebox.askyesno("Dokončené", "Hotovo! Chceš uložiť výsledky do Excelu?")
        if response:
            save_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                title="Uložiť výslednú tabuľku"
            )
            if save_path:
                df = pd.DataFrame(self.results_data)
                cols = ["Kod", "Cislo_Ula", "Lokacia", "Parafin_Percento", "Strana", 
                        "Vystavane_Percent", "Med_Percent", "Plod_Percent", 
                        "Original_Name"]
                final_cols = [c for c in cols if c in df.columns] + [c for c in df.columns if c not in cols]
                df = df[final_cols]
                
                try:
                    df.to_excel(save_path, index=False)
                    messagebox.showinfo("Super", "Excel tabuľka bola uložená.")
                except Exception as e:
                    messagebox.showerror("Chyba", f"Nedalo sa uložiť: {e}")
        
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ManualBeeAnalyzer(root)
    root.mainloop()