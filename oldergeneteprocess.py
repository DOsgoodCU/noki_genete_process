import pandas as pd
import sys

def calculate_drought_answer_percentages():
    """
    Reads CSV data from standard input, filters for questions starting with "Now,",
    calculates the percentage of each answer option per unique hashed_user_id,
    and prints the results to standard output.
    """
    try:
        # Read the CSV file from standard input into a DataFrame
        df = pd.read_csv(sys.stdin)

        # Ensure necessary columns exist
        required_cols = ['hashed_user_id', 'question', 'answer']
        if not all(col in df.columns for col in required_cols):
            missing = [col for col in required_cols if col not in df.columns]
            sys.stderr.write(f"Error: Missing expected columns: {', '.join(missing)}. "
                             "Please ensure 'hashed_user_id', 'question', and 'answer' columns exist.\n")
            sys.exit(1)

        # Filter for questions that start with "Now,"
        # .str.startswith() is used for string matching. .dropna() handles potential NaN in 'question'.
        # The filter has been updated from "Now, for droughts" to "Now,"
        filtered_questions_df = df[df['question'].astype(str).str.startswith("Now,", na=False)].copy()

        if filtered_questions_df.empty:
            sys.stdout.write("No questions starting with 'Now,' found in the input.\n")
            return

        # Count occurrences of each answer for each hashed_user_id
        # Group by 'hashed_user_id' and 'answer', then count the size of each group.
        answer_counts = filtered_questions_df.groupby(['hashed_user_id', 'answer']).size().reset_index(name='count')

        # Calculate the total answers for each hashed_user_id
        # Group by 'hashed_user_id' and sum the 'count' to get total answers per user.
        total_answers_per_user = answer_counts.groupby('hashed_user_id')['count'].sum().reset_index(name='total_answers')

        # Merge counts with total answers to prepare for percentage calculation
        merged_df = pd.merge(answer_counts, total_answers_per_user, on='hashed_user_id')

        # Calculate the percentage for each answer
        # The percentage is (answer_count / total_answers_for_user) * 100.
        merged_df['percentage'] = (merged_df['count'] / merged_df['total_answers']) * 100

        # Select and reorder columns for the final output
        final_output_df = merged_df[['hashed_user_id', 'answer', 'percentage']].copy()

        # Sort the output for better readability (by hashed_user_id, then by percentage descending)
        final_output_df = final_output_df.sort_values(by=['hashed_user_id', 'percentage'], ascending=[True, False])

        # Print the results to standard output in CSV format
        # index=False prevents pandas from writing the DataFrame index as a column.
        final_output_df.to_csv(sys.stdout, index=False)

    except pd.errors.EmptyDataError:
        sys.stderr.write("Error: No data to parse. The input CSV might be empty.\n")
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"An unexpected error occurred: {e}\n")
        sys.exit(1)

# This block ensures the function is called when the script is executed.
if __name__ == "__main__":
    calculate_drought_answer_percentages()

