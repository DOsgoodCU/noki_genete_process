

# Hurricane Evacuation Analysis

Tools to process survey data from NokiEvacuateOutput.csv, generate visualizations, and deploy reports.

## Local Analysis

Generate plots and the HTML report locally:

python evacuation_analysis.py

### Filtering Arguments

Flag: --today
Description: Process only today's responses.

Flag: --start "YYYY-MM-DD"
Description: Filter from a specific start date/time.

Flag: --end "YYYY-MM-DD"
Description: Filter up to a specific end date/time.

## Deployment

To copy results to ~/Evacuate/docs and deploy via MkDocs:

./deploy_analysis.sh

## Outputs

* player_breakdown.png: Distribution of player types.
* evacuation_overall.png: Total evacuation vs. stay counts.
* evacuation_by_type.png: Choice breakdown per player type.
* evacuation_results.html: Combined summary report.
# noki_evacuate_process
