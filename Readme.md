

# Genete Noki Analysis

**Note that this was adapted from noki_evacuate_process** so there may be accidental remnants of that, which already included some Geneti scripts.

## command line for class
```
python downloadGenete.py
python processGenete.py --today
./deploy_analysis.sh
```

```python downloadGenete.py``` Run this first.Hardcoded to download the instance that has the start word Genete, saves to  NokiGeneteOutput.csv

```python processGenete.py```Takes NokiGeneteOutput.csv and creates genete_results.html

  - reports raw preference between 2002 and 1984
  - reports how many people were right that 2009 was a bad year and 2010 was not
  - filters answers for only people that got 2009 right and makes an updated plot

Available Options:
  --start-date YYYY-MM-DD   (Example: --start-date 2025-01-01)
  --end-date YYYY-MM-DD     (Example: --end-date 2025-12-31)
  --today                   (Example: --today)
  --all-responses           (Example: --all-responses) (instead of only most recent response)
  Defaults: all time, only most recent response

  **for  class, run:** 
  
  ```python processGenete.py --today```
  
  **for demo use**
  
  ```python processGenete.py --all-responses``` because not enough responses for meaningful analysis (yet)

## ./deploy_analysis.sh
Put analysis results, the complete file genete_results.html in the insurepeopleinteractive repo and push to github, once updated


