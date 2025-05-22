from difflib import unified_diff
from pathlib import Path

def compare_files(correct_output_filename: str):
    diff_dir: Path = Path("diffs")
    diff_dir.mkdir(parents=True, exist_ok=True)
    student_output_filename: str = f"test_{correct_output_filename}"
    with open(f"correct_output/{correct_output_filename}.txt", "r") as correct_output:
        with open(f"output/{student_output_filename}.txt", "r") as student_output:
            diff = unified_diff(
                correct_output.readlines(),
                student_output.readlines(),
                fromfile = f"{correct_output_filename}.txt",
                tofile = f"{student_output_filename}.txt",
            )
            with open(f"diffs/diff_{correct_output_filename}.txt", "w") as diff_output:
                for line in diff:
                    diff_output.write(line)