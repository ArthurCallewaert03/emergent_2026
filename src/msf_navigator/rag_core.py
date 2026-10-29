"""Markdown chunk retrieval and optional local Ollama answer generation."""
import json
import re
from urllib.request import Request, urlopen

from .local_bm25 import BM25Okapi
from .navigator_core import tokenize, search
from .enrich_metadata import COUNTRIES

OLLAMA = "http://127.0.0.1:11434"
PARTNER_CUE = re.compile(r"\b(partner|partnership|partners|partenaire|partenariat|collaborat\w*|cooperat\w*|coopérat\w*|socio|asociaci[oó]n)\b", re.I)
PARTNER_RELATION = re.compile(
    r"\b(?:partner(?:ship)?\s+(?:with|organisation|organization)|"
    r"in\s+collaboration\s+with|working\s+with|worked\s+with|"
    r"collaborat(?:ing|ed)\s+with|partenaire\s+(?:avec|local)|"
    r"en\s+partenariat\s+avec)\b", re.I)
SPECULATIVE = re.compile(r"\b(?:must|should|will|would|urge|urged|calling on|called on|needs to)\b", re.I)
COUNTRY_EXTRA = {"Syria": ["Syrian", "Syrien", "syrienne"], "Sudan": ["Sudanese"],
                 "Haiti": ["Haitian", "Haïtien"], "Ukraine": ["Ukrainian"],
                 "Palestine": ["Palestinian"], "Afghanistan": ["Afghan"]}


def split_markdown(text, target=1400, overlap=180):
    """Make bounded chunks while carrying the current Markdown heading."""
    heading = ""
    section = 0
    for block in re.split(r"\n\s*\n", text):
        block = block.strip()
        if not block:
            continue
        lines = block.splitlines()
        if lines[0].lstrip().startswith("#"):
            heading = lines[0].lstrip("# ").strip()[:140]
            section += 1
        # Some parsed PDFs have very long blocks; split them deterministically.
        step = max(1, target - overlap)
        for start in range(0, len(block), step):
            piece = block[start:start + target].strip()
            if piece:
                yield heading, section, piece
            if start + target >= len(block):
                break


def build_chunk_index(documents):
    chunks = []
    for doc in documents:
        for number, (heading, section, text) in enumerate(split_markdown(doc["text"]), 1):
            chunks.append({"id": doc["id"], "citation": f"{doc['id']}:{number}",
                           "title": doc["title"], "heading": heading,
                           "section": section, "text": text, "language": doc["language"],
                           "genre": doc["genre"], "country_mentions": doc["country_mentions"],
                           "topic_tags": doc["topic_tags"],
                           "original_path": doc.get("original_path", ""),
                           "parsed_path": doc["parsed_path"]})
    index = BM25Okapi([tokenize(c["text"]) for c in chunks])
    return chunks, index


def retrieve(query, chunks, index, language="All", genre="All", country="All", topic="All", limit=5):
    terms = tokenize(query)
    if not terms:
        return []
    scores = index.get_scores(terms)
    ranked = []
    for chunk, score in zip(chunks, scores):
        if score <= 0 or (language != "All" and chunk["language"] != language):
            continue
        if genre != "All" and chunk["genre"] != genre:
            continue
        if country != "All" and country not in chunk["country_mentions"].split("|"):
            continue
        if topic != "All" and topic not in chunk["topic_tags"].split("|"):
            continue
        ranked.append((chunk, float(score)))
    ranked.sort(key=lambda item: (-item[1], item[0]["citation"]))
    selected, per_doc = [], {}
    for item in ranked:
        doc_id = item[0]["id"]
        if per_doc.get(doc_id, 0) >= 2:
            continue
        selected.append(item)
        per_doc[doc_id] = per_doc.get(doc_id, 0) + 1
        if len(selected) == limit:
            break
    return selected


def extract_evidence(query, retrieved, limit=3):
    """Return exact, query-bearing sentences when model output is unavailable."""
    terms = set(tokenize(query))
    candidates = []
    for chunk, score in retrieved:
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", chunk["text"]):
            sentence = sentence.strip()
            if not 25 <= len(sentence) <= 500:
                continue
            hits = len(terms & set(tokenize(sentence)))
            if hits:
                candidates.append((hits, score, chunk["citation"], sentence))
    candidates.sort(key=lambda item: (-item[0], -item[1], item[2]))
    seen, used_docs, result = set(), set(), []
    for _, _, citation, sentence in candidates:
        if sentence in seen or citation.split(":", 1)[0] in used_docs:
            continue
        result.append((citation, sentence))
        seen.add(sentence)
        used_docs.add(citation.split(":", 1)[0])
        if len(result) == limit:
            break
    return result


