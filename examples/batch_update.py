"""This script can do a batch update of notebook examples.
"""


import glob
import os
import shutil

in_dir = os.path.dirname(os.path.abspath(__file__))
print(in_dir)
notebook_dir = os.path.abspath(os.path.join(in_dir, 'notebooks'))
workshop_dir = os.path.abspath(os.path.join(in_dir, 'workshops'))

os.chdir(notebook_dir)
cmd = "jupytext --to myst *.ipynb"
os.system(cmd)

os.chdir(workshop_dir)
cmd = "jupytext --to myst *.ipynb"
os.system(cmd)

os.chdir(in_dir)


notebooks = glob.glob(in_dir + '/notebooks/*.md')
workshops = glob.glob(in_dir + '/workshops/*.md')

files = notebooks + workshops

for file in files:
    with open(file, 'r') as f:
        lines = f.readlines()

    has_colab = False
    for line in lines:
        if 'colab-badge.svg' in line:
            has_colab = True
            break
    if not has_colab:
        print(f'No Colab badge found in {file}')

    out_lines = []
    for index, line in enumerate(lines):
        if 'colab-badge.svg' in line and 'jupyterlite' not in lines[index - 1]:
            badge = (
                '[![image](https://jupyterlite.rtfd.io/en/latest/_static/badge.svg)]'
            )
            baseurl = 'https://demo.leafmap.org/lab/index.html?path='
            base_dir = os.path.basename(os.path.dirname(file))
            basename = os.path.basename(file).replace('.md', '.ipynb')
            url = baseurl + base_dir + '/' + basename
            badge_url = f"{badge}({url})\n"
            out_lines.append(badge_url)
            out_lines.append(line)

        elif 'jupyterlite.rtfd' in line and "Open In Studio Lab" not in lines[index + 1]:
            # Add Studio Lab badge
            badge = (
                '[![Open In Studio Lab](https://studiolab.sagemaker.aws/studiolab.svg)]'
            )
            baseurl = 'https://studiolab.sagemaker.aws/import/github/giswqs/leafmap/blob/master/examples/'
            base_dir = os.path.basename(os.path.dirname(file))
            basename = os.path.basename(file).replace('.md', '.ipynb')
            url = baseurl + base_dir + '/' + basename
            badge_url = f"{badge}({url})\n"
            out_lines.append(line)

            out_lines.append(badge_url)

            # Add Planetary Computer badge
            badge = (
                '[![Open in Planetary Computer](https://img.shields.io/badge/Open-Planetary%20Computer-black?style=flat&logo=microsoft)]'
            )
            baseurl = 'https://studiolab.sagemaker.aws/import/github/giswqs/leafmap/blob/master/examples/'
            base_dir = os.path.basename(os.path.dirname(file))
            basename = os.path.basename(file).replace('.md', '.ipynb')

            url = f'https://pccompute.westeurope.cloudapp.azure.com/compute/hub/user-redirect/git-pull?repo=https://github.com/giswqs/leafmap&urlpath=lab/tree/leafmap/examples/{base_dir}/{basename}&branch=master'
            badge_url = f"{badge}({url})\n"
            out_lines.append(badge_url)

        elif ':id:' in line:
            print(file)
            print(line)
            pass
        else:
            out_lines.append(line)

    with open(file, 'w') as f:
        f.writelines(out_lines)


os.chdir(notebook_dir)
cmd = "jupytext --to ipynb *.md"
os.system(cmd)

os.chdir(workshop_dir)
cmd = "jupytext --to ipynb *.md"
os.system(cmd)

os.chdir(in_dir)

for file in files:
    os.remove(file)

files = [file.replace('.md', '.ipynb') for file in files]

for file in files:
    with open(file, 'r') as f:
        lines = f.readlines()

    out_lines = []
    for index, line in enumerate(lines):
        if '"id":' in line:
            pass
        elif "display_name" in line:
            out_lines.append('   "display_name": "Python 3",\n')
        else:
            out_lines.append(line)

    with open(file, 'w') as f:
        f.writelines(out_lines)


shutil.copytree(
    notebook_dir, notebook_dir.replace('examples', 'docs'), dirs_exist_ok=True
)
shutil.copytree(
    workshop_dir, workshop_dir.replace('examples', 'docs'), dirs_exist_ok=True
)
