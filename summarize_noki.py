import pandas as pd
import sys
import argparse

def process_data_from_stdin():
    """
    Reads CSV data from standard input into a pandas DataFrame.
    Handles potential errors during data reading, such as empty input.

    Returns:
        pd.DataFrame: The DataFrame containing the input CSV data.
    """
    try:
        df = pd.read_csv(sys.stdin)
        return df
    except pd.errors.EmptyDataError:
        sys.stderr.write("Error: No data to parse. The input CSV might be empty.\n")
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"An unexpected error occurred while reading input: {e}\n")
        sys.exit(1)

def get_unique_answers_for_question(df, question_text):
    """
    Filters the DataFrame for a specific question and returns a list of unique answers.
    Exits with an error if the 'question' or 'answer' columns are missing.

    Args:
        df (pd.DataFrame): The input DataFrame.
        question_text (str): The exact text of the question to filter by.

    Returns:
        list: A list of unique answers for the specified question.
    """
    if 'question' not in df.columns or 'answer' not in df.columns:
        sys.stderr.write("Error: 'question' or 'answer' column not found in the input data.\n")
        sys.exit(1)

    # Filter rows where the 'question' column matches the question_text
    filtered_df = df[df['question'] == question_text]

    # Get unique answers from the filtered DataFrame, drop any NaN (Not a Number) values,
    # and convert the result to a list for easy iteration and printing.
    unique_answers = filtered_df['answer'].dropna().unique().tolist()
    return unique_answers

def generate_full_summary(df):
    """
    Generates the full summary of answers: grouped by 'hashed_user_id', 'created_at',
    and 'question', with unique answers joined by a comma. The output is sorted
    by 'hashed_user_id' and then by 'created_at', and printed to standard output in CSV format.
    Exits with an error if required columns are missing.

    Args:
        df (pd.DataFrame): The input DataFrame.
    """
    try:
        # Define the columns that are required for this summary generation.
        required_cols = ['hashed_user_id', 'created_at', 'question', 'answer']
        # Check if all required columns are present in the DataFrame.
        if not all(col in df.columns for col in required_cols):
            # Identify missing columns for a helpful error message.
            missing = [col for col in required_cols if col not in df.columns]
            raise KeyError(f"Missing expected columns: {', '.join(missing)}")

        # Group the DataFrame by 'hashed_user_id', 'created_at', and 'question'.
        # For each group, apply a lambda function to join all unique 'answer' values
        # into a single comma-separated string.
        # .reset_index() converts the grouped result back into a DataFrame.
        summary_df = df.groupby(['hashed_user_id', 'created_at', 'question'])['answer'].apply(
            lambda x: ', '.join(x.unique())
        ).reset_index()

        # Order the output DataFrame first by 'hashed_user_id' and then by 'created_at'.
        summary_df = summary_df.sort_values(by=['hashed_user_id', 'created_at'])

        # Print the summarized DataFrame to standard output in CSV format.
        # index=False prevents pandas from writing the DataFrame index as a column in the output.
        summary_df.to_csv(sys.stdout, index=False)

    except KeyError as e:
        sys.stderr.write(f"Error: {e}. Please ensure relevant columns exist in your CSV input.\n")
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"An unexpected error occurred during full summary generation: {e}\n")
        sys.exit(1)

# This block ensures the script's main execution logic is run only when the
# script is executed directly (e.g., `python script.py`), and not when it's
# imported as a module into another Python script.
if __name__ == "__main__":
    # Create an ArgumentParser object to handle command-line arguments.
    parser = argparse.ArgumentParser(
        description="Summarize answers from CSV data, or extract specific answers based on a question."
    )
    # Add a command-line argument '--filter-question'.
    # This argument expects a string value, which will be the question to filter by.
    parser.add_argument(
        '--filter-question',
        type=str,
        help='Output unique answers for a specific question. '
             'The question text should be provided in quotes (e.g., --filter-question "What would the game be about?").'
    )

    # Parse the arguments provided by the user on the command line.
    args = parser.parse_args()

    # Read the entire CSV data from standard input into a DataFrame.
    data_frame = process_data_from_stdin()

    # Check if the --filter-question option was provided.
    if args.filter_question:
        question_to_filter = args.filter_question
        answers = get_unique_answers_for_question(data_frame, question_to_filter)
        # Print each unique answer on a new line.
        for answer in answers:
            print(answer)
    else:
        # If no specific filter option is provided, perform the default full summary generation.
        generate_full_summary(data_frame)

