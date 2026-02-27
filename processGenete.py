import pandas as pd
import matplotlib.pyplot as plt
import argparse
import sys
import os
from datetime import datetime, time
import pytz

# --- Configuration & Styling ---
INPUT_FILE = 'NokiGeneteOutput.csv'
OUTPUT_HTML = 'genete_results.html'
LOCAL_TZ = pytz.timezone('America/New_York')
COLOR_PRIMARY = '#007bff'
COLOR_SECONDARY = '#6c757d'
COLOR_SUCCESS = '#28a745'
COLOR_DANGER = '#dc3545'

def get_local_now():
    """Returns current time in America/New_York."""
    return datetime.now(pytz.utc).astimezone(LOCAL_TZ)

def get_local_timestamp_str():
    """Formatted timestamp for headers/footers."""
    return get_local_now().strftime("%Y-%m-%d %H:%M %Z")

def generate_bar_chart(df_counts, output_path, title, filter_label, colors=COLOR_PRIMARY):
    """Generates bar chart with the required timestamp footer."""
    if df_counts.empty:
        return False
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(df_counts['answer'].astype(str), df_counts['count'], color=colors)
    ax.set_ylabel('Number of Responses')
    ax.set_title(title)
    ax.bar_label(bars, padding=3)
    
    timestamp_str = f"Updated: {get_local_timestamp_str()}\nFilter: {filter_label}"
    plt.figtext(0.99, 0.01, timestamp_str, ha='right', va='bottom', fontsize=8, color='gray')
    
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    return True

def create_html_table(df_counts):
    """Generates summary tables with percentages."""
    if df_counts.empty:
        return "<p style='color: #666;'>No data available for this range.</p>"
    
    table_html = """
    <table style="width:100%; border-collapse: collapse; margin-top: 20px; text-align: left; font-size: 0.9em;">
        <thead>
            <tr style="background-color: #f8f9fa; border-bottom: 2px solid #dee2e6;">
                <th style="padding: 12px; border: 1px solid #dee2e6;">Answer Option</th>
                <th style="padding: 12px; border: 1px solid #dee2e6;">Total Count</th>
                <th style="padding: 12px; border: 1px solid #dee2e6;">Percentage</th>
            </tr>
        </thead>
        <tbody>
    """
    for _, row in df_counts.iterrows():
        table_html += f"""
            <tr>
                <td style="padding: 12px; border: 1px solid #dee2e6;">{row['answer']}</td>
                <td style="padding: 12px; border: 1px solid #dee2e6;">{int(row['count'])}</td>
                <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">{row['percentage']:.1f}%</td>
            </tr>
        """
    table_html += "</tbody></table>"
    return table_html

def process_stats(data):
    """Standardized counting and percentage calculation."""
    if data.empty: return pd.DataFrame(columns=['answer', 'count', 'percentage'])
    counts = data.value_counts().reset_index()
    counts.columns = ['answer', 'count']
    total = counts['count'].sum()
    counts['percentage'] = (counts['count'] / total * 100)
    return counts

