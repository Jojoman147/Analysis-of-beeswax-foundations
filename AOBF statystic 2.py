import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats
import os

# Visual settings
sns.set_theme(style="whitegrid")

class ApiaryComparator:
    def __init__(self, root):
        self.root = root
        self.root.title("AOBF Statistics 2.1 (Mann-Whitney U test)")
        self.root.geometry("650x500")

        self.df_a = None
        self.df_b = None
        self.name_a = ""
        self.name_b = ""

        # --- GUI Setup ---
        tk.Label(root, text="Comparison: Apiary A vs. Apiary B", font=("Arial", 16, "bold")).pack(pady=15)
        tk.Label(root, text="(Including Honey, Brood, and P-values)", font=("Arial", 10)).pack(pady=5)
        
        # Apiary A Section
        self.frame_a = tk.Frame(root)
        self.frame_a.pack(pady=5)
        self.btn_a = tk.Button(self.frame_a, text="1. Load Excel: Apiary A", command=self.load_a, width=30)
        self.btn_a.pack(side=tk.LEFT, padx=5)
        self.ent_a_name = tk.Entry(self.frame_a, width=15)
        self.ent_a_name.insert(0, "Apiary A")
        self.ent_a_name.pack(side=tk.LEFT)

        # Apiary B Section
        self.frame_b = tk.Frame(root)
        self.frame_b.pack(pady=5)
        self.btn_b = tk.Button(self.frame_b, text="2. Load Excel: Apiary B", command=self.load_b, width=30)
        self.btn_b.pack(side=tk.LEFT, padx=5)
        self.ent_b_name = tk.Entry(self.frame_b, width=15)
        self.ent_b_name.insert(0, "Apiary B")
        self.ent_b_name.pack(side=tk.LEFT)

        tk.Label(root, text="------------------------------------------------", pady=10).pack()

        self.btn_run = tk.Button(root, text="RUN COMPARISON", command=self.run_comparison, bg="#aaffaa", font=("Arial", 12, "bold"), state=tk.DISABLED, height=2)
        self.btn_run.pack(pady=15)

        self.status_lbl = tk.Label(root, text="Waiting for files...", fg="gray")
        self.status_lbl.pack(pady=5)

    def load_excel(self):
        path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if not path: return None, None
        
        try:
            xl = pd.ExcelFile(path)
            sheet_name = None
            # Searching for the data sheet (ignoring previous stats sheets)
            for s in xl.sheet_names:
                if "Raw" in s or "Data" in s or "All" in s or "Zdrojove" in s:
                    sheet_name = s
                    break
            
            if sheet_name:
                df = pd.read_excel(path, sheet_name=sheet_name)
            else:
                # If no specific sheet is found, take the last one
                df = pd.read_excel(path, sheet_name=-1)

            # Data cleaning and numeric conversion
            # Note: Ensure your Excel headers match these English names or keep them as in your original file
            cols_to_numeric = ['Paraffin_Percentage', 'Drawn_Out_Percentage', 'Honey_Percentage', 'Brood_Percentage']
            for c in cols_to_numeric:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
            
            return df, os.path.basename(path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {e}")
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
            self.status_lbl.config(text="Ready for analysis.", fg="green")

    def run_comparison(self):
        self.name_a = self.ent_a_name.get()
        self.name_b = self.ent_b_name.get()

        self.df_a['Apiary'] = self.name_a
        self.df_b['Apiary'] = self.name_b
        
        full_df = pd.concat([self.df_a, self.df_b], ignore_index=True)
        
        output_dir = "Apiary_Comparison_Detail"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        try:
            # === PLOT 1: Overall Drawing Activity (Barplot) ===
            plt.figure(figsize=(10, 6))
            sns.barplot(
                data=full_df, 
                x="Measurement_Name", 
                y="Drawn_Out_Percentage", 
                hue="Apiary",
                palette="pastel",
                errorbar='sd', capsize=.1
            )
            plt.title("Overall Comb Building Activity (All Frames)")
            plt.ylabel("Average Drawn-out Area (%)")
            plt.ylim(0, 100)
            plt.savefig(f"{output_dir}/1_Overall_Drawing_Activity.png")
            plt.close()

            # === PLOT 2: Drawing Out vs. Paraffin (Lineplot) ===
            self.create_comparison_lineplot(
                data=full_df, 
                x="Paraffin_Percentage", 
                y="Drawn_Out_Percentage", 
                title="Impact of Paraffin on Comb Construction",
                ylabel="Drawn-out Area (%)",
                filename=f"{output_dir}/2_Drawing_vs_Paraffin.png",
                ylim_100=True
            )

            # === PLOT 3: Honey vs. Paraffin (Lineplot - Honey Supers Only) ===
            df_honey = full_df[full_df['Location'] == 'Honey Super']
            if not df_honey.empty:
                self.create_comparison_lineplot(
                    data=df_honey, 
                    x="Paraffin_Percentage", 
                    y="Honey_Percentage", 
                    title="Honey Storage by Paraffin Content (Honey Supers)",
                    ylabel="Honey Area (%)",
                    filename=f"{output_dir}/3_Honey_vs_Paraffin.png",
                    ylim_100=False
                )

            # === PLOT 4: Brood vs. Paraffin (Lineplot - Brood Chambers Only) ===
            df_brood = full_df[full_df['Location'] == 'Brood Chamber']
            if not df_brood.empty:
                self.create_comparison_lineplot(
                    data=df_brood, 
                    x="Paraffin_Percentage", 
                    y="Brood_Percentage", 
                    title="Brood Rearing by Paraffin Content (Brood Chambers)",
                    ylabel="Brood Area (%)",
                    filename=f"{output_dir}/4_Brood_vs_Paraffin.png",
                    ylim_100=False
                )

            # === EXCEL REPORT (Statistics) ===
            self.export_comparison_stats(full_df, output_dir)

            messagebox.showinfo("Success", f"Analysis complete!\n\nCharts and Excel are in:\n{output_dir}\n\nCheck 'Comparison_Statistics.xlsx' for P-values.")

        except Exception as e:
            messagebox.showerror("Error", f"Comparison failed: {e}")
            print(e)

    def create_comparison_lineplot(self, data, x, y, title, ylabel, filename, ylim_100=True):
        plt.figure(figsize=(10, 6))
        
        # Plot with Standard Deviation (SD)
        sns.lineplot(
            data=data,
            x=x,
            y=y,
            hue="Apiary",
            style="Apiary",
            markers=True, dashes=False, linewidth=3,
            errorbar='sd', err_style='bars', err_kws={'capsize': 5}
        )
        
        plt.title(title)
        plt.ylabel(ylabel)
        plt.xlabel("Paraffin Content (%)")
        
        if ylim_100:
            plt.ylim(0, 100)
        else:
            plt.ylim(bottom=0)
            
        plt.grid(True, alpha=0.3)
        plt.savefig(filename)
        plt.close()

    def export_comparison_stats(self, df, output_dir):
        """Compares Apiary A vs B using Mann-Whitney U test"""
        stats_rows = []
        
        scenarios = [
            ("Comb Building", "Drawn_Out_Percentage", "All"),
            ("Honey Storage", "Honey_Percentage", "Honey Super"),
            ("Brood Rearing", "Brood_Percentage", "Brood Chamber")
        ]
        
        for measurement in df['Measurement_Name'].unique():
            subset_time = df[df['Measurement_Name'] == measurement]
            
            for param_name, col_name, loc_filter in scenarios:
                if col_name not in df.columns: continue

                # Filter by location
                if loc_filter == "Honey Super":
                    data_to_test = subset_time[subset_time['Location'] == 'Honey Super']
                elif loc_filter == "Brood Chamber":
                    data_to_test = subset_time[subset_time['Location'] == 'Brood Chamber']
                else:
                    data_to_test = subset_time

                # Grouping A and B
                group_a = data_to_test[data_to_test['Apiary'] == self.name_a][col_name]
                group_b = data_to_test[data_to_test['Apiary'] == self.name_b][col_name]
                
                count_a = len(group_a)
                count_b = len(group_b)
                mean_a = group_a.mean() if count_a > 0 else 0
                mean_b = group_b.mean() if count_b > 0 else 0
                
                p_val_text = "N/A"
                conclusion = "Insufficient Data"
                
                if count_a > 1 and count_b > 1:
                    try:
                        u_stat, p_val = stats.mannwhitneyu(group_a, group_b, alternative='two-sided')
                        p_val_text = round(p_val, 4)
                        conclusion = "SIGNIFICANT DIFFERENCE" if p_val < 0.05 else "No Difference"
                    except:
                        conclusion = "Error"
                
                stats_rows.append({
                    "Measurement": measurement,
                    "Parameter": param_name,
                    "Location": loc_filter,
                    f"Mean {self.name_a}": round(mean_a, 2),
                    f"Mean {self.name_b}": round(mean_b, 2),
                    "Difference": round(mean_a - mean_b, 2),
                    "P-value": p_val_text,
                    "Conclusion": conclusion
                })

        # Save to Excel
        stats_df = pd.DataFrame(stats_rows)
        with pd.ExcelWriter(f"{output_dir}/Comparison_Statistics.xlsx") as writer:
            if not stats_df.empty:
                stats_df.to_excel(writer, sheet_name='Comparison_A_vs_B', index=False)
            df.to_excel(writer, sheet_name='Merged_Data', index=False)

if __name__ == "__main__":
    root = tk.Tk()
    app = ApiaryComparator(root)
    root.mainloop()