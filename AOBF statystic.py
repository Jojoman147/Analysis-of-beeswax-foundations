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
        self.root.title("Včelár Štatistika 3.0 - Vedecká analýza")
        self.root.geometry("650x600")

        self.data_frames = {} 
        self.merged_df = None

        # --- GUI ---
        tk.Label(root, text="Vedecká analýza 3 meraní", font=("Arial", 16, "bold")).pack(pady=10)
        tk.Label(root, text="(Porovnanie voči 0% parafínu + Štandardná odchýlka)", font=("Arial", 10)).pack(pady=5)

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
        
        output_dir = "Vystup_Vedecka_Analyza"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        try:
            # === GENERUJEME GRAFY ===
            
            # 1. PARAFÍN vs VYSTAVANIE (Všetko)
            self.create_significance_plot(
                data=self.merged_df,
                x="Parafin_Percento",
                y="Vystavane_Percent",
                title="Vplyv parafínu na Vystavanie (Celkovo)",
                filename=f"{output_dir}/1_Parafin_Vystavanie_SD.png",
                ylabel="Vystavaná plocha (%)"
            )

            # 2. PARAFÍN vs MED (Len Medník)
            df_mednik = self.merged_df[self.merged_df['Lokacia'] == 'Medník']
            if not df_mednik.empty:
                self.create_significance_plot(
                    data=df_mednik,
                    x="Parafin_Percento",
                    y="Med_Percent",
                    title="Vplyv parafínu na zásoby MEDU (Medníky)",
                    filename=f"{output_dir}/2_Parafin_MED_Mednik_SD.png",
                    ylabel="Plocha Medu (%)"
                )

            # 3. PARAFÍN vs PLOD (Len Plodisko)
            df_plodisko = self.merged_df[self.merged_df['Lokacia'] == 'Plodisko']
            if not df_plodisko.empty:
                self.create_significance_plot(
                    data=df_plodisko,
                    x="Parafin_Percento",
                    y="Plod_Percent",
                    title="Vplyv parafínu na PLODOVANIE (Plodiská)",
                    filename=f"{output_dir}/3_Parafin_PLOD_Plodisko_SD.png",
                    ylabel="Plocha Plodu (%)"
                )

            # 4. MEDNÍK vs PLODISKO (Barplot)
            plt.figure(figsize=(10, 6))
            ax = sns.barplot(
                data=self.merged_df, 
                x="Meranie_Nazov", 
                y="Vystavane_Percent", 
                hue="Lokacia", 
                palette="viridis",
                errorbar='sd', # Štandardná odchýlka
                capsize=.1
            )
            plt.title("Porovnanie Plodisko vs. Medník (+ SD)")
            plt.ylabel("Vystavané (%)")
            plt.ylim(bottom=0) # Len spodný limit, horný je dynamický
            plt.savefig(f"{output_dir}/4_Porovnanie_Lokacii_SD.png")
            plt.close()

            # === EXPORT DO EXCELU ===
            self.export_stats_excel(output_dir)

            messagebox.showinfo("Hotovo", f"Analýza dokončená!\n\nLegenda ku grafom:\n* = Štatisticky významný rozdiel oproti 0% (p<0.05)\nZvislé čiary = Štandardná odchýlka\n\nSúbory sú v: {output_dir}")

        except Exception as e:
            messagebox.showerror("Chyba", f"Chyba pri generovaní: {e}")
            print(e)

    def create_significance_plot(self, data, x, y, title, filename, ylabel):
        """
        Univerzálna funkcia na vytvorenie grafu s T-testom voči 0%.
        """
        plt.figure(figsize=(11, 7))
        
        # 1. Vykreslenie grafu s SD
        ax = sns.lineplot(
            data=data, 
            x=x, 
            y=y, 
            hue="Meranie_Nazov", 
            style="Meranie_Nazov",
            markers=True, 
            dashes=False, 
            linewidth=2,
            errorbar='sd', # Zobrazujeme Štandardnú odchýlku
            err_style="bars",
            err_kws={'capsize': 5}
        )

        # 2. Výpočet štatistickej významnosti voči 0%
        # Získame unikátne merania
        merania = data['Meranie_Nazov'].unique()
        parafin_levels = sorted(data[x].unique())
        
        # Pre každé meranie (jún, júl...) zvlášť
        for meranie in merania:
            subset = data[data['Meranie_Nazov'] == meranie]
            
            # Baseline dáta (0% parafín pre dané meranie)
            baseline_data = subset[subset[x] == 0][y]
            
            if len(baseline_data) < 2:
                continue # Nemáme dosť dát na porovnanie
            
            # Iterujeme cez ostatné úrovne parafínu (10, 20...)
            for level in parafin_levels:
                if level == 0: continue
                
                compare_data = subset[subset[x] == level][y]
                
                if len(compare_data) < 2: 
                    continue

                # T-TEST
                stat, p_val = stats.ttest_ind(baseline_data, compare_data, equal_var=False)
                
                # Ak je významný rozdiel (p < 0.05)
                if p_val < 0.05:
                    # Nájdeme súradnice pre hviezdičku
                    mean_val = compare_data.mean()
                    std_val = compare_data.std()
                    
                    # Offset pre text (aby bol nad chybovou úsečkou)
                    # Ak je std NaN (jeden bod), použijeme malý offset
                    offset = std_val if not pd.isna(std_val) else 0
                    
                    # Pridanie hviezdičky do grafu
                    # Musíme nájsť farbu čiary pre dané meranie, ale pre zjednodušenie dáme červenú
                    plt.text(
                        x=level, 
                        y=mean_val + offset + (data[y].max() * 0.02), # Trochu nad SD
                        s="*", 
                        color='red', 
                        fontweight='bold', 
                        fontsize=14,
                        ha='center'
                    )

        plt.title(title)
        plt.ylabel(ylabel)
        plt.xlabel("Obsah Parafínu (%)")
        plt.ylim(bottom=0) # Dynamická Y os (len spodok fixujeme na 0)
        plt.grid(True, alpha=0.3)
        plt.legend(title="Meranie")
        plt.savefig(filename)
        plt.close()

    def export_stats_excel(self, output_dir):
        """Urobí detailný export p-hodnôt do Excelu"""
        stats_rows = []
        
        # Pre každú kombináciu: Meranie + Lokácia + Premenná
        scenarios = [
            ("Vystavanie", "Vystavane_Percent"),
            ("Množstvo Medu", "Med_Percent"),
            ("Množstvo Plodu", "Plod_Percent")
        ]
        
        for name_metric, col_metric in scenarios:
            for meranie in self.merged_df['Meranie_Nazov'].unique():
                subset = self.merged_df[self.merged_df['Meranie_Nazov'] == meranie]
                baseline = subset[subset['Parafin_Percento'] == 0][col_metric]
                
                if len(baseline) < 2: continue
                
                for level in sorted(subset['Parafin_Percento'].unique()):
                    if level == 0: continue
                    
                    group = subset[subset['Parafin_Percento'] == level][col_metric]
                    if len(group) < 2: continue
                    
                    t_stat, p_val = stats.ttest_ind(baseline, group, equal_var=False)
                    significance = "VÝZNAMNÝ" if p_val < 0.05 else "Nevýznamný"
                    
                    stats_rows.append({
                        "Meranie": meranie,
                        "Parameter": name_metric,
                        "Porovnanie": f"{level}% vs 0%",
                        "Rozdiel_Priemerov": round(group.mean() - baseline.mean(), 2),
                        "P-hodnota": round(p_val, 4),
                        "Záver": significance
                    })

        df_stats = pd.DataFrame(stats_rows)
        excel_path = f"{output_dir}/Statistika_P_hodnoty.xlsx"
        
        with pd.ExcelWriter(excel_path) as writer:
            self.merged_df.to_excel(writer, sheet_name='Zdrojove_Data', index=False)
            df_stats.to_excel(writer, sheet_name='T-testy_voci_kontrole', index=False)

if __name__ == "__main__":
    root = tk.Tk()
    app = BeeStatAnalyzer(root)
    root.mainloop()