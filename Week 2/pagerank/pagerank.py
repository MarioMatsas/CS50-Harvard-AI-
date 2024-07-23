import os
import random
import re
import sys

DAMPING = 0.85
SAMPLES = 10000


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python pagerank.py corpus")
    corpus = crawl(sys.argv[1])
    ranks = sample_pagerank(corpus, DAMPING, SAMPLES)
    print(f"PageRank Results from Sampling (n = {SAMPLES})")
    for page in sorted(ranks):
        print(f"  {page}: {ranks[page]:.4f}")
    ranks = iterate_pagerank(corpus, DAMPING)
    print(f"PageRank Results from Iteration")
    for page in sorted(ranks):
        print(f"  {page}: {ranks[page]:.4f}")


def crawl(directory):
    """
    Parse a directory of HTML pages and check for links to other pages.
    Return a dictionary where each key is a page, and values are
    a list of all other pages in the corpus that are linked to by the page.
    """
    pages = dict()

    # Extract all links from HTML files
    for filename in os.listdir(directory):
        if not filename.endswith(".html"):
            continue
        with open(os.path.join(directory, filename)) as f:
            contents = f.read()
            links = re.findall(r"<a\s+(?:[^>]*?)href=\"([^\"]*)\"", contents)
            pages[filename] = set(links) - {filename}

    # Only include links to other pages in the corpus
    for filename in pages:
        pages[filename] = set(
            link for link in pages[filename]
            if link in pages
        )

    return pages


def transition_model(corpus, page, damping_factor):
    """
    Return a probability distribution over which page to visit next,
    given a current page.

    With probability `damping_factor`, choose a link at random
    linked to by `page`. With probability `1 - damping_factor`, choose
    a link at random chosen from all pages in the corpus.
    """
    linked_pages = corpus[page]
    total_pages = len(corpus)
    probability_distribution = {}

    # Probability for any page in the corpus to be chosen
    cor_choose = (1 - damping_factor)/total_pages
    # If no links from the current page to the others are found, then just 
    # set the number of linked pages to all pages
    if len(linked_pages) == 0:
        linked_pages = corpus.keys()
    # Probability for any page linked to the current one to be chosen
    link_choose = damping_factor/len(linked_pages)

    for p in corpus:
        if p in corpus[page]:
            # P(p) = P(link) + P(cor) since they can be chosen in both senarios
            probability_distribution[p] = link_choose + cor_choose
        else:
            probability_distribution[p] = cor_choose
    
    return probability_distribution
    

def sample_pagerank(corpus, damping_factor, n):
    """
    Return PageRank values for each page by sampling `n` pages
    according to transition model, starting with a page at random.

    Return a dictionary where keys are page names, and values are
    their estimated PageRank value (a value between 0 and 1). All
    PageRank values should sum to 1.
    """
    result = {}
    for p in corpus:
        result[p] = 0
    
    # Choose the first page at random
    page = random.choice(list(corpus.keys()))
    result[page] += 1

    for _ in range(1, n):
        # Get the probability to pick any of the pages and pick one based on that 
        probabilities = transition_model(corpus, page, damping_factor)
        page = random.choices(list(probabilities.keys()), weights=probabilities.values(), k=1)[0]
        result[page] += 1

    # Normalize result
    for p in corpus:
        result[p] = result[p] / n
    return result




def iterate_pagerank(corpus, damping_factor):
    """
    Return PageRank values for each page by iteratively updating
    PageRank values until convergence.

    Return a dictionary where keys are page names, and values are
    their estimated PageRank value (a value between 0 and 1). All
    PageRank values should sum to 1.
    """
    N = len(corpus)
    result = {}
    for p in corpus:
        result[p] = 1/N

    # Ensure pages with no links are treated as linking to all pages
    for page in corpus:
        if len(corpus[page]) == 0:
            corpus[page] = set(corpus.keys())
    
    while True:
        new_result = result.copy() 
        # Get the new results as per the Background
        for p in corpus:
            s = sum(result[pg]/len(corpus[pg]) for pg in corpus if p in corpus[pg])
            new_result[p] = (1-damping_factor)/N + damping_factor*s
        
        # Check to see if the result hasn't changed too much
        end = 0
        for p in result:
            if abs(new_result[p] - result[p]) >= 0.001:
                end = 1
        result = new_result
        
        if end == 0:
            break
    
    return result

if __name__ == "__main__":
    main()
