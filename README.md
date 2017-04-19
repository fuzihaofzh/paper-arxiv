# Paper Arxiv: A Command Line Based Academic Paper Management Tool.

      _____                                           _       
     |  __ \                          /\             (_)      
     | |__) |_ _ _ __   ___ _ __     /  \   _ ____  _____   __
     |  ___/ _` | '_ \ / _ \ '__|   / /\ \ | '__\ \/ / \ \ / /
     | |  | (_| | |_) |  __/ |     / ____ \| |   >  <| |\ V / 
     |_|   \__,_| .__/ \___|_|    /_/    \_\_|  /_/\_\_| \_/  
                | |                                           
                |_|                                           

## Introduction
Paper Arxiv is a command line based academic paper management tool. It provides an efficient access to your pdf files, comments, tags and so on.

## Highlights
- **Automatic Information Extraction**: It can extract information from pdf files, websites and generate default meta information.
- **Multi File Source**: You can add local files, URL links, websites.
- **Portable**: all information is stored in one folder and you can put in your cloud disk.
- **Search Everything**: You can use its powerful find tool to find whatever you want.


## Install
```bash
brew install pdftohtml # for mac
sudo apt-get install pdftohtml # for Ubuntu
pip install pa
pa config --libpath /Path/To/Store/Library
```

## Usage
Here is a small example showing how to manage your file. For more details please refer to `pa --help`
```bash
cd your_floder_storing_pdf_files
pa add slide.pdf
pa add https://arxiv.org/pdf/1701.02720.pdf
pa find VAE
pa -h
```
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-fork-ribbon-css/0.2.0/gh-fork-ribbon.min.css" />
<!--[if lt IE 9]>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-fork-ribbon-css/0.2.0/gh-fork-ribbon.ie.min.css" />
<![endif]-->
<a class="github-fork-ribbon" href="https://github.com/maplewizard/paper-arxiv" title="Fork me on GitHub">Fork me on GitHub</a>
