"""Local document navigator for the supplied D4GC corpus."""
from pathlib import Path
import sys
import re

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
ASSETS = Path(__file__).resolve().parent / "assets"
from msf_navigator.navigator_core import ROOT, load_index, search, excerpt
from msf_navigator.rag_core import (build_chunk_index, ollama_models,
                      country_in_question, partner_passages, extract_partners,
                      local_search_queries, retrieve_via_documents, answer_question)

st.set_page_config(page_title="MSF Document Navigator", page_icon="📚", layout="wide")
st.markdown(f"<style>{(ASSETS / 'msf_theme.css').read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
st.image(str(ASSETS / "msf-azg-logo-en.svg"), width=205)
st.markdown(
    '<div class="msf-kicker">Independent Data 4 Good prototype</div>'
    '<div class="msf-header-title">Document navigator</div>'
    '<p class="msf-header-copy">Explore the supplied MSF documents and trace answers to their sources.</p>',
    unsafe_allow_html=True)
st.markdown('<hr class="msf-rule">', unsafe_allow_html=True)


@st.cache_resource(show_spinner="Indexing the local document collection…")
def cached_index():
    return load_index()


try:
    documents, index = cached_index()
except (FileNotFoundError, ValueError) as error:
    st.error(str(error))
    st.stop()

st.markdown(
    '<div class="msf-note">'
    f'<strong>{len(documents)} supplied documents indexed locally.</strong> '
    'Find documents ranks source text. Ask LLM drafts an answer from retrieved '
    'passages and shows its sources. Review those passages before acting.'
    '</div>',
    unsafe_allow_html=True,
)

@st.cache_resource(show_spinner="Indexing Markdown passages…")
def cached_chunks():
    return build_chunk_index(documents)

with st.sidebar:
    st.header("Refine results")
    languages = sorted({d["language"] for d in documents if d["language"]})
    genres = sorted({d["genre"] for d in documents if d["genre"]})
    countries = sorted({v for d in documents for v in d["country_mentions"].split("|") if v})
    topics = sorted({v for d in documents for v in d["topic_tags"].split("|") if v})
    language = st.selectbox("Language", ["All", *languages])
    genre = st.selectbox("Genre", ["All", *genres])
    country = st.selectbox("Country mention", ["All", *countries], help="Candidate text mentions; not verified primary locations.")
    topic = st.selectbox("Topic tag", ["All", *topics], help="Keyword tags; incomplete across languages.")
    limit = st.slider("Results", 5, 30, 10, 5)
    st.caption("All indexing and search run locally. Location and topic filters can hide relevant documents.")

mode = st.radio("Mode", ["Find documents", "Ask LLM", "Find partners (optional)"], horizontal=True)
query = st.text_input("Search the documents" if mode == "Find documents" else "Ask a question",
                      placeholder="e.g. Who are the partners in Syria?")
if not query.strip():
    st.write("Find documents searches the collection. Ask LLM finds documents, selects relevant passages from them, and drafts an answer. The partner finder is a focused example.")
    st.stop()

if mode == "Ask LLM":
    try:
        models = ollama_models(timeout=10)
    except Exception:
        models = []
    if not models:
        st.warning("The local model service is unavailable. Start `ollama serve` and try again.")
        st.stop()
    preferred = "qwen3:4b" if "qwen3:4b" in models else models[0]
    model = st.selectbox("Local model", models, index=models.index(preferred))
    request_key = (query, language, genre, country, topic, model)
    if st.button("Ask local model", type="primary"):
        chunks, chunk_index = cached_chunks()
        try:
            with st.spinner("Searching local documents and drafting a cited answer…"):
                try:
                    queries = local_search_queries(query, model)
                except Exception:
                    queries = [query]
                found_docs, passages = retrieve_via_documents(
                    queries, documents, index, chunks, chunk_index, language, genre, country, topic)
                if passages:
                    try:
                        answer, cited, invalid = answer_question(query, passages, model)
                        error = ""
                    except Exception as exc:
                        answer, cited, invalid, error = "", set(), set(), str(exc)
                else:
                    answer, cited, invalid, error = "", set(), set(), "No matching source passages."
            st.session_state["llm_search_result"] = (request_key, queries, found_docs, passages, answer, cited, invalid, error)
        except Exception as exc:
            st.error(f"Local search failed: {exc}")
    saved = st.session_state.get("llm_search_result")
    if saved and saved[0] == request_key:
        _, queries, found_docs, passages, answer, cited, invalid, error = saved
        if answer:
            st.subheader("Draft answer from local model")
            if not cited:
                st.warning("The model gave no valid passage citation. This is an unverified draft; check the retrieved passages below before using it.")
            else:
                st.warning("Check the cited passages below. A citation confirms the passage exists, not that the model interpreted it correctly.")
            if invalid:
                st.caption(f"Removed {len(invalid)} citation(s) that did not match a retrieved passage.")
            st.markdown(answer)
        else:
            st.info(f"No cited answer produced: {error} Review the retrieved passages below.")
        with st.expander("Search terms used"):
            for search_query in queries:
                st.write(search_query)
        with st.expander(f"Documents found first ({len(found_docs)})"):
            for doc in found_docs:
                st.write(f"[{doc['id']}] {doc['title']}")
        st.subheader("Sources supplied to the model")
        st.caption("These passages were provided as context. A passage ID in the answer identifies a source the model cited; check its text before relying on the answer.")
        for chunk, score in passages:
            st.markdown(f"**[{chunk['citation']}] {chunk['title']}** · {chunk['language']} · {chunk['genre']}")
            with st.expander(f"[{chunk['citation']}] {chunk['title']} · score {score:.2f}"):
                st.write(chunk["text"])
                source_rel = chunk["original_path"] or chunk["parsed_path"]
                st.caption(source_rel)
                source = ROOT / source_rel
                if source.is_file():
                    with source.open("rb") as handle:
                        st.download_button("Download original", handle, file_name=source.name,
                                           key=f"llm-source-{chunk['citation']}")
    st.stop()

if mode == "Find partners (optional)":
    st.info("This focused search looks for a country and partnership wording in the same source passage. The local model proposes organisation names; the app keeps a name only when it appears near partnership wording in that passage. Results may be historical.")
    chosen_country = country if country != "All" else country_in_question(query)
    if not chosen_country:
        st.info("Name a country in your question or choose one under Country mention in the sidebar.")
        st.stop()
    chunks, chunk_index = cached_chunks()
    passages = partner_passages(chosen_country, chunks, chunk_index)
    st.caption(f"Looking for explicit partnership language in {chosen_country} passages")
    if not passages:
        st.warning("No candidate partner passages found. This does not mean there are no partners; the available documents or wording may not cover them.")
        st.stop()
    try:
        models = ollama_models(timeout=10)
    except Exception:
        models = []
    if models:
        preferred = "qwen3:4b" if "qwen3:4b" in models else models[0]
        model = st.selectbox("Local model", models, index=models.index(preferred))
        if st.button("Find partner names", type="primary"):
            try:
                with st.spinner("Checking names against the source passages…"):
                    partners, rejected = extract_partners(query, chosen_country, passages, model)
                if partners:
                    st.subheader("Partner names found in the documents")
                    st.caption("These are historical document mentions, not a verified current partner list.")
                    for partner in partners:
                        st.markdown(f"**{partner['name']}** · [{partner['citation']}]")
                        st.write(partner["evidence"])
                        st.caption(partner["source_path"])
                else:
                    st.info("The model found no names that passed source verification. Review the passages below.")
                if rejected:
                    st.caption(f"Discarded {rejected} candidate name(s) without nearby partnership evidence.")
            except Exception as error:
                st.error(f"Local model request failed: {error}")
    else:
        st.info("Start `ollama serve` to extract partner names with a local model. The source passages remain available.")
    st.subheader("Candidate source passages")
    for chunk, score in passages:
        with st.expander(f"[{chunk['citation']}] {chunk['title']} · score {score:.2f}"):
            st.write(chunk["text"])
            st.caption(chunk["original_path"] or chunk["parsed_path"])
    st.stop()

results = search(query, documents, index, language, genre, country, topic, limit)
st.write(f"Showing {len(results)} matching documents")
if not results:
    st.warning("No matches with the current terms and filters. Try fewer filters or another language.")

for rank, (doc, score) in enumerate(results, 1):
    with st.container(border=True):
        st.subheader(f"{rank}. {doc['title']}")
        st.caption(f"ID: {doc['id']} · {doc['genre']} · {doc['language']} · BM25 score: {score:.2f}")
        st.write(excerpt(doc["text"], query))
        facets = []
        if doc["country_mentions"]:
            facets.append("Country mentions: " + doc["country_mentions"].replace("|", ", "))
        if doc["city_mentions"]:
            facets.append("City mentions: " + doc["city_mentions"].replace("|", ", "))
        if doc["topic_tags"]:
            facets.append("Topic tags: " + doc["topic_tags"].replace("|", ", "))
        if facets:
            st.caption(" · ".join(facets))
        source_rel = doc.get("original_path") or doc["parsed_path"]
        source = ROOT / source_rel
        st.caption(f"Source: {source_rel}")
        if source.is_file():
            with source.open("rb") as handle:
                st.download_button("Download source", handle, file_name=source.name,
                                   key=f"source-{doc['id']}")
