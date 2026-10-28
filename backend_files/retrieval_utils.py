"""Hybrid lexical/vector retrieval with policy headings and table context."""
import math
import re
from collections import Counter

STOP = set('a an the is are was were be been being to of for and or in on at as by with '
           'i me my we our you your it its this that there what which how can could would '
           'should do does did have has had will may need get'.split())


def words(text):
    text = re.sub(r'check[ -]?in', 'checkin', text.lower())
    text = re.sub(r'check[ -]?out', 'checkout', text)
    groups = {
        'cancel': ['cancellation', 'cancellations', 'canceled', 'cancelled', 'canceling'],
        'smoke': ['smoking', 'smokes', 'smoked'],
        'vape': ['vaping', 'vapes', 'vaped'],
        'noise': ['loud', 'noisy', 'disturbance', 'disturbances'],
        'pet': ['pets', 'dog', 'dogs'],
        'refund': ['refunds', 'refunded', 'refunding'],
        'charge': ['charges', 'charged', 'charging'],
        'hold': ['holds', 'pending', 'authorization', 'authorizations'],
        'fee': ['fees', 'cost', 'costs', 'budget'],
        'late': ['deadline', 'cutoff'],
    }
    aliases = {item: key for key, items in groups.items() for item in items}
    return [aliases.get(w, w) for w in re.findall(r'[a-z0-9]+', text)
            if w not in STOP and len(w) > 1]


def annotate_chunks(chunks, raw_docs):
    texts = {doc.metadata['source']: doc.page_content for doc in raw_docs}
    for chunk in chunks:
        text = texts[chunk.metadata['source']]
        start = chunk.metadata.get('start_index', 0)
        preceding = text[:start]
        headings = list(re.finditer(r'^#{1,6} .+$', preceding, re.M))
        title = headings[-1].group().lstrip('# ') if headings else ''
        chunk.metadata['section_title'] = title
        section_start = headings[-1].end() if headings else 0
        table_rows = list(re.finditer(r'^\|.+\|\s*\n\|\s*:?-', text[section_start:start + len(chunk.page_content)], re.M))
        if table_rows:
            chunk.metadata['table_header'] = table_rows[-1].group().splitlines()[0]
    return chunks


def search(query, k, vectorstore):
    documents = list(vectorstore.docstore._dict.values())
    corpus = [words(d.metadata.get('section_title', '') + ' ' +
                    d.metadata.get('table_header', '') + ' ' + d.page_content) for d in documents]
    frequencies = [Counter(row) for row in corpus]
    terms = set(words(query))
    avg_length = sum(map(len, corpus)) / max(len(corpus), 1)
    idfs = {term: math.log(1 + (len(corpus) - sum(term in row for row in frequencies) + 0.5)
                          / (sum(term in row for row in frequencies) + 0.5)) for term in terms}
    scores = []
    for row, counts in zip(corpus, frequencies):
        score = sum(idfs[t] * counts[t] * 2.5 /
                    (counts[t] + 1.5 * (0.25 + 0.75 * len(row) / max(avg_length, 1)))
                    for t in terms if counts[t])
        scores.append(score)
    lexical_order = sorted(range(len(documents)), key=lambda i: scores[i], reverse=True)
    lexical_rank = {i: rank for rank, i in enumerate(lexical_order)}
    dense = vectorstore.similarity_search(query, k=min(30, len(documents)))
    dense_rank = {d.metadata.get('chunk_id'): i for i, d in enumerate(dense)}
    order = sorted(range(len(documents)), key=lambda i:
        0.8 / (10 + lexical_rank[i]) +
        0.2 / (10 + dense_rank.get(documents[i].metadata.get('chunk_id'), 1000)), reverse=True)
    chosen, token_sets = [], []
    for index in order:
        document = documents[index]
        tokens = set(corpus[index])
        if any(len(tokens & previous) / max(len(tokens | previous), 1) > 0.65 for previous in token_sets):
            continue
        chosen.append(document)
        token_sets.append(tokens)
        if len(chosen) == k:
            break
    return chosen
