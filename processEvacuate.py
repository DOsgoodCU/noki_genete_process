import pandas as pd
import matplotlib.pyplot as plt
import argparse
import datetime
import os

# Define consistent order and colors for evacuation choices
# 'Yep, evacuate!' will always be on the left/first.
EVAC_ORDER = ['Yep, evacuate!', 'Heck no! dont evacuate']
COLOR_MAP = {'Yep, evacuate!': 'lightgreen', 'Heck no! dont evacuate': 'coral'}

def process_data(csv_file, only_today=False, start_time=None, end_time=None):
    """Loads and filters data based on time constraints."""
    df = pd.read_csv(csv_file)
    df['created_at'] = pd.to_datetime(df['created_at'], utc=True)
    
    if only_today:
        today = datetime.datetime.now(datetime.timezone.utc).date()
        df = df[df['created_at'].dt.date == today]
    
    if start_time:
        start_ts = pd.to_datetime(start_time, utc=True)
        df = df[df['created_at'] >= start_ts]
        
    if end_time:
        end_ts = pd.to_datetime(end_time, utc=True)
        df = df[df['created_at'] <= end_ts]

    if df.empty:
        print("Warning: No data found for the specified timeframe.")
        return None

    # Standardize player types
    df['answer'] = df['answer'].replace({'Petowner': 'Pet Owner'})

    # Get most recent player type per user
    player_types = df[df['step_name'].isin(['player_select', 'playerselect'])].sort_values('created_at')
    player_types = player_types.drop_duplicates('user_id', keep='last')[['user_id', 'answer']].rename(columns={'answer': 'player_type'})

    # Get most recent evacuation choice per user
    evac_choices = df[df['step_name'] == 'evacuate_select'].sort_values('created_at')
    evac_choices = evac_choices.drop_duplicates('user_id', keep='last')[['user_id', 'answer']].rename(columns={'answer': 'evacuate_choice'})

    # Merge
    merged = pd.merge(player_types, evac_choices, on='user_id', how='inner')
    return merged

def generate_plots(df):
    """Creates the three requested figures with labels and consistent styling."""
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
        ax1.text(i, v + 0.1, f'{v}\n({p:.1f}%)', ha='center', fontweight='bold')
    plt.tight_layout()
    plt.savefig('player_breakdown.png')
    plt.close()

    # --- Plot 2: Overall Evacuation Choices ---
    plt.figure(figsize=(6, 6))
    # Reindex to ensure 'Yep, evacuate!' is on the left
    ev_counts = df['evacuate_choice'].value_counts().reindex(EVAC_ORDER, fill_value=0)
    ev_pcts = (ev_counts / ev_counts.sum()) * 100
    
    # Map colors based on the fixed order
    colors = [COLOR_MAP[choice] for choice in EVAC_ORDER]
    
    ax2 = ev_counts.plot(kind='bar', color=colors, edgecolor='black')
    plt.title('Overall Evacuation Choices', fontsize=14)
    plt.ylabel('Count')
    plt.xticks(rotation=0)
    for i, v in enumerate(ev_counts):
        p = ev_pcts.iloc[i]
        ax2.text(i, v + 0.1, f'{v}\n({p:.1f}%)', ha='center', fontweight='bold')
    plt.tight_layout()
    plt.savefig('evacuation_overall.png')
    plt.close()

    # --- Plot 3: Evacuation Choice Broken Down by Player Type ---
    # Group and pivot
    grouped = df.groupby(['player_type', 'evacuate_choice']).size().unstack(fill_value=0)
    # Reindex columns to ensure consistent order (Evacuate on Left)
    grouped = grouped.reindex(columns=EVAC_ORDER, fill_value=0)
    
    row_totals = grouped.sum(axis=1)
    colors = [COLOR_MAP[choice] for choice in EVAC_ORDER]
    
    ax3 = grouped.plot(kind='bar', figsize=(12, 7), color=colors, edgecolor='black')
    plt.title('Evacuation Choice by Player Type', fontsize=14)
    plt.ylabel('Count')
    plt.xlabel('Player Type')
    plt.xticks(rotation=45)
    plt.legend(title='Choice', bbox_to_anchor=(1.05, 1), loc='upper left')

    n_groups = len(grouped.index)
    for i, patch in enumerate(ax3.patches):
        height = patch.get_height()
        width = patch.get_width()
        x, y = patch.get_xy()
        # Matplotlib plots groups together
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

def create_html_report(start=None, end=None, only_today=False):
    """Generates the combined HTML summary."""
    time_info = ""
    if only_today: time_info = " (Today)"
    elif start or end: time_info = f" (Range: {start or 'Min'} to {end or 'Max'})"

    html_content = f"""
    <html>
    <head><title>Analysis Summary</title>
    <style>body{{font-family:Arial; text-align:center; padding:20px;}} .box{{border:1px solid #ccc; padding:20px; border-radius:10px;}} img{{max-width:90%; margin:20px;}}</style>
    </head>
    <body>
        <div class="box">
            <h1>Hurricane Evacuation Report{time_info}</h1>
            <hr><h2>1. Player Distribution</h2><img src="player_breakdown.png">
            <hr><h2>2. Overall Evacuation</h2><img src="evacuation_overall.png">
            <hr><h2>3. Detailed Breakdown</h2><img src="evacuation_by_type.png">
        </div>
    </body>
    </html>"""
    with open('evacuation_results.html', 'w') as f:
        f.write(html_content)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Analyze evacuation data.')
    parser.add_argument('--today', action='store_true', help='Filter for today only')
    parser.add_argument('--start', type=str, help='Start time (e.g., "2026-01-01")')
    parser.add_argument('--end', type=str, help='End time (e.g., "2026-01-09 23:59:59")')
    args = parser.parse_args()

    data = process_data('NokiEvacuateOutput.csv', only_today=args.today, start_time=args.start, end_time=args.end)
    if data is not None:
        generate_plots(data)
        create_html_report(args.start, args.end, args.today)
        
        # Summary message with instructions
        print("\n" + "="*50)
        print("SUCCESS: Analysis Complete")
        print("="*50)
        print("Output files generated:")
        print("  - player_breakdown.png")
        print("  - evacuation_overall.png")
        print("  - evacuation_by_type.png")
        print("  - evacuation_results.html")
        print("\nTo filter by date/time, use the following options:")
        print("  --today            : Only include responses from today.")
        print("  --start \"YYYY-MM-DD\": Include responses from this date onwards.")
        print("  --end \"YYYY-MM-DD\"  : Include responses up until this date.")
        print("Note: Date strings also accept times (e.g., \"2026-01-01 12:00:00\").")
        print("="*50)
