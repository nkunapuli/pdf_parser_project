# pdf_parser_project
Scripts for downloading and formatting papers from arXiv and PLOS to train Nougat models

Nougat includes code for training models if you can create your own dataset. Datasets must consist of two folders, one containing PDF files and another containing HTML files with corresponding filenames.

## arXiv scraper

`arxiv_downloader.py` (within the `arxiv` folder) attempts to download some number of the most recently uploaded papers to arXiv. It downloads both the PDF and the source as a `.tar.gz`. The script unzips the source and runs `latexml` on the source to generate HTML files. It then deletes all of the unnecessary folders and log files, leaving you with one folder `pdf` and one folder `html`. Not all `.tex` files can be successfully converted to HTML, so you will end up with fewer PDFs and HTMLs than you initially requested (you usually get around 75-80% successful conversion). With more time, I would modify the script to continue downloading more papers until you hit the user's requested number. `latexml` is very slow, so to speed up the script I used multiprocessing.

To run this script, specify the number of papers you wish to download:

```
python arxiv_downloader.py 100
```

## PLOS scraper

`plos_scraper.py` is in the `plos` folder. As before, specify the number of papers you wish to download:
```
python plos_downloader.py 100
```
