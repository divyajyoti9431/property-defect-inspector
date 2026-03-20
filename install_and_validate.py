"""Install deps and validate the docx file."""
import subprocess
import sys
import os

# Install required packages
print("Installing defusedxml and lxml...")
result = subprocess.run(
    [sys.executable, '-m', 'pip', 'install', 'defusedxml', 'lxml', '-q'],
    capture_output=True, text=True
)
print("pip stdout:", result.stdout)
if result.stderr:
    print("pip stderr:", result.stderr)

# Add the scripts/office directory to sys.path so validate.py can import validators
scripts_dir = r'C:\Users\divya\AppData\Roaming\Claude\local-agent-mode-sessions\skills-plugin\6a60dd0b-fd5e-4a5e-a902-2c989a35f621\ad4c30f4-97d6-491e-916a-d76c6c247c28\skills\docx\scripts\office'
sys.path.insert(0, scripts_dir)

docx_path = r'C:\Users\divya\OBJECT DETECTION\PTU_Predictive_Tracking_Plan.docx'

# Now run the validation
validate_script = os.path.join(scripts_dir, 'validate.py')
result2 = subprocess.run(
    [sys.executable, validate_script, docx_path],
    capture_output=True, text=True,
    cwd=scripts_dir
)
print("VALIDATION OUTPUT:")
print(result2.stdout)
if result2.stderr:
    print("VALIDATION STDERR:", result2.stderr)
print("Return code:", result2.returncode)
