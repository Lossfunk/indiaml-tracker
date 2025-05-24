import sys

def process_file(input_filename, output_filename):
    try:
        with open(input_filename, 'r') as file:
            lines = file.readlines()

        # Strip lines and remove the prefix
        processed_lines = (
            line.strip().replace("No mapping found for ", "")
            for line in lines
        )

        # Create a set to remove duplicates
        unique_lines = set(processed_lines)

        # Write the unique lines to a new file
        with open(output_filename, 'w') as file:
            for line in unique_lines:
                file.write(f"{line}\n")

        print(f"Processed file saved as: {output_filename}")

    except FileNotFoundError:
        print(f"File not found: {input_filename}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python src/main.py <filename>")
        sys.exit(1)

    input_filename = sys.argv[1]
    output_filename = f"proc_{input_filename}"
    process_file(input_filename, output_filename)