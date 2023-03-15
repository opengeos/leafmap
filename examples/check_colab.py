import glob
import os
import shutil

in_dir = os.path.dirname(os.path.abspath(__file__))
print(in_dir)
notebook_dir = os.path.abspath(os.path.join(in_dir, "notebooks"))
workshop_dir = os.path.abspath(os.path.join(in_dir, "workshops"))

os.chdir(notebook_dir)
cmd = "jupytext --to myst *.ipynb"
os.system(cmd)

os.chdir(workshop_dir)
cmd = "jupytext --to myst *.ipynb"
os.system(cmd)

os.chdir(in_dir)


notebooks = glob.glob(in_dir + "/notebooks/*.md")
workshops = glob.glob(in_dir + "/workshops/*.md")

files = notebooks + workshops

for file in files:
    with open(file, "r") as f:
        lines = f.readlines()

    has_colab = False
    for line in lines:
        if "colab-badge.svg" in line:
            has_colab = True
            break
    if not has_colab:
        print(f"No Colab badge found in {file}")
