"""Citation and source requirements for agent prompts"""

CITATION_INSTRUCTIONS = """
<citation_requirements>
CRITICAL: You MUST cite sources using numbered format: [1], [2], [3], etc.
- ONLY use information from the provided web sources
- Every factual claim requires a citation
- Format: "Statement [1]" or "According to research [2], ..."
- Include at least 3 citations in your response
- If no sources are provided, explicitly state "No sources available"
</citation_requirements>
"""

SOURCE_USAGE_INSTRUCTIONS = """
<source_usage>
You have been provided with web search results. These are your ONLY source of truth.
DO NOT use information from your training data unless explicitly confirmed by sources.
If sources conflict, note the conflict and cite both: "Source [1] states X, while [2] claims Y"
</source_usage>
"""

def format_sources_with_indices(sources: list) -> tuple[str, list]:
    """
    Format search results with numbered indices for citation.
    
    Returns:
        tuple: (formatted_text, sources_metadata)
    """
    if not sources:
        return "No sources available.", []
    
    formatted_parts = []
    metadata = []
    
    for i, source in enumerate(sources, 1):
        title = source.get("title", "Untitled")
        url = source.get("url", "")
        snippet = source.get("snippet", source.get("content", ""))[:500]
        
        formatted_parts.append(f"""[{i}] {title}
URL: {url}
Content: {snippet}
""")
        
        metadata.append({
            "index": i,
            "title": title,
            "url": url,
            "snippet": snippet[:200]
        })
    
    formatted_text = "\n".join(formatted_parts)
    return formatted_text, metadata


def validate_citations(content: str, sources_metadata: list) -> dict:
    """
    Validate that citations in content reference valid sources.
    
    Returns:
        dict with 'valid', 'citation_count', 'issues'
    """
    import re
    
    # Find all citations [1], [2], etc.
    citations = re.findall(r'\[(\d+)\]', content)
    citation_indices = set(int(c) for c in citations)
    
    valid_indices = set(s["index"] for s in sources_metadata)
    
    issues = []
    
    # Check for citations to non-existent sources
    invalid_citations = citation_indices - valid_indices
    if invalid_citations:
        issues.append(f"Citations reference non-existent sources: {invalid_citations}")
    
    # Check minimum citation count
    if len(citation_indices) < 2 and sources_metadata:
        issues.append(f"Only {len(citation_indices)} unique sources cited, expected at least 2")
    
    return {
        "valid": len(issues) == 0,
        "citation_count": len(citation_indices),
        "unique_sources_cited": list(citation_indices),
        "issues": issues
    }
