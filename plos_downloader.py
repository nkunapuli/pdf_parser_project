import requests
import argparse
import os
import subprocess
import shutil

def download_plos_papers(n):
    base_url = "https://api.plos.org/search"
    downloaded_count = 0
    start = 0
    batch_size = max(10, n)  # Fetch at least 10 entries or as many as needed at a time

    # Ensure directories exist
    os.makedirs('pdf', exist_ok=True)
    os.makedirs('xml', exist_ok=True)
    os.makedirs('html', exist_ok=True)  # Create HTML directory
    os.makedirs('outputs', exist_ok=True)
    os.makedirs('figures', exist_ok=True)

    while downloaded_count < n:
        query_params = {
            "q": "*:*",
            "start": start,
            "rows": batch_size,
            "fl": "id,title",
            "wt": "json",
            "sort": "publication_date desc"
        }

        response = requests.get(base_url, params=query_params)
        papers = response.json().get('response', {}).get('docs', [])

        if not papers:
            print("No more papers found. Exiting.")
            break

        for paper in papers:
            paper_id = paper['id']
            if '/title' in paper_id or '/abstract' in paper_id or '/references' in paper_id or '/body' in paper_id:
                continue

            title = paper.get('title')
            if not title:
                continue

            # Sanitize title for filename
            sanitized_title = title.replace(' ', '_').replace('/', '_').replace('\\', '_')

            # Download PDF
            pdf_url = f"https://journals.plos.org/plosone/article/file?id={paper_id}&type=printable"
            pdf_response = requests.get(pdf_url)
            pdf_filename = f"pdf/{sanitized_title}.pdf"
            if pdf_response.status_code == 200:
                with open(pdf_filename, 'wb') as f:
                    f.write(pdf_response.content)
                print(f"Downloaded PDF: {pdf_filename}")
            else:
                print(f"Failed to download PDF for {sanitized_title}")

            # Download XML
            xml_url = f"https://journals.plos.org/plosone/article/file?id={paper_id}&type=manuscript"
            xml_response = requests.get(xml_url)
            xml_filename = f"xml/{sanitized_title}.xml"
            if xml_response.status_code == 200:
                with open(xml_filename, 'wb') as f:
                    f.write(xml_response.content)
                print(f"Downloaded XML: {xml_filename}")
                convert_xml_to_html(xml_filename, sanitized_title)
            else:
                print(f"Failed to download XML for {sanitized_title}")

            downloaded_count += 1
            if downloaded_count == n:
                break

        start += len(papers)
        if downloaded_count < n:
            remaining_papers = n - downloaded_count
            batch_size = max(10, remaining_papers)

def convert_xml_to_html(xml_filename, title):
    html_filename = f"html/{title}.html"
    command = ["pandoc", "-s", xml_filename, "-o", html_filename]
    try:
        subprocess.run(command, check=True)
        print(f"Converted {xml_filename} to HTML: {html_filename}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to convert {xml_filename} to HTML: {e}")

def main():
    parser = argparse.ArgumentParser(description="Download the N most recent papers from PLOS in PDF and XML formats, and convert XML to HTML.")
    parser.add_argument("number_of_papers", type=int, help="Number of recent papers to download")
    args = parser.parse_args()

    download_plos_papers(args.number_of_papers)
    
    # Remove the XML directory
    try:
        shutil.rmtree('xml')
        print("XML folder deleted successfully.")
    except Exception as e:
        print(f"Error deleting XML folder: {e}")

if __name__ == "__main__":
    main()
