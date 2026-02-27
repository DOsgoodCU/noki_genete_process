import pandas as pd
import matplotlib.pyplot as plt
import argparse
import datetime
import os

def process_data(csv_file, only_today=False):
    # Load data
    df = pd.read_csv(csv_file)
    df['created_at'] = pd.to_datetime(df['created_at'])
    
    # Filter for today if requested
    if only_today:
        # Uses the current system date
        today = datetime.datetime.now().date()
        df = df[df['created_at'].dt.date == today]
        if df.empty:
            print(f"No responses found for today ({today}).")
            return None

    # Normalize player types (handling variations in case or spacing)
    df['answer'] = df['answer'].replace({'Petowner': 'Pet Owner'})

    # Extract most recent player type for each user
    player_types = df[df['step_name'].isin(['player_select', 'playerselect'])].sort_values('created_at')
    player_types = player_types.drop_duplicates('user_id', keep='last')[['user_id', 'answer']].rename(columns={'answer': 'player_type'})

    # Extract most recent evacuation choice for each user
    evac_choices = df[df['step_name'] == 'evacuate_select'].sort_values('created_at')
    evac_choices = evac_choices.drop_duplicates('user_id', keep='last')[['user_id', 'answer']].rename(columns={'answer': 'evacuate_choice'})

    # Merge data on user_id (Inner join ensures we only have users who answered both)
    merged = pd.merge(player_types, evac_choices, on='user_id', how='inner')
    return merged

def generate_plots(df):
    if df is None or df.empty:
        return

    # --- Plot 1: Breakdown of Player Types ---
    plt.figure(figsize=(8, 6))
    counts = df['player_type'].value_counts()
    pcts = df['player_type'].value_counts(normalize=True) * 100
    
    ax1 = counts.plot(kind='bar', color='skyblue', edgecolor='black')
    plt.title('Breakdown of Player Types', fontsize=14)
    plt.ylabel('Count')
    plt.xticks(rotation=45)
    
    for i, (v, p) in enumerate(zip(counts, pcts)):
        ax1.text(i, v + 0.2, f'{v}\n({p:.1f}%)', ha='center', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('player_breakdown.png')
    plt.close()

    # --- Plot 2: Evacuation Choice (All Types Combined) ---
    plt.figure(figsize=(6, 6))
    ev_counts = df['evacuate_choice'].value_counts()
    ev_pcts = df['evacuate_choice'].value_counts(normalize=True) * 100
    
    ax2 = ev_counts.plot(kind='bar', color=['coral', 'lightgreen'], edgecolor='black')
    plt.title('Overall Evacuation Choices', fontsize=14)
    plt.ylabel('Count')
    plt.xticks(rotation=0)
    
    for i, (v, p) in enumerate(zip(ev_counts, ev_pcts)):
        ax2.text(i, v + 0.2, f'{v}\n({p:.1f}%)', ha='center', fontweight='bold')
        
    plt.tight_layout()
    plt.savefig('evacuation_overall.png')
    plt.close()

    # --- Plot 3: Evacuation Choice Broken Down by Player Type ---
    grouped = df.groupby(['player_type', 'evacuate_choice']).size().unstack(fill_value=0)
    row_totals = grouped.sum(axis=1)
    
    ax3 = grouped.plot(kind='bar', figsize=(12, 7), edgecolor='black')
    plt.title('Evacuation Choice by Player Type', fontsize=14)
    plt.ylabel('Count')
    plt.xlabel('Player Type')
    plt.xticks(rotation=45)
    plt.legend(title='Choice', bbox_to_anchor=(1.05, 1), loc='upper left')

    # Label counts and percentages on bars
    n_groups = len(grouped.index)
    for i, patch in enumerate(ax3.patches):
        height = patch.get_height()
        width = patch.get_width()
        x, y = patch.get_xy()
        
        # Calculate group and category indices
        group_idx = i % n_groups
        cat_idx = i // n_groups
        
        count = grouped.iloc[group_idx, cat_idx]
        total = row_totals.iloc[group_idx]
        pct = (count / total * 100) if total > 0 else 0
        
        if height > 0:
            ax3.text(x + width/2, y + height + 0.1, f'{int(count)}\n({pct:.1f}%)', 
                     ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.tight_layout()
    plt.savefig('evacuation_by_type.png')
    plt.close()

def create_html_report():
    html_content = """
    <html>
    <head>
        <title>Evacuation Analysis Summary</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; text-align: center; background-color: #f4f4f4; }
            .container { background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); display: inline-block; }
            h1 { color: #333; }
            img { margin: 20px; border: 1px solid #ddd; border-radius: 5px; max-width: 90%; }
            hr { border: 0; border-top: 1px solid #eee; margin: 40px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Hurricane Evacuation Survey Results</h1>
            <p>Analysis based on the most recent response for each user.</p>
            <hr>
            <h2>1. Player Type Distribution</h2>
            <img src="player_breakdown.png">
            <hr>
            <h2>2. Overall Evacuation Choice</h2>
            <img src="evacuation_overall.png">
            <hr>
            <h2>3. Evacuation Choice by Player Type</h2>
            <img src="evacuation_by_type.png">
        </div>
    </body>
    </html>
    """
    with open('plots_summary.html', 'w') as f:
        f.write(html_content)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Analyze evacuation survey data.')
    parser.add_argument('--today', action='store_true', help='Only show responses from today')
    args = parser.parse_args()

    data = process_data('NokiEvacuateOutput.csv', only_today=args.today)
    if data is not None:
        generate_plots(data)
        create_html_report()
        print("Success! Created: player_breakdown.png, evacuation_overall.png, evacuation_by_type.png, and plots_summary.html")