def main():
    # 1. CLI Arguments
    parser = argparse.ArgumentParser(description="Genete Survey Analysis Dashboard")
    parser.add_argument('--start-date', type=str, help='Filter: Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='Filter: End date (YYYY-MM-DD)')
    parser.add_argument('--today', action='store_true', help='Filter: Process today only')
    parser.add_argument('--all-responses', action='store_true', help='Toggle: Include all responses (Default is most recent only)')
    args = parser.parse_args()

    # 2. Filtering Options Output with Examples (stdout)
    sys.stdout.write("--- Analysis Configuration & Command Line Examples ---\n")
    sys.stdout.write("Available Options:\n")
    sys.stdout.write("  --start-date YYYY-MM-DD   (Example: --start-date 2025-01-01)\n")
    sys.stdout.write("  --end-date YYYY-MM-DD     (Example: --end-date 2025-12-31)\n")
    sys.stdout.write("  --today                   (Example: --today)\n")
    sys.stdout.write("  --all-responses           (Example: --all-responses)\n\n")
    
    sys.stdout.write("Current Execution Settings:\n")
    sys.stdout.write(f"  Input File:     {INPUT_FILE}\n")
    sys.stdout.write(f"  Start Date:     {args.start_date if args.start_date else 'Any'}\n")
    sys.stdout.write(f"  End Date:       {args.end_date if args.end_date else 'Any'}\n")
    sys.stdout.write(f"  Today Only:     {args.today}\n")
    sys.stdout.write(f"  User Filtering: {'Most Recent Only (Deduplicated)' if not args.all_responses else 'Include All Responses'}\n\n")

    # 3. Load Data
    if not os.path.exists(INPUT_FILE):
        sys.stderr.write(f"Error: {INPUT_FILE} not found. Ensure the file is in the current directory.\n")
        sys.exit(1)

    df = pd.read_csv(INPUT_FILE)
    df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce', utc=True)
    df = df.dropna(subset=['created_at', 'hashed_user_id'])
    
    # 4. Apply Time Filtering (Local Time)
    df['local_time'] = df['created_at'].dt.tz_convert(LOCAL_TZ)
    now_local = get_local_now()
    
    start_dt, end_dt = None, None
    if args.today:
        start_dt = LOCAL_TZ.localize(datetime.combine(now_local.date(), time.min))
        end_dt = LOCAL_TZ.localize(datetime.combine(now_local.date(), time.max))
    else:
        if args.start_date:
            start_dt = LOCAL_TZ.localize(datetime.strptime(args.start_date, '%Y-%m-%d'))
        if args.end_date:
            end_dt = LOCAL_TZ.localize(datetime.combine(datetime.strptime(args.end_date, '%Y-%m-%d'), time.max))

    if start_dt: df = df[df['local_time'] >= start_dt]
    if end_dt: df = df[df['local_time'] <= end_dt]

    # 5. Deduplication (Applied by default unless --all-responses is passed)
    if not args.all_responses:
        df = df.sort_values(by='created_at', ascending=True)
        # Keeps only the last (most recent) response per user for each specific question
        df = df.drop_duplicates(subset=['hashed_user_id', 'question'], keep='last')

    filter_label = f"Range: {start_dt.date() if start_dt else 'Start'} to {end_dt.date() if end_dt else 'End'}"
    if not args.all_responses: filter_label += " (Latest Only)"

    # 6. Analysis Logic
    # Analysis 1: 2002 vs 1984
    now_q = df[df['question'].astype(str).str.contains("Now,", na=False)]
    f1_stats = process_stats(now_q[now_q['answer'].isin(["2002", "1984"])]['answer'])

    # Analysis 2: Accuracy (2009)
    first_q = df[df['question'].astype(str).str.contains("First question", na=False)].copy()
    first_q['is_correct'] = first_q['answer'].apply(lambda x: 'Correct (2009)' if str(x) == "2009" else 'Incorrect')
    f2_stats = process_stats(first_q['is_correct'])

    # Analysis 3: Cross-filtered (2002 vs 1984 only for correct users)
    correct_users = first_q[first_q['answer'] == "2009"]['hashed_user_id'].unique()
    adj_now = now_q[now_q['hashed_user_id'].isin(correct_users)]
    f3_stats = process_stats(adj_now[adj_now['answer'].isin(["2002", "1984"])]['answer'])

    # 7. Generate Output
    analyses = [
        {"df": f1_stats, "file": "fig1.png", "title": "Overall Choice: 2002 vs 1984", "colors": COLOR_PRIMARY},
        {"df": f2_stats, "file": "fig2.png", "title": "Knowledge Check: Correct (2009) vs Incorrect", "colors": [COLOR_SUCCESS, COLOR_DANGER]},
        {"df": f3_stats, "file": "fig3.png", "title": "Adjusted Choice: 2002 vs 1984 (Correct Respondents Only)", "colors": COLOR_SECONDARY}
    ]

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Genete Survey Results</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, sans-serif; margin: 0; padding: 40px; background-color: #f0f2f5; color: #1c1e21; }}
            .container {{ max-width: 900px; margin: auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
            h1 {{ border-bottom: 2px solid #007bff; padding-bottom: 15px; color: #007bff; }}
            .meta {{ font-size: 0.85em; color: #606770; background: #f8f9fa; padding: 15px; border-radius: 4px; border-left: 5px solid #007bff; margin-bottom: 30px; }}
            .section {{ margin-bottom: 60px; padding-top: 20px; border-top: 1px solid #eee; }}
            h2 {{ color: #4b4f56; margin-bottom: 15px; font-size: 1.3em; }}
            img {{ max-width: 100%; height: auto; display: block; margin: 25px auto; border: 1px solid #e9ebee; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Genete Survey Dashboard</h1>
            <div class="meta">
                <strong>Local Time:</strong> {get_local_timestamp_str()}<br>
                <strong>Date Filter:</strong> {filter_label}<br>
                <strong>Unique Users Counted:</strong> {df['hashed_user_id'].nunique()}
            </div>
    """

    for item in analyses:
        html_content += f"<div class='section'><h2>{item['title']}</h2>"
        if not item['df'].empty:
            generate_bar_chart(item['df'], item['file'], item['title'], filter_label, item['colors'])
            html_content += f"<img src='{item['file']}' alt='{item['title']}'>{create_html_table(item['df'])}"
        else:
            html_content += "<p style='color: #888; font-style: italic;'>Inadequate data for this calculation in the selected date range.</p>"
        html_content += "</div>"

    html_content += "</div></body></html>"

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)

    sys.stdout.write(f"Success. Dashboard generated: {OUTPUT_HTML}\n")

if __name__ == "__main__":
    main()
