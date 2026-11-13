import nltk

def download_resources():
    resources = ['punkt', 'punkt_tab', 'wordnet', 'omw-1.4']
    for res in resources:
        print(f"Downloading NLTK resource: {res}...")
        nltk.download(res, quiet=True)
    print("All NLTK resources downloaded successfully.")

if __name__ == "__main__":
    download_resources()