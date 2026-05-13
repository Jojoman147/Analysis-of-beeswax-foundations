import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats
import os

# Nastavenie vizuálu
sns.set_theme(style="whitegrid")

class ApiaryComparator:
    def __init__(self, root):
        self.root = root
        self.root.title("AOBF statystic 2.0 (Mann-Whitney U test)")
        self.root.geometry("650x500")

        self.df_a = None
        self.df_b = None
        self.name_a = ""
        self.name_b = ""

        # --- GUI ---
        tk.Label(root, text="Porovnanie Včelnice A vs. Včelnice B", font=("Arial", 16, "bold")).pack(pady=15)
        tk.Label(root, text="(Vrátane medu, plodu a P-hodnôt)", font=("Arial", 10)).pack(pady=5)
        
        # Včelnica A
        self.frame_a = tk.Frame(root)
        self.frame_a.pack(pady=5)
        self.btn_a = tk.Button(self.frame_a, text="1. Načítať Excel Včelnice A", command=self.load_a, width=30)
        self.btn_a.pack(side=tk.LEFT, padx=5)
        self.ent_a_name = tk.Entry(self.frame_a, width=15)
        self.ent_a_name.insert(0, "Včelnica A")
        self.ent_a_name.pack(side=tk.LEFT)

        # Včelnica B
        self.frame_b = tk.Frame(root)
        self.frame_b.pack(pady=5)
        self.btn_b = tk.Button(self.frame_b, text="2. Načítať Excel Včelnice B", command=self.load_b, width=30)
        self.btn_b.pack(side=tk.LEFT, padx=5)
        self.ent_b_name = tk.Entry(self.frame_b, width=15)
        self.ent_b_name.insert(0, "Včelnica B")
        self.ent_b_name.pack(side=tk.LEFT)

        tk.Label(root, text="------------------------------------------------", pady=10).pack()

        self.btn_run = tk.Button(root, text="SPUSTIŤ POROVNANIE", command=self.run_comparison, bg="#aaffaa", font=("Arial", 12, "bold"), state=tk.DISABLED, height=2)
        self.btn_run.pack(pady=15)

        self.status_lbl = tk.Label(root, text="Čakám na súbory...", fg="gray")
        self.status_lbl.pack(pady=5)

    def load_excel(self):
        path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if not path: return None, None
        
        try:
            xl = pd.ExcelFile(path)
            sheet_name = None
            # Hľadáme hárok s dátami (ignorujeme hárok s p-hodnotami z minula)
            for s in xl.sheet_names:
                if "Zdrojove" in s or "Data" in s or "Vsetky" in s:
                    sheet_name = s
                    break
            
            if sheet_name:
                df = pd.read_excel(path, sheet_name=sheet_name)
            else:
                # Ak nenájde špecifický, vezme posledný (často tam sú dáta)
                df = pd.read_excel(path, sheet_name=-1)

            # Čistenie a konverzia na čísla
            cols_to_numeric = ['Parafin_Percento', 'Vystavane_Percent', 'Med_Percent', 'Plod_Percent']
            for c in cols_to_numeric:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
            
            return df, os.path.basename(path)
        except Exception as e:
            messagebox.showerror("Chyba", f"Nepodarilo sa načítať: {e}")
            return None, None

    def load_a(self):
        df, name = self.load_excel()
        if df is not None:
            self.df_a = df
            self.btn_a.config(bg="#ccffcc", text=f"A: {name}")
            self.check_ready()

    def load_b(self):
        df, name = self.load_excel()
        if df is not None:
            self.df_b = df
            self.btn_b.config(bg="#ccffcc", text=f"B: {name}")
            self.check_ready()

    def check_ready(self):
        if self.df_a is not None and self.df_b is not None:
            self.btn_run.config(state=tk.NORMAL)
            self.status_lbl.config(text="Pripravené na analýzu.", fg="green")

    def run_comparison(self):
        self.name_a = self.ent_a_name.get()
        self.name_b = self.ent_b_name.get()

        self.df_a['Vcelnica'] = self.name_a
        self.df_b['Vcelnica'] = self.name_b
        
        full_df = pd.concat([self.df_a, self.df_b], ignore_index=True)
        
        output_dir = "Porovnanie_Vcelnic_Detail"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        try:
            # === GRAF 1: Celkové Vystavanie (Boxplot/Barplot) ===
            plt.figure(figsize=(10, 6))
            sns.barplot(
                data=full_df, 
                x="Meranie_Nazov", 
                y="Vystavane_Percent", 
                hue="Vcelnica",
                palette="pastel",
                errorbar='sd', capsize=.1
            )
            plt.title("Celková aktivita stavby (Všetky rámiky)")
            plt.ylabel("Priemerné vystavanie (%)")
            plt.ylim(0, 100) # Tu necháme 100, lebo stavba býva vysoká
            plt.savefig(f"{output_dir}/1_Celkove_Vystavanie.png")
            plt.close()

            # === GRAF 2: Vystavanie vs. Parafín (Lineplot) ===
            self.create_comparison_lineplot(
                data=full_df, 
                x="Parafin_Percento", 
                y="Vystavane_Percent", 
                title="Vplyv parafínu na Vystavanie (Porovnanie včelníc)",
                ylabel="Vystavané (%)",
                filename=f"{output_dir}/2_Vystavanie_vs_Parafin.png",
                ylim_100=True
            )

            # === GRAF 3: MED vs. Parafín (Lineplot - Len Medníky) ===
            df_med = full_df[full_df['Lokacia'] == 'Medník']
            if not df_med.empty:
                self.create_comparison_lineplot(
                    data=df_med, 
                    x="Parafin_Percento", 
                    y="Med_Percent", 
                    title="Množstvo MEDU podľa parafínu (Len Medníky)",
                    ylabel="Plocha Medu (%)",
                    filename=f"{output_dir}/3_Med_vs_Parafin.png",
                    ylim_100=False # Dynamická os
                )

            # === GRAF 4: PLOD vs. Parafín (Lineplot - Len Plodiská) ===
            df_plod = full_df[full_df['Lokacia'] == 'Plodisko']
            if not df_plod.empty:
                self.create_comparison_lineplot(
                    data=df_plod, 
                    x="Parafin_Percento", 
                    y="Plod_Percent", 
                    title="Množstvo PLODU podľa parafínu (Len Plodiská)",
                    ylabel="Plocha Plodu (%)",
                    filename=f"{output_dir}/4_Plod_vs_Parafin.png",
                    ylim_100=False # Dynamická os
                )

            # === EXCEL REPORT (Štatistika) ===
            self.export_comparison_stats(full_df, output_dir)

            messagebox.showinfo("Hotovo", f"Analýza úspešná!\n\nGrafy a Excel sú v priečinku:\n{output_dir}\n\nSkontroluj 'Porovnanie_Statistika.xlsx' pre P-hodnoty.")

        except Exception as e:
            messagebox.showerror("Chyba", f"Chyba pri porovnaní: {e}")
            print(e)

    def create_comparison_lineplot(self, data, x, y, title, ylabel, filename, ylim_100=True):
        plt.figure(figsize=(10, 6))
        
        # Vykreslenie s SD (Standard Deviation)
        sns.lineplot(
            data=data,
            x=x,
            y=y,
            hue="Vcelnica",
            style="Vcelnica",
            markers=True, dashes=False, linewidth=3,
            errorbar='sd', err_style='bars', err_kws={'capsize': 5}
        )
        
        plt.title(title)
        plt.ylabel(ylabel)
        plt.xlabel("Parafín (%)")
        
        # Dynamická alebo fixná os
        if ylim_100:
            plt.ylim(0, 100)
        else:
            plt.ylim(bottom=0) # Len spodný limit fixný
            
        plt.grid(True, alpha=0.3)
        plt.savefig(filename)
        plt.close()

    def export_comparison_stats(self, df, output_dir):
        """Porovná A vs B pomocou Mann-Whitney U testu pre Vystavanie, Med aj Plod"""
        stats_rows = []
        
        scenarios = [
            ("Vystavanie", "Vystavane_Percent", "Všetko"),
            ("Množstvo Medu", "Med_Percent", "Medník"),
            ("Množstvo Plodu", "Plod_Percent", "Plodisko")
        ]
        
        # Prechádzame každé meranie (čas)
        for meranie in df['Meranie_Nazov'].unique():
            subset_time = df[df['Meranie_Nazov'] == meranie]
            
            for param_name, col_name, loc_filter in scenarios:
                if col_name not in df.columns: continue

                # Filter na lokáciu (ak treba)
                if loc_filter == "Medník":
                    data_to_test = subset_time[subset_time['Lokacia'] == 'Medník']
                elif loc_filter == "Plodisko":
                    data_to_test = subset_time[subset_time['Lokacia'] == 'Plodisko']
                else:
                    data_to_test = subset_time

                # Rozdelenie na skupiny A a B
                group_a = data_to_test[data_to_test['Vcelnica'] == self.name_a][col_name]
                group_b = data_to_test[data_to_test['Vcelnica'] == self.name_b][col_name]
                
                # Výpočet
                count_a = len(group_a)
                count_b = len(group_b)
                mean_a = group_a.mean() if count_a > 0 else 0
                mean_b = group_b.mean() if count_b > 0 else 0
                
                p_val_text = "N/A"
                zaver = "Málo dát"
                
                if count_a > 1 and count_b > 1:
                    try:
                        # --- OPRAVA: Použitie Mann-Whitney U testu namiesto T-testu ---
                        u_stat, p_val = stats.mannwhitneyu(group_a, group_b, alternative='two-sided')
                        p_val_text = round(p_val, 4)
                        zaver = "VÝZNAMNÝ ROZDIEL" if p_val < 0.05 else "Rovnaké"
                    except:
                        zaver = "Chyba"
                
                stats_rows.append({
                    "Meranie": meranie,
                    "Parameter": param_name,
                    "Lokalita": loc_filter,
                    f"Priemer {self.name_a}": round(mean_a, 2),
                    f"Priemer {self.name_b}": round(mean_b, 2),
                    "Rozdiel": round(mean_a - mean_b, 2),
                    "P-hodnota": p_val_text,
                    "Záver": zaver
                })

        # Uloženie do Excelu
        stats_df = pd.DataFrame(stats_rows)
        with pd.ExcelWriter(f"{output_dir}/Porovnanie_Statistika.xlsx") as writer:
            if not stats_df.empty:
                stats_df.to_excel(writer, sheet_name='Porovnanie_A_vs_B', index=False)
            else:
                 pd.DataFrame({"Info": ["Žiadne dáta"]}).to_excel(writer, sheet_name='Porovnanie_A_vs_B', index=False)
            
            df.to_excel(writer, sheet_name='Spojene_Data', index=False)

if __name__ == "__main__":
    root = tk.Tk()
    app = ApiaryComparator(root)
    root.mainloop()