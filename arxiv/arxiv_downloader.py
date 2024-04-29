import aiohttp
import asyncio
import os
import shutil
from multiprocessing import Pool
import tarfile
import subprocess
import arxiv
import requests
import argparse

async def download_paper(session, paper):
    source_url = f"https://arxiv.org/e-print/{paper.get_short_id()}"
    async with session.get(source_url) as response:
        if response.status == 200:
            source_path = os.path.join('source', f"{paper.get_short_id()}.tar.gz")
            with open(source_path, 'wb') as f:
                while True:
                    chunk = await response.content.read(1024)
                    if not chunk:
                        break
                    f.write(chunk)
            return paper, source_path
        else:
            print(f"Failed to download source for {paper.title}. Skipping this paper.")
            return None, None

def extract_and_convert(paper, source_path):
    if source_path:
        try:
            extraction_path = os.path.join('extracted', paper.get_short_id())
            with tarfile.open(source_path) as tar:
                tar.extractall(path=extraction_path)
            tex_files = [f for f in os.listdir(extraction_path) if f.endswith('.tex')]
            if tex_files:
                tex_path = os.path.join(extraction_path, tex_files[0])
                process_file(paper, tex_path)
        except tarfile.ReadError:
            print(f"Failed to extract {source_path}, it may not be a valid tar file.")

def process_file(paper, tex_path):
    html_output = os.path.join('html', f"{paper.get_short_id()}.html")
    cmd = f"latexml {tex_path} --destination={paper.get_short_id()}.xml"
    latexml_status = subprocess.run(cmd, shell=True, capture_output=True)
    if latexml_status.returncode == 0:
        cmd_post = f"latexmlpost --destination={html_output} --format=html {paper.get_short_id()}.xml"
        latexmlpost_status = subprocess.run(cmd_post, shell=True, capture_output=True)
        if latexmlpost_status.returncode == 0:
            pdf_response = requests.get(paper.pdf_url, stream=True)
            pdf_path = os.path.join('pdf', f"{paper.get_short_id()}.pdf")
            with open(pdf_path, 'wb') as f:
                f.raw.decode_content = True
                shutil.copyfileobj(pdf_response.raw, f)
            print(f"Downloaded PDF for {paper.title}")
        else:
            print(f"Error in XML to HTML conversion: {latexmlpost_status.stderr.decode()}")
    else:
        print(f"Error in LaTeX to XML conversion: {latexml_status.stderr.decode()}")

async def main(num_papers):
    # Create necessary directories
    os.makedirs('pdf', exist_ok=True)
    os.makedirs('source', exist_ok=True)
    os.makedirs('extracted', exist_ok=True)
    os.makedirs('html', exist_ok=True)

    # Setup the client and search
    client = arxiv.Client()
    search = arxiv.Search(
        query="all",
        max_results=num_papers,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )

    async with aiohttp.ClientSession() as session:
        tasks = [download_paper(session, paper) for paper in client.results(search)]
        download_results = await asyncio.gather(*tasks)
        download_results = [result for result in download_results if result[0] is not None]

        # Use multiprocessing for conversion
        with Pool(processes=os.cpu_count()) as pool:
            pool.starmap(extract_and_convert, download_results)

    # Cleanup
    shutil.rmtree('extracted')
    shutil.rmtree('source')
    print("Deleted 'extracted' and 'source' directories.")

    # Cleanup non-HTML files and directories in the HTML directory
    for item in os.listdir('html'):
        item_path = os.path.join('html', item)
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)  # Remove directories
        elif not item.endswith('.html'):
            os.remove(item_path)  # Remove non-HTML files
    print("Cleaned up HTML directory.")

    for filename in os.listdir('.'):
        if filename.endswith('.log') or filename.endswith('.xml'):
            os.remove(filename)
    print("Deleted .log and .xml files.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Download and process arXiv papers")
    parser.add_argument('num_papers', type=int, help='Number of papers to download and process')
    args = parser.parse_args()
    asyncio.run(main(args.num_papers))
