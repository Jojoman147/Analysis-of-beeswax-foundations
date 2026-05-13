import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats
import os
import numpy as np

# Nastavenie vizuálu
sns.set_theme(style="whitegrid")

class BeeStatAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("AOBF statystic 4.0 (Mann-Whitney + Post-Hoc)")
        self.root.geometry("650x600")

        self.data_frames = {} 
        self.merged_df = None

        # --- GUI ---
        tk.Label(root, text="Vedecká analýza (Post-Hoc verzia)", font=("Arial", 16, "bold")).pack(pady=10)
        tk.Label(root, text="(Mann-Whitney test + Bonferroni post-hoc korekcia)", font=("Arial", 10)).pack(pady=5)

        self.btn_1 = tk.Button(root, text="1. Načítať Prvé Meranie", command=lambda: self.load_file(1), width=45)
        self.btn_1.pack(pady=5)
        
        self.btn_2 = tk.Button(root, text="2. Načítať Druhé Meranie", command=lambda: self.load_file(2), width=45)
        self.btn_2.pack(pady=5)
        
        self.btn_3 = tk.Button(root, text="3. Načítať Tretie Meranie", command=lambda: self.load_file(3), width=45)
        self.btn_3.pack(pady=5)

        tk.Label(root, text="------------------------------------------------", pady=10).pack()

        self.btn_run = tk.Button(root, text="GENERUJ GRAFY A ŠTATISTIKU", command=self.run_analysis, bg="#aaffaa", font=("Arial", 11, "bold"), state=tk.DISABLED, height=2)
        self.btn_run.pack(pady=10)

        self.status_lbl = tk.Label(root, text="Čakám na súbory...", fg="gray")
        self.status_lbl.pack(pady=5)

    def load_file(self, measure_num):
        path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if path:
            try:
                df = pd.read_excel(path)
                
                # Čistenie dát pri načítaní
                cols_to_numeric = ['Parafin_Percento', 'Vystavane_Percent', 'Med_Percent', 'Plod_Percent']
                for c in cols_to_numeric:
                    if c in df.columns:
                        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
                        
                df['Meranie_ID'] = measure_num
                df['Meranie_Nazov'] = f"{measure_num}. Meranie"
                self.data_frames[measure_num] = df
                
                btn = [self.btn_1, self.btn_2, self.btn_3][measure_num-1]
                btn.config(bg="#ccffcc", text=f"Meranie {measure_num}: {os.path.basename(path)}")
                
                if len(self.data_frames) == 3:
                    self.btn_run.config(state=tk.NORMAL)
                    self.status_lbl.config(text="Pripravené.", fg="green")
            except Exception as e:
                messagebox.showerror("Chyba", f"Chyba pri načítaní: {e}")

    def run_analysis(self):
        # Spojenie dát
        df_list = [self.data_frames[1], self.data_frames[2], self.data_frames[3]]
        self.merged_df = pd.concat(df_list, ignore_index=True)
        
        output_dir = "Vystup_PostHoc_Analyza"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        try:
            # === GENERUJEME GRAFY ===
            
            # 1. PARAFÍN vs VYSTAVANIE (Všetko) - Tu fixujeme os do 100%
            self.create_significance_plot(
                data=self.merged_df,
                x="Parafin_Percento",
                y="Vystavane_Percent",
                title="Vplyv parafínu na Vystavanie (Celkovo)",
                filename=f"{output_dir}/1_Parafin_Vystavanie_SD_PostHoc.png",
                ylabel="Vystavaná plocha (%)",
                fix_100=True
            )

            # 2. PARAFÍN vs MED (Len Medník) - Dynamická os
            df_mednik = self.merged_df[self.merged_df['Lokacia'] == 'Medník']
            if not df_mednik.empty:
                self.create_significance_plot(
                    data=df_mednik,
                    x="Parafin_Percento",
                    y="Med_Percent",
                    title="Vplyv parafínu na zásoby MEDU (Medníky)",
                    filename=f"{output_dir}/2_Parafin_MED_Mednik_SD_PostHoc.png",
                    ylabel="Plocha Medu (%)",
                    fix_100=False
                )

            # 3. PARAFÍN vs PLOD (Len Plodisko) - Dynamická os
            df_plodisko = self.merged_df[self.merged_df['Lokacia'] == 'Plodisko']
            if not df_plodisko.empty:
                self.create_significance_plot(
                    data=df_plodisko,
                    x="Parafin_Percento",
                    y="Plod_Percent",
                    title="Vplyv parafínu na PLODOVANIE (Plodiská)",
                    filename=f"{output_dir}/3_Parafin_PLOD_Plodisko_SD_PostHoc.png",
                    ylabel="Plocha Plodu (%)",
                    fix_100=False
                )

            # 4. MEDNÍK vs PLODISKO (Barplot)
            plt.figure(figsize=(10, 6))
            ax = sns.barplot(
                data=self.merged_df, 
                x="Meranie_Nazov", 
                y="Vystavane_Percent", 
                hue="Lokacia", 
                palette="viridis",
                errorbar='sd',
                capsize=.1
            )
            plt.title("Porovnanie Plodisko vs. Medník (+ SD)")
            plt.ylabel("Vystavané (%)")
            plt.ylim(0, 100)
            plt.savefig(f"{output_dir}/4_Porovnanie_Lokacii_SD.png")
            plt.close()

            # === EXPORT DO EXCELU ===
            self.export_stats_excel(output_dir)

            messagebox.showinfo("Hotovo", f"Analýza dokončená!\n\n* = Významný rozdiel (s Bonferroni korekciou, p<0.05)\n\nSúbory sú v: {output_dir}")

        except Exception as e:
            messagebox.showerror("Chyba", f"Chyba pri generovaní: {e}")
            print(e)

    def create_significance_plot(self, data, x, y, title, filename, ylabel, fix_100=False):
        plt.figure(figsize=(11, 7))
        
        ax = sns.lineplot(
            data=data, 
            x=x, 
            y=y, 
            hue="Meranie_Nazov", 
            style="Meranie_Nazov",
            markers=True, 
            dashes=False, 
            linewidth=2,
            errorbar='sd',
            err_style="bars",
            err_kws={'capsize': 5}
        )

        merania = data['Meranie_Nazov'].unique()
        parafin_levels = sorted(data[x].unique())
        
        for meranie in merania:
            subset = data[data['Meranie_Nazov'] == meranie]
            baseline_data = subset[subset[x] == 0][y]
            
            if len(baseline_data) < 2:
                continue 
            
            # Počet porovnaní pre Bonferroniho korekciu
            # Rátame, koľko iných hodnôt parafínu porovnávame voči nule
            pocet_porovnani = len([l for l in parafin_levels if l != 0])
            
            for level in parafin_levels:
                if level == 0: continue
                
                compare_data = subset[subset[x] == level][y]
                if len(compare_data) < 2: 
                    continue

                try:
                    u_stat, p_val_raw = stats.mannwhitneyu(baseline_data, compare_data, alternative='two-sided')
                    
                    # POST-HOC KOREKCIA (Bonferroni)
                    p_val_adj = min(p_val_raw * pocet_porovnani, 1.0)
                    
                    # Hviezdičku dáme iba ak je to významné AJ PO post-hoc korekcii
                    if p_val_adj < 0.05:
                        mean_val = compare_data.mean()
                        std_val = compare_data.std() if not pd.isna(compare_data.std()) else 0
                        
                        y_pos = mean_val + std_val + (data[y].max() * 0.02)
                        if fix_100 and y_pos > 98:
                            y_pos = 98
                            
                        plt.text(
                            x=level, 
                            y=y_pos, 
                            s="*", 
                            color='red', 
                            fontweight='bold', 
                            fontsize=16,
                            ha='center'
                        )
                except Exception:
                    pass

        plt.title(title)
        plt.ylabel(ylabel)
        plt.xlabel("Obsah Parafínu (%)")
        
        if fix_100:
            plt.ylim(0, 100)
        else:
            plt.ylim(bottom=0)
            current_top = plt.ylim()[1]
            if current_top > 100:
                plt.ylim(0, 100)

        plt.grid(True, alpha=0.3)
        plt.legend(title="Meranie")
        plt.savefig(filename)
        plt.close()

    def export_stats_excel(self, output_dir):
        stats_rows = []
        
        scenarios = [
            ("Vystavanie", "Vystavane_Percent"),
            ("Množstvo Medu", "Med_Percent"),
            ("Množstvo Plodu", "Plod_Percent")
        ]
        
        for name_metric, col_metric in scenarios:
            if col_metric not in self.merged_df.columns: continue
            
            for meranie in self.merged_df['Meranie_Nazov'].unique():
                subset = self.merged_df[self.merged_df['Meranie_Nazov'] == meranie]
                baseline = subset[subset['Parafin_Percento'] == 0][col_metric]
                
                if len(baseline) < 2: continue
                
                # Zistíme počet porovnaní pre Post-hoc
                levels_to_compare = [l for l in sorted(subset['Parafin_Percento'].unique()) if l != 0]
                pocet_porovnani = len(levels_to_compare)
                
                for level in levels_to_compare:
                    group = subset[subset['Parafin_Percento'] == level][col_metric]
                    if len(group) < 2: continue
                    
                    try:
                        u_stat, p_val_raw = stats.mannwhitneyu(baseline, group, alternative='two-sided')
                        
                        # POST-HOC KOREKCIA (Bonferroni)
                        p_val_adj = min(p_val_raw * pocet_porovnani, 1.0)
                        
                        significance = "VÝZNAMNÝ" if p_val_adj < 0.05 else "Nevýznamný"
                    except:
                        p_val_raw = "N/A"
                        p_val_adj = "N/A"
                        significance = "Chyba"
                    
                    stats_rows.append({
                        "Meranie": meranie,
                        "Parameter": name_metric,
                        "Porovnanie": f"{level}% vs 0%",
                        "Rozdiel_Priemerov": round(group.mean() - baseline.mean(), 2),
                        "P-hodnota (Pôvodná)": round(p_val_raw, 4) if isinstance(p_val_raw, float) else p_val_raw,
                        "P-hodnota (Bonferroni Post-Hoc)": round(p_val_adj, 4) if isinstance(p_val_adj, float) else p_val_adj,
                        "Záver (podľa Post-Hoc)": significance
                    })

        df_stats = pd.DataFrame(stats_rows)
        excel_path = f"{output_dir}/Statistika_PostHoc.xlsx"
        
        with pd.ExcelWriter(excel_path) as writer:
            if not df_stats.empty:
                df_stats.to_excel(writer, sheet_name='Mann-Whitney_PostHoc', index=False)
            self.merged_df.to_excel(writer, sheet_name='Zdrojove_Data', index=False)

if __name__ == "__main__":
    root = tk.Tk()
    app = BeeStatAnalyzer(root)
    root.mainloop()