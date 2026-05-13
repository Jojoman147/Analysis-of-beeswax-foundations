import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats
import os
import numpy as np

# Visual settings for publication-quality charts
sns.set_theme(style="whitegrid")

class BeeStatAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("AOBF Statistics 4.0 (Mann-Whitney + Post-Hoc)")
        self.root.geometry("650x600")

        self.data_frames = {} 
        self.merged_df = None

        # --- GUI Setup ---
        tk.Label(root, text="Scientific Analysis (Post-Hoc Version)", font=("Arial", 16, "bold")).pack(pady=10)
        tk.Label(root, text="(Mann-Whitney Test + Bonferroni Post-Hoc Correction)", font=("Arial", 10)).pack(pady=5)

        self.btn_1 = tk.Button(root, text="1. Load First Measurement", command=lambda: self.load_file(1), width=45)
        self.btn_1.pack(pady=5)
        
        self.btn_2 = tk.Button(root, text="2. Load Second Measurement", command=lambda: self.load_file(2), width=45)
        self.btn_2.pack(pady=5)
        
        self.btn_3 = tk.Button(root, text="3. Load Third Measurement", command=lambda: self.load_file(3), width=45)
        self.btn_3.pack(pady=5)

        tk.Label(root, text="------------------------------------------------", pady=10).pack()

        self.btn_run = tk.Button(root, text="GENERATE CHARTS AND STATISTICS", command=self.run_analysis, bg="#aaffaa", font=("Arial", 11, "bold"), state=tk.DISABLED, height=2)
        self.btn_run.pack(pady=10)

        self.status_lbl = tk.Label(root, text="Waiting for files...", fg="gray")
        self.status_lbl.pack(pady=5)

    def load_file(self, measure_num):
        path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if path:
            try:
                df = pd.read_excel(path)
                
                # Data cleaning and numeric conversion
                # IMPORTANT: Your Excel columns should now match these names
                cols_to_numeric = ['Paraffin_Percentage', 'Drawn_Out_Percentage', 'Honey_Percentage', 'Brood_Percentage']
                for c in cols_to_numeric:
                    if c in df.columns:
                        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
                        
                df['Measurement_ID'] = measure_num
                df['Measurement_Name'] = f"Measurement {measure_num}"
                self.data_frames[measure_num] = df
                
                btn = [self.btn_1, self.btn_2, self.btn_3][measure_num-1]
                btn.config(bg="#ccffcc", text=f"Measurement {measure_num}: {os.path.basename(path)}")
                
                if len(self.data_frames) == 3:
                    self.btn_run.config(state=tk.NORMAL)
                    self.status_lbl.config(text="Ready.", fg="green")
            except Exception as e:
                messagebox.showerror("Error", f"Loading failed: {e}")

    def run_analysis(self):
        # Merge dataframes
        df_list = [self.data_frames[1], self.data_frames[2], self.data_frames[3]]
        self.merged_df = pd.concat(df_list, ignore_index=True)
        
        output_dir = "PostHoc_Analysis_Results"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        try:
            # === GENERATING CHARTS ===
            
            # 1. PARAFFIN vs COMB CONSTRUCTION (Overall)
            self.create_significance_plot(
                data=self.merged_df,
                x="Paraffin_Percentage",
                y="Drawn_Out_Percentage",
                title="Impact of Paraffin on Comb Construction (Overall)",
                filename=f"{output_dir}/1_Paraffin_Drawing_PostHoc.png",
                ylabel="Drawn-out Area (%)",
                fix_100=True
            )

            # 2. PARAFFIN vs HONEY (Honey Supers Only)
            df_honey_super = self.merged_df[self.merged_df['Location'] == 'Honey Super']
            if not df_honey_super.empty:
                self.create_significance_plot(
                    data=df_honey_super,
                    x="Paraffin_Percentage",
                    y="Honey_Percentage",
                    title="Impact of Paraffin on Honey Storage (Honey Supers)",
                    filename=f"{output_dir}/2_Paraffin_Honey_PostHoc.png",
                    ylabel="Honey Area (%)",
                    fix_100=False
                )

            # 3. PARAFFIN vs BROOD (Brood Chambers Only)
            df_brood_chamber = self.merged_df[self.merged_df['Location'] == 'Brood Chamber']
            if not df_brood_chamber.empty:
                self.create_significance_plot(
                    data=df_brood_chamber,
                    x="Paraffin_Percentage",
                    y="Brood_Percentage",
                    title="Impact of Paraffin on Brood Rearing (Brood Chambers)",
                    filename=f"{output_dir}/3_Paraffin_Brood_PostHoc.png",
                    ylabel="Brood Area (%)",
                    fix_100=False
                )

            # 4. HONEY SUPER vs BROOD CHAMBER (Comparison Barplot)
            plt.figure(figsize=(10, 6))
            ax = sns.barplot(
                data=self.merged_df, 
                x="Measurement_Name", 
                y="Drawn_Out_Percentage", 
                hue="Location", 
                palette="viridis",
                errorbar='sd',
                capsize=.1
            )
            plt.title("Comparison: Brood Chamber vs. Honey Super (+ SD)")
            plt.ylabel("Drawn-out Area (%)")
            plt.ylim(0, 100)
            plt.savefig(f"{output_dir}/4_Location_Comparison_SD.png")
            plt.close()

            # === EXPORT TO EXCEL ===
            self.export_stats_excel(output_dir)

            messagebox.showinfo("Done", f"Analysis complete!\n\n* = Significant difference (with Bonferroni correction, p<0.05)\n\nFiles saved in: {output_dir}")

        except Exception as e:
            messagebox.showerror("Error", f"Generation failed: {e}")
            print(e)

    def create_significance_plot(self, data, x, y, title, filename, ylabel, fix_100=False):
        plt.figure(figsize=(11, 7))
        
        ax = sns.lineplot(
            data=data, 
            x=x, 
            y=y, 
            hue="Measurement_Name", 
            style="Measurement_Name",
            markers=True, 
            dashes=False, 
            linewidth=2,
            errorbar='sd',
            err_style="bars",
            err_kws={'capsize': 5}
        )

        measures = data['Measurement_Name'].unique()
        paraffin_levels = sorted(data[x].unique())
        
        for measure in measures:
            subset = data[data['Measurement_Name'] == measure]
            baseline_data = subset[subset[x] == 0][y]
            
            if len(baseline_data) < 2:
                continue 
            
            # Number of comparisons for Bonferroni correction
            comparison_count = len([l for l in paraffin_levels if l != 0])
            
            for level in paraffin_levels:
                if level == 0: continue
                
                compare_data = subset[subset[x] == level][y]
                if len(compare_data) < 2: 
                    continue

                try:
                    u_stat, p_val_raw = stats.mannwhitneyu(baseline_data, compare_data, alternative='two-sided')
                    
                    # POST-HOC CORRECTION (Bonferroni)
                    p_val_adj = min(p_val_raw * comparison_count, 1.0)
                    
                    # Add star marker only if significant AFTER correction
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
        plt.xlabel("Paraffin Content (%)")
        
        if fix_100:
            plt.ylim(0, 100)
        else:
            plt.ylim(bottom=0)
            current_top = plt.ylim()[1]
            if current_top > 100:
                plt.ylim(0, 100)

        plt.grid(True, alpha=0.3)
        plt.legend(title="Measurement")
        plt.savefig(filename)
        plt.close()

    def export_stats_excel(self, output_dir):
        stats_rows = []
        
        scenarios = [
            ("Comb Construction", "Drawn_Out_Percentage"),
            ("Honey Storage", "Honey_Percentage"),
            ("Brood Rearing", "Brood_Percentage")
        ]
        
        for name_metric, col_metric in scenarios:
            if col_metric not in self.merged_df.columns: continue
            
            for measure in self.merged_df['Measurement_Name'].unique():
                subset = self.merged_df[self.merged_df['Measurement_Name'] == measure]
                baseline = subset[subset['Paraffin_Percentage'] == 0][col_metric]
                
                if len(baseline) < 2: continue
                
                # Get comparison count for Post-hoc
                levels_to_compare = [l for l in sorted(subset['Paraffin_Percentage'].unique()) if l != 0]
                comparison_count = len(levels_to_compare)
                
                for level in levels_to_compare:
                    group = subset[subset['Paraffin_Percentage'] == level][col_metric]
                    if len(group) < 2: continue
                    
                    try:
                        u_stat, p_val_raw = stats.mannwhitneyu(baseline, group, alternative='two-sided')
                        
                        # POST-HOC CORRECTION (Bonferroni)
                        p_val_adj = min(p_val_raw * comparison_count, 1.0)
                        
                        significance = "SIGNIFICANT" if p_val_adj < 0.05 else "Non-significant"
                    except:
                        p_val_raw = "N/A"
                        p_val_adj = "N/A"
                        significance = "Error"
                    
                    stats_rows.append({
                        "Measurement": measure,
                        "Parameter": name_metric,
                        "Comparison": f"{level}% vs 0%",
                        "Mean_Difference": round(group.mean() - baseline.mean(), 2),
                        "P-value (Original)": round(p_val_raw, 4) if isinstance(p_val_raw, float) else p_val_raw,
                        "P-value (Bonferroni Post-Hoc)": round(p_val_adj, 4) if isinstance(p_val_adj, float) else p_val_adj,
                        "Conclusion (Post-Hoc)": significance
                    })

        df_stats = pd.DataFrame(stats_rows)
        excel_path = f"{output_dir}/PostHoc_Statistics.xlsx"
        
        with pd.ExcelWriter(excel_path) as writer:
            if not df_stats.empty:
                df_stats.to_excel(writer, sheet_name='Mann-Whitney_PostHoc', index=False)
            self.merged_df.to_excel(writer, sheet_name='Raw_Data', index=False)

if __name__ == "__main__":
    root = tk.Tk()
    app = BeeStatAnalyzer(root)
    root.mainloop()