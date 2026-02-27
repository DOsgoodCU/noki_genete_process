import pandas as pd
import sys
import argparse

def calculate_aggregated_answer_percentages(df_input, question_prefix):
    """
    Calculates the overall percentage of each answer option for questions starting with a given prefix,
    aggregated across all hashed_user_ids in the input DataFrame.

    Args:
        df_input (pd.DataFrame): The DataFrame to process.
        question_prefix (str): The prefix of the questions to filter by.

    Returns:
        pd.DataFrame: A DataFrame containing 'answer' and 'percentage'.
                      Returns an empty DataFrame if no matching questions are found.
    """
    # Filter for questions that start with the specified prefix
    filtered_questions_df = df_input[df_input['question'].astype(str).str.startswith(question_prefix, na=False)].copy()

    if filtered_questions_df.empty:
        return pd.DataFrame(columns=['answer', 'percentage'])

    # Count occurrences of each answer globally (not broken down by hashed_user_id)
    answer_counts = filtered_questions_df['answer'].value_counts().reset_index()
    answer_counts.columns = ['answer', 'count'] # Rename columns for clarity

    total_answers = answer_counts['count'].sum()

    if total_answers == 0:
        return pd.DataFrame(columns=['answer', 'percentage'])

    # Calculate percentage
    answer_counts['percentage'] = (answer_counts['count'] / total_answers) * 100

    # Select and reorder columns for the final output, sort by percentage descending
    final_output_df = answer_counts[['answer', 'percentage']].sort_values(by='percentage', ascending=False)

    return final_output_df

def process_and_output_percentages(start_date=None):
    """
    Reads CSV data from standard input, calculates and outputs three sets of percentages:
    1. Overall percentages for questions starting with "Now," for all data (optionally filtered by start_date).
    2. Overall percentage of answers that are "2009" for questions starting with "First" (optionally filtered by start_date).
    3. Overall percentages for questions starting with "Now," but only for sessions where
       the answer to a question starting with "First" was "2009" (optionally filtered by start_date).

    Args:
        start_date (str, optional): A date string (e.g., 'YYYY-MM-DD'). If provided,
                                     only data from this date onwards will be considered.
                                     Defaults to None.
    """
    try:
        # Read the CSV file from standard input into a DataFrame
        df = pd.read_csv(sys.stdin)

        # Ensure necessary columns exist for all calculations
        required_cols = ['hashed_user_id', 'question', 'answer', 'session_id', 'created_at']
        if not all(col in df.columns for col in required_cols):
            missing = [col for col in required_cols if col not in df.columns]
            sys.stderr.write(f"Error: Missing expected columns: {', '.join(missing)}. "
                             "Please ensure 'hashed_user_id', 'question', 'answer', 'session_id', and 'created_at' columns exist.\n")
            sys.exit(1)

        # Convert 'created_at' to datetime objects for proper comparison
        # Use errors='coerce' to turn unparseable dates into NaT (Not a Time)
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
        # Drop rows where 'created_at' could not be parsed
        df.dropna(subset=['created_at'], inplace=True)

        # Apply date filtering if start_date is provided
        if start_date:
            try:
                # Convert the start_date string to a datetime object for comparison
                start_datetime = pd.to_datetime(start_date)
                # Filter the DataFrame to include only records on or after the start_date
                df = df[df['created_at'] >= start_datetime].copy()
                if df.empty:
                    sys.stdout.write(f"No data found on or after {start_date} after filtering.\n")
                    return
            except ValueError:
                sys.stderr.write(f"Error: Invalid start date format: '{start_date}'. Please use YYYY-MM-DD format.\n")
                sys.exit(1)


        # --- First Output: Overall Percentages for questions starting with "Now," (All Data) ---
        sys.stdout.write("--- Overall Percentage of Answers for Questions Starting with 'Now,' (All Data) ---\n")
        all_data_percentages = calculate_aggregated_answer_percentages(df, "Now,")
        if not all_data_percentages.empty:
            all_data_percentages.to_csv(sys.stdout, index=False)
        else:
            sys.stdout.write("No questions starting with 'Now,' found in the full dataset (after date filter if applied).\n")
        sys.stdout.write("\n") # Add a newline for separation


        # --- Second Output: Overall Percentage of "2009" Answers for Questions Starting with "First" ---
        sys.stdout.write("--- Overall Percentage of '2009' Answers for Questions Starting with 'First' ---\n")
        first_questions_overall_df = df[df['question'].astype(str).str.startswith("First", na=False)].copy()

        if first_questions_overall_df.empty:
            sys.stdout.write("No questions starting with 'First' found in the dataset (after date filter if applied).\n")
        else:
            total_first_questions_answered = len(first_questions_overall_df)
            answers_2009_count = (first_questions_overall_df['answer'] == "2009").sum()

            if total_first_questions_answered > 0:
                percentage_2009 = (answers_2009_count / total_first_questions_answered) * 100
                sys.stdout.write(f"Overall percentage of '2009' answers for 'First' questions: {percentage_2009:.2f}%\n")
            else:
                sys.stdout.write("No answers found for questions starting with 'First'.\n")
        sys.stdout.write("\n")


        # --- Third Output: Overall Percentages for questions starting with "Now," (Filtered by "First" = "2009") ---
        sys.stdout.write("--- Overall Percentage of Answers for Questions Starting with 'Now,' (Filtered by 'First' = '2009') ---\n")

        # Step 1: Find session_ids where the answer to a question starting with "First" was "2009"
        first_questions_df = df[df['question'].astype(str).str.startswith("First", na=False)].copy()
        sessions_with_2009_answer = first_questions_df[first_questions_df['answer'] == "2009"]['session_id'].unique()

        if len(sessions_with_2009_answer) == 0:
            sys.stdout.write("No sessions found where answer to a 'First' question was '2009'.\n")
            sys.stdout.write("Therefore, no filtered percentages for 'Now,' questions can be calculated.\n")
        else:
            # Step 2: Filter the original DataFrame to include only these session_ids
            filtered_df = df[df['session_id'].isin(sessions_with_2009_answer)].copy()

            # Step 3: Calculate overall percentages on this filtered DataFrame
            filtered_data_percentages = calculate_aggregated_answer_percentages(filtered_df, "Now,")

            if not filtered_data_percentages.empty:
                filtered_data_percentages.to_csv(sys.stdout, index=False)
            else:
                sys.stdout.write("No questions starting with 'Now,' found in the filtered dataset (after date filter if applied).\n")
        sys.stdout.write("\n") # Add a newline for separation


    except pd.errors.EmptyDataError:
        sys.stderr.write("Error: No data to parse. The input CSV might be empty.\n")
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"An unexpected error occurred: {e}\n")
        sys.exit(1)

# This block ensures the main function is called when the script is executed.
if __name__ == "__main__":
    # Create an ArgumentParser object to handle command-line arguments.
    parser = argparse.ArgumentParser(
        description="Calculate percentage of answers for specific questions, "
                    "optionally filtered by a start date."
    )
    # Add a command-line argument '--start-date'.
    # This argument expects a string value, which will be the start date for filtering.
    parser.add_argument(
        '--start-date',
        type=str,
        help='Optional: Start date (YYYY-MM-DD) to include data from. '
             'Only data on or after this date will be processed.'
    )

    # Parse the arguments provided by the user on the command line.
    args = parser.parse_args()

    # Call the main processing function with the provided start_date argument.
    process_and_output_percentages(start_date=args.start_date)

