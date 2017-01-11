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
Paper Arxiv is a command line base academic paper management tool. It provide an efficient access to your pdf files, comments, tags and so on.

## Highlights
- **Automatic Infortation Extraction**: It can extract information from pdf files, websites and generate default meta information.
- **Multi File Source**: You can add local files, URL links, websites.
- **Protable**: all information are sotred in one floder and you can put in your cloud disk.
- **Search Everything**: You can use its powerful find tool to find whatever you want.


## Install
```
brew install pdftohtml
pip install pa
```

## Nutshell
Here is a small example showing how to manage your file. For more details plseas refer to `pa --help`
```
cd your_floder_storing_pdf_files
pa init
pa add .
pa add https://arxiv.org/pdf/1701.02720.pdf
pa find -a Bengio
pa --help
```
