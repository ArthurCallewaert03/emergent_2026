"""Small dependency-free BM25 scorer for the offline navigator."""
from collections import Counter
from math import log


class BM25Okapi:
    def __init__(self, corpus, k1=1.5, b=0.75):
        self.docs = [Counter(tokens) for tokens in corpus]
        self.lengths = [sum(doc.values()) for doc in self.docs]
        self.avg_length = sum(self.lengths) / max(len(self.lengths), 1)
        self.k1, self.b = k1, b
        df = Counter(token for doc in self.docs for token in doc)
        self.idf = {term: log(1 + (len(self.docs) - count + 0.5) / (count + 0.5))
                    for term, count in df.items()}

    def get_scores(self, query):
        scores = []
        for doc, length in zip(self.docs, self.lengths):
            norm = self.k1 * (1 - self.b + self.b * length / max(self.avg_length, 1))
            scores.append(sum(self.idf.get(term, 0) * count * (self.k1 + 1) / (count + norm)
                              for term in query if (count := doc.get(term, 0))))
        return scores