def country_in_question(question):
    """Recognize a named country in a natural-language question."""
    matches = []
    for country, aliases in COUNTRIES.items():
        for alias in aliases:
            match = re.search(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", question, re.I)
            if match:
                matches.append((len(alias), country))
    return max(matches)[1] if matches else None


def partner_passages(country, chunks, index, limit=8):
    """Find passages that mention a country and partnership language."""
    aliases = COUNTRIES.get(country, [country]) + COUNTRY_EXTRA.get(country, [])
    query = f"{country} {' '.join(COUNTRY_EXTRA.get(country, []))} partner organisation partnership collaboration"
    candidates = retrieve(query, chunks, index, country=country, limit=60)
    selected = []
    for chunk, score in candidates:
        text = chunk["text"]
        if not any(not SPECULATIVE.search(text[max(0, relation.start()-100):relation.start()])
                   for relation in PARTNER_RELATION.finditer(text)):
            continue
        direct = any(re.search(r"(?<!\w)" + re.escape(a) + r"(?!\w)", text, re.I) for a in aliases)
        if direct:
            selected.append((chunk, score))
        if len(selected) >= limit:
            break
    return selected


def extract_partners(question, country, retrieved, model, timeout=180):
    """Ask Ollama for candidate names, then verify name and cue in source text."""
    if not retrieved:
        return [], 0
    context = "\n\n".join(f"[{c['citation']}] {c['text'][:1400]}" for c, _ in retrieved)
    system = (
        "Find organisations explicitly described as partners or collaborators in the supplied passages. "
        "Return JSON only: {\"partners\":[{\"name\":\"exact source name\",\"citation\":\"D123:4\"}]}. "
        "Do not infer a partnership from a mere mention. Do not include MSF itself. "
        "If no names are explicit, return an empty partners list."
    )
    payload = {"model": model, "stream": False, "think": False, "format": "json",
               "options": {"temperature": 0, "num_predict": 350},
               "messages": [{"role": "system", "content": system},
                            {"role": "user", "content": f"Question: {question}\nCountry: {country}\n\nPassages:\n{context}"}]}
    request = Request(OLLAMA + "/api/chat", data=json.dumps(payload).encode("utf-8"),
                      headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=timeout) as response:
        items = json.loads(json.load(response)["message"]["content"]).get("partners", [])
    if isinstance(items, (str, dict)):
        items = [items]
    sources = {c["citation"]: c for c, _ in retrieved}
    accepted, rejected, seen = [], 0, set()
    for item in items[:12]:
        name = str(item.get("name", "") if isinstance(item, dict) else item).strip()
        citation = str(item.get("citation", "") if isinstance(item, dict) else "").strip().strip("[]")
        if len(name) < 3 or len(name) > 100 or name.casefold() in seen or name.casefold() in {"msf", "médecins sans frontières", "doctors without borders"}:
            rejected += 1
            continue
        candidates = [sources[citation]] if citation in sources else [c for c, _ in retrieved]
        found = next(((chunk, match) for chunk in candidates if (match := re.search(re.escape(name), chunk["text"], re.I))), None)
        if not found:
            rejected += 1
            continue
        chunk, match = found
        if not match:
            rejected += 1
            continue
        start, end = max(0, match.start()-200), min(len(chunk["text"]), match.end()+200)
        evidence = re.sub(r"\s+", " ", chunk["text"][start:end]).strip()
        relation_near_name = any(
            relation.end() <= match.start() and match.start() - relation.end() <= 100
            and not SPECULATIVE.search(chunk["text"][max(0, relation.start()-100):relation.start()])
            for relation in PARTNER_RELATION.finditer(chunk["text"])
        )
        if not relation_near_name:
            rejected += 1
            continue
        accepted.append({"name": name, "citation": chunk["citation"], "evidence": evidence,
                         "source_path": chunk["original_path"] or chunk["parsed_path"]})
        seen.add(name.casefold())
    return accepted, rejected


def ollama_models(timeout=3):
    with urlopen(OLLAMA + "/api/tags", timeout=timeout) as response:
        return [m["name"] for m in json.load(response).get("models", [])]


def local_search_queries(question, model, timeout=90):
    """Use the local model to turn a question into lexical corpus queries."""
    payload = {"model": model, "stream": False, "think": False, "format": "json",
               "options": {"temperature": 0, "num_predict": 180},
               "messages": [{"role": "system", "content":
                             "Create 2 or 3 short keyword searches for finding source passages that answer the question. "
                             "Use synonyms and document terminology. Return JSON only: {\"queries\":[\"query one\",\"query two\"]}. "
                             "Do not answer the question."},
                            {"role": "user", "content": question}]}
    request = Request(OLLAMA + "/api/chat", data=json.dumps(payload).encode("utf-8"),
                      headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=timeout) as response:
        raw = json.load(response)["message"]["content"]
    result = json.loads(raw)
    queries = result.get("queries", result.get("search_queries", result.get("query", [])))
    if isinstance(queries, str):
        queries = [queries]
    if not isinstance(queries, list):
        queries = []
    country = country_in_question(question)
    if country and re.search(r"partner|collaborat|organis|organiz", question, re.I):
        queries.extend([f"{country} {' '.join(COUNTRY_EXTRA.get(country, []))} partner organisation partnership collaboration",
                        f"{country} local partner ministry health organisation"])
    return list(dict.fromkeys([question] + [q.strip() for q in queries[:4]
                                                if isinstance(q, str) and 3 <= len(q.strip()) <= 120]))


def retrieve_multiple(queries, chunks, index, language="All", genre="All", country="All", topic="All", limit=6):
    """Merge BM25 passage hits from the question and local-model search terms."""
    found = {}
    for query in queries:
        for rank, (chunk, score) in enumerate(retrieve(query, chunks, index, language, genre,
                                                       country, topic, limit=12)):
            key = chunk["citation"]
            value = 1 / (rank + 1)
            if key not in found:
                found[key] = (chunk, 0)
            found[key] = (chunk, found[key][1] + value)
    ranked = sorted(found.values(), key=lambda item: (-item[1], item[0]["citation"]))
    selected, per_doc = [], {}
    for item in ranked:
        doc_id = item[0]["id"]
        if per_doc.get(doc_id, 0) >= 2:
            continue
        selected.append(item)
        per_doc[doc_id] = per_doc.get(doc_id, 0) + 1
        if len(selected) == limit:
            break
    return selected


def retrieve_via_documents(queries, documents, document_index, chunks, chunk_index,
                           language="All", genre="All", country="All", topic="All",
                           document_limit=20, passage_limit=3):
    """Find whole documents first, then rank passages inside that shortlist."""
    doc_scores = {}
    for query in queries:
        hits = search(query, documents, document_index, language, genre, country, topic, limit=30)
        for rank, (doc, _) in enumerate(hits):
            doc_scores[doc["id"]] = doc_scores.get(doc["id"], 0) + 1 / (rank + 1)
    ranked_docs = sorted((d for d in documents if d["id"] in doc_scores),
                         key=lambda d: (-doc_scores[d["id"]], d["id"]))[:document_limit]
    allowed = {d["id"] for d in ranked_docs}
    if not allowed:
        return [], []
    candidate_indices = [i for i, chunk in enumerate(chunks) if chunk["id"] in allowed]
    passage_scores = {}
    for query in queries:
        scores = chunk_index.get_scores(tokenize(query))
        ranked = sorted((i for i in candidate_indices if scores[i] > 0),
                        key=lambda i: (-scores[i], chunks[i]["citation"]))[:25]
        for rank, i in enumerate(ranked):
            citation = chunks[i]["citation"]
            passage_scores[citation] = passage_scores.get(citation, 0) + 1 / (rank + 1)
    partner_intent = bool(re.search(r"partner|collaborat|organis|organiz|work(?:ed|ing|s)? with", queries[0], re.I))
    target_country = country_in_question(queries[0]) if partner_intent else None
    def direct_partner_evidence(chunk):
        if not target_country:
            return False
        aliases = COUNTRIES.get(target_country, [target_country]) + COUNTRY_EXTRA.get(target_country, [])
        places = [m for alias in aliases for m in re.finditer(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", chunk["text"], re.I)]
        relations = [m for m in PARTNER_RELATION.finditer(chunk["text"])
                     if not SPECULATIVE.search(chunk["text"][max(0, m.start()-100):m.start()])]
        return any(abs(place.start() - relation.start()) <= 300
                   for place in places for relation in relations)
    def passage_rank(chunk):
        bonus = 0
        if partner_intent and any(
            not SPECULATIVE.search(chunk["text"][max(0, relation.start()-100):relation.start()])
            for relation in PARTNER_RELATION.finditer(chunk["text"])
        ):
            bonus = 1
        return (-(passage_scores[chunk["citation"]] + bonus), chunk["citation"])
    ranked_chunks = sorted((c for c in chunks if c["citation"] in passage_scores), key=passage_rank)
    if partner_intent and target_country:
        direct = [c for c in ranked_chunks if direct_partner_evidence(c)]
        if direct:
            ranked_chunks = direct
    passages, per_doc = [], {}
    for chunk in ranked_chunks:
        if per_doc.get(chunk["id"], 0) >= 2:
            continue
        passages.append((chunk, passage_scores[chunk["citation"]]))
        per_doc[chunk["id"]] = per_doc.get(chunk["id"], 0) + 1
        if len(passages) == passage_limit:
            break
    return ranked_docs, passages


def answer_question(question, retrieved, model, timeout=180):
    """Draft a cited answer, rejecting nonexistent or missing passage citations."""
    if not retrieved:
        raise ValueError("No source passages were retrieved.")
    context = "\n\n".join(
        f"[{chunk['citation']}] {chunk['title']}\n{chunk['text'][:1200]}"
        for chunk, _ in retrieved
    )
    valid = {chunk["citation"] for chunk, _ in retrieved}
    answer_schema = {"type": "object", "properties": {
        "answer": {"type": "string"},
        "citations": {"type": "array", "items": {"type": "string", "enum": sorted(valid)}}},
        "required": ["answer", "citations"]}
    payload = {"model": model, "stream": False, "think": False, "format": answer_schema,
               "options": {"temperature": 0, "num_predict": 450},
               "messages": [{"role": "system", "content":
                             "Answer the question in no more than 130 words using only the supplied passages. "
                             "Put the passage IDs that support your answer in the citations field. "
                             "If the passages do not answer it, say the evidence is insufficient and leave citations empty. "
                             "Do not invent names, protocols, dosages, or facts. Do not show reasoning."},
                            {"role": "user", "content": f"Question: {question}\n\nPassages:\n{context}"}]}
    request = Request(OLLAMA + "/api/chat", data=json.dumps(payload).encode("utf-8"),
                      headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=timeout) as response:
        raw = json.load(response)["message"]["content"]
    result = json.loads(raw)
    answer = str(result.get("answer", "")).strip()
    listed = result.get("citations", [])
    if isinstance(listed, str):
        listed = [listed]
    cited = set(re.findall(r"\[([^\]]+)\]", answer)) | {str(x).strip().strip("[]") for x in listed if isinstance(x, str)}
    if not answer:
        raise ValueError(f"The local model returned no answer text. Raw response: {raw[:350]}")
    invalid = cited - valid
    for citation in invalid:
        answer = answer.replace(f"[{citation}]", "")
    cited -= invalid
    if not re.search(r"\[[^\]]+\]", answer):
        answer += (" " + " ".join(f"[{x}]" for x in sorted(cited))) if cited else ""
    return answer, cited, invalid


def generate_answer(query, retrieved, model, timeout=180):
    if not retrieved:
        raise ValueError("No source passages were retrieved.")
    context = "\n\n".join(
        f"[{chunk['citation']}] {chunk['title']} — {chunk['heading']}\n{chunk['text'][:1400]}"
        for chunk, _ in retrieved
    )
    system = (
        "Select up to three short exact contiguous quotations from the source passages that answer the question. "
        "Return JSON only: {\"quotes\":[{\"citation\":\"D123:4\",\"quote\":\"exact words from passage\"}]}. "
        "Do not paraphrase, infer, invent text, or include commentary. If unsupported, return an empty quotes list."
    )
    prompt = f"Question: {query}\n\nSource passages:\n{context}"
    payload = {"model": model, "stream": False, "think": False, "format": "json",
               "options": {"temperature": 0, "num_predict": 400},
               "messages": [{"role": "system", "content": system},
                            {"role": "user", "content": prompt}]}
    request = Request(OLLAMA + "/api/chat", data=json.dumps(payload).encode("utf-8"),
                      headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=timeout) as response:
        response_text = json.load(response)["message"]["content"].strip()
    selected = json.loads(response_text).get("quotes", [])
    sources = {c["citation"]: c["text"] for c, _ in retrieved}
    accepted = []
    rejected = 0
    for item in selected[:3]:
        citation, quote = item.get("citation", ""), item.get("quote", "")
        source = sources.get(citation, "")
        normalize = lambda value: re.sub(r"\s+", " ", value).strip()
        if citation and 20 <= len(quote) <= 500 and normalize(quote) in normalize(source):
            accepted.append((citation, quote))
        else:
            rejected += 1
    return accepted, rejected
