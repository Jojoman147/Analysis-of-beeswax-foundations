import tkinter as tk
from tkinter import filedialog, messagebox
import os
import pandas as pd
from PIL import Image, ImageTk

class ManualBeeAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("Analysis of Beeswax Foundations 4.0 - Measurement Tool")
        self.root.geometry("1200x800")

        # -- Data Variables --
        self.file_paths = []
        self.current_index = 0
        self.results_data = []
        
        # Points for polygons
        self.frame_points = []   # Blue (Frame)
        self.built_points = []   # Green (Drawn-out)
        self.honey_points = []   # Red (Honey)
        self.brood_points = []   # Orange (Brood)
        
        self.stage = 'FRAME' 
        self.img_scale = 1.0
        self.original_image = None
        self.tk_image = None

        # --- GUI ELEMENTS ---
        control_frame = tk.Frame(root, bg="#f0f0f0", pady=5, padx=5)
        control_frame.pack(fill=tk.X)

        self.btn_load = tk.Button(control_frame, text="1. Load Images", command=self.load_files, bg="#dddddd", font=("Arial", 10))
        self.btn_load.pack(side=tk.LEFT, padx=5)

        self.lbl_status = tk.Label(control_frame, text="Waiting for files...", font=("Arial", 11, "bold"), bg="#f0f0f0")
        self.lbl_status.pack(side=tk.LEFT, padx=15)

        self.btn_next = tk.Button(control_frame, text="Confirm and Next >>", command=self.confirm_and_next, state=tk.DISABLED, bg="#ccffcc", font=("Arial", 10, "bold"))
        self.btn_next.pack(side=tk.RIGHT, padx=5)

        self.btn_undo = tk.Button(control_frame, text="Undo", command=self.undo_last_point, state=tk.DISABLED, bg="#ffcccc")
        self.btn_undo.pack(side=tk.RIGHT, padx=5)
        
        self.btn_full_built = tk.Button(control_frame, text="100% Drawn-out", command=self.set_full_built, state=tk.DISABLED, bg="#aaffaa")
        self.btn_full_built.pack(side=tk.RIGHT, padx=10)

        self.btn_zero_built = tk.Button(control_frame, text="0% (Empty)", command=self.set_zero_built, state=tk.DISABLED, bg="#ffd0d0")
        self.btn_zero_built.pack(side=tk.RIGHT, padx=5)

        self.canvas_frame = tk.Frame(root)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="gray")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<Button-3>", self.on_right_click)

        self.lbl_instruction = tk.Label(root, text="", bg="yellow", font=("Arial", 12), pady=5)
        self.lbl_instruction.pack(fill=tk.X)

    def load_files(self):
        files = filedialog.askopenfilenames(title="Select photos", filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp")])
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
            self.lbl_status.config(text=f"Image {self.current_index + 1} / {len(self.file_paths)}: {filename}")
            self.update_ui_state()
        except Exception as e:
            self.current_index += 1
            self.load_current_image()

    def update_ui_state(self):
        self.btn_undo.config(state=tk.NORMAL if (self.frame_points or self.built_points or self.honey_points or self.brood_points) else tk.DISABLED)
        self.btn_full_built.config(state=tk.DISABLED)
        self.btn_zero_built.config(state=tk.DISABLED)

        if self.stage == 'FRAME':
            self.lbl_instruction.config(text=f"STEP 1: Mark 4 corners of inner frame ({len(self.frame_points)}/4)", bg="#ccccff")
            self.btn_next.config(state=tk.DISABLED)
        elif self.stage == 'BUILT':
            self.lbl_instruction.config(text="STEP 2: Outline DRAWN-OUT area. Right-click to finish.", bg="#ccffcc")
            self.btn_full_built.config(state=tk.NORMAL if not self.built_points else tk.DISABLED)
            self.btn_zero_built.config(state=tk.NORMAL if not self.built_points else tk.DISABLED)
            self.btn_next.config(state=tk.DISABLED)
        elif self.stage == 'HONEY':
            self.lbl_instruction.config(text="STEP 3: Outline HONEY area. If none, click Next.", bg="#ffcccc")
            self.btn_next.config(state=tk.NORMAL, text="No honey (Next) >>")
        elif self.stage == 'BROOD':
            self.lbl_instruction.config(text="STEP 4: Outline BROOD area. If none, click Finish.", bg="#ffe4b5")
            self.btn_next.config(state=tk.NORMAL, text="No brood (Finish) >>")
        elif self.stage == 'DONE':
            self.btn_next.config(state=tk.NORMAL, text="Confirm and Next >>")

    def redraw_overlays(self):
        self.canvas.delete("overlay")
        self._draw_polygon(self.frame_points, "blue", closed=(len(self.frame_points)==4))
        if self.built_points: self._draw_polygon(self.built_points, "#00ff00", closed=(self.stage != 'BUILT'), fill_color="green")
        if self.honey_points: self._draw_polygon(self.honey_points, "red", closed=(self.stage != 'HONEY'), fill_color="red")
        if self.brood_points: self._draw_polygon(self.brood_points, "orange", closed=(self.stage == 'DONE'), fill_color="orange")

    def _draw_polygon(self, points, color, closed=False, fill_color=None):
        if not points: return
        for i, p in enumerate(points):
            self.canvas.create_oval(p[0]-3, p[1]-3, p[0]+3, p[1]+3, fill=color, tags="overlay")
            if i < len(points) - 1: self.canvas.create_line(points[i], points[i+1], fill=color, width=2, tags="overlay")
        if closed and len(points) > 2:
            self.canvas.create_line(points[-1], points[0], fill=color, width=2, tags="overlay")
            if fill_color: self.canvas.create_polygon(points, outline=color, fill=fill_color, stipple="gray25", width=2, tags="overlay")

    def on_left_click(self, event):
        x, y = event.x, event.y
        if self.stage == 'FRAME' and len(self.frame_points) < 4:
            self.frame_points.append((x, y))
            if len(self.frame_points) == 4: self.stage = 'BUILT'
        elif self.stage == 'BUILT': self.built_points.append((x, y))
        elif self.stage == 'HONEY': self.honey_points.append((x, y))
        elif self.stage == 'BROOD': self.brood_points.append((x, y))
        self.redraw_overlays(); self.update_ui_state()

    def on_right_click(self, event):
        if self.stage == 'BUILT' and len(self.built_points) > 2: self.stage = 'HONEY'
        elif self.stage == 'HONEY' and len(self.honey_points) > 2: self.stage = 'BROOD'
        elif self.stage == 'BROOD' and len(self.brood_points) > 2: self.stage = 'DONE'
        self.redraw_overlays(); self.update_ui_state()

    def set_full_built(self):
        self.built_points = list(self.frame_points); self.stage = 'HONEY'
        self.redraw_overlays(); self.update_ui_state()

    def set_zero_built(self):
        self.built_points = []; self.honey_points = []; self.brood_points = []; self.stage = 'DONE'
        self.redraw_overlays(); self.update_ui_state()

    def undo_last_point(self):
        if self.stage == 'DONE': self.stage = 'BROOD'
        elif self.stage == 'BROOD': (self.brood_points.pop() if self.brood_points else setattr(self, 'stage', 'HONEY'))
        elif self.stage == 'HONEY': (self.honey_points.pop() if self.honey_points else setattr(self, 'stage', 'BUILT'))
        elif self.stage == 'BUILT': (self.built_points.pop() if self.built_points else setattr(self, 'stage', 'FRAME'))
        elif self.stage == 'FRAME' and self.frame_points: self.frame_points.pop()
        self.redraw_overlays(); self.update_ui_state()

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
        data = {"Original_Name": filename, "Code": code, "Hive_Number": None, "Location": "Other", "Paraffin_Percentage": 0}
        try:
            if code[0].isdigit():
                data["Hive_Number"] = int(code[0])
                loc_map = {'D': "Brood_Chamber", 'H': "Honey_Super"}
                data["Location"] = loc_map.get(code[2], "Other")
                data["Paraffin_Percentage"] = int(code[3]) * 10
        except: pass
        return data

    def confirm_and_next(self):
        if self.stage == 'HONEY': self.stage = 'BROOD'; self.update_ui_state(); return
        if self.stage == 'BROOD': self.stage = 'DONE'; self.update_ui_state(); return

        area_frame = self.calculate_polygon_area(self.frame_points)
        pct_built = min((self.calculate_polygon_area(self.built_points) / area_frame * 100), 100) if area_frame > 0 else 0
        pct_honey = min((self.calculate_polygon_area(self.honey_points) / area_frame * 100), 100) if area_frame > 0 else 0
        pct_brood = min((self.calculate_polygon_area(self.brood_points) / area_frame * 100), 100) if area_frame > 0 else 0

        filename = os.path.basename(self.file_paths[self.current_index])
        row = self.parse_filename(filename)
        row.update({"Drawn_Out_Percentage": round(pct_built, 2), "Honey_Percentage": round(pct_honey, 2), "Brood_Percentage": round(pct_brood, 2)})
        self.results_data.append(row)
        self.current_index += 1; self.load_current_image()

    def finish_analysis(self):
        if self.results_data and messagebox.askyesno("Save", "Save to Excel?"):
            save_path = filedialog.asksaveasfilename(defaultextension=".xlsx")
            if save_path:
                pd.DataFrame(self.results_data).to_excel(save_path, index=False)
                messagebox.showinfo("Success", "Saved.")
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk(); app = ManualBeeAnalyzer(root); root.mainloop()