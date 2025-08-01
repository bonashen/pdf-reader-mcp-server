"""
Citation and reference parsing for academic papers
"""
import re
from typing import List, Dict, Any, Optional
from ..core.pdf_processor import PDFProcessor

class CitationParser:
    """Parses citations and references from academic papers"""
    
    # Citation patterns
    IN_TEXT_PATTERNS = [
        r'\(([A-Z][a-z]+ et al\.?, \d{4}[a-z]?)\)',  # (Smith et al., 2020)
        r'\(([A-Z][a-z]+ & [A-Z][a-z]+, \d{4}[a-z]?)\)',  # (Smith & Jones, 2020)
        r'\(([A-Z][a-z]+, \d{4}[a-z]?)\)',  # (Smith, 2020)
        r'\[(\d+)\]',  # [1]
        r'\[(\d+)-(\d+)\]',  # [1-3]
        r'\[(\d+,\s*\d+(?:,\s*\d+)*)\]',  # [1, 2, 3]
    ]
    
    # Reference patterns
    REFERENCE_PATTERNS = [
        # Author, A. (Year). Title. Journal, Volume(Issue), pages.
        r'^([A-Z][a-z]+(?:,\s[A-Z]\.)*(?:\s&\s[A-Z][a-z]+(?:,\s[A-Z]\.)*)*)\.\s*\((\d{4}[a-z]?)\)\.\s*(.+?)\.\s*([^,]+),\s*(\d+)(?:\((\d+)\))?,\s*(\d+-\d+)\.',
        # Author, A., & Author, B. (Year). Title. Journal, Volume, pages.
        r'^([A-Z][a-z]+(?:,\s[A-Z]\.)*(?:\s&\s[A-Z][a-z]+(?:,\s[A-Z]\.)*)*)\.\s*\((\d{4}[a-z]?)\)\.\s*(.+?)\.\s*([^,]+),\s*(\d+),\s*(\d+-\d+)\.',
        # Numbered references: [1] Author, A. (Year). Title...
        r'^\[(\d+)\]\s+([A-Z][a-z]+(?:,\s[A-Z]\.)*(?:(?:,\s)?\s?&\s[A-Z][a-z]+(?:,\s[A-Z]\.)*)*)\.\s*\((\d{4}[a-z]?)\)\.\s*(.+)',
    ]
    
    @staticmethod
    async def extract_citations(pdf_path: str) -> Dict[str, Any]:
        """Extract all citations from the PDF"""
        text = await PDFProcessor.extract_raw_text(pdf_path)
        
        in_text_citations = CitationParser._find_in_text_citations(text)
        references = await CitationParser._extract_references(pdf_path)
        
        return {
            "in_text_citations": in_text_citations,
            "references": references,
            "citation_count": len(in_text_citations),
            "reference_count": len(references),
            "citation_style": CitationParser._detect_citation_style(in_text_citations)
        }
    
    @staticmethod
    def _find_in_text_citations(text: str) -> List[Dict[str, Any]]:
        """Find in-text citations"""
        citations = []
        
        for pattern in CitationParser.IN_TEXT_PATTERNS:
            matches = re.finditer(pattern, text)
            for match in matches:
                citation_text = match.group(0)
                position = match.start()
                
                # Get context (50 chars before and after)
                context_start = max(0, position - 50)
                context_end = min(len(text), position + len(citation_text) + 50)
                context = text[context_start:context_end]
                
                citations.append({
                    "citation": citation_text,
                    "position": position,
                    "context": context,
                    "type": CitationParser._classify_citation_type(citation_text)
                })
        
        # Remove duplicates and sort by position
        unique_citations = []
        seen = set()
        for citation in sorted(citations, key=lambda x: x["position"]):
            if citation["citation"] not in seen:
                unique_citations.append(citation)
                seen.add(citation["citation"])
        
        return unique_citations
    
    @staticmethod
    async def _extract_references(pdf_path: str) -> List[Dict[str, Any]]:
        """Extract reference list"""
        from .section_detector import SectionDetector
        
        sections = await SectionDetector.detect_sections(pdf_path)
        
        if "references" not in sections["sections"]:
            return []
        
        ref_text = sections["sections"]["references"]["content"]
        references = []
        
        # Split by lines and clean
        lines = [line.strip() for line in ref_text.split('\n') if line.strip()]
        
        current_ref = ""
        ref_number = 1
        
        for line in lines:
            # Check if line starts a new reference
            if (re.match(r'^\[\d+\]', line) or 
                re.match(r'^\d+\.', line) or
                re.match(r'^[A-Z][a-z]+,', line)):
                
                # Save previous reference
                if current_ref:
                    parsed_ref = CitationParser._parse_reference(current_ref, ref_number - 1)
                    if parsed_ref:
                        references.append(parsed_ref)
                
                current_ref = line
                ref_number += 1
            else:
                # Continue previous reference
                current_ref += " " + line
        
        # Save last reference
        if current_ref:
            parsed_ref = CitationParser._parse_reference(current_ref, ref_number - 1)
            if parsed_ref:
                references.append(parsed_ref)
        
        return references
    
    @staticmethod
    def _parse_reference(ref_text: str, ref_number: int) -> Optional[Dict[str, Any]]:
        """Parse a single reference"""
        ref_text = ref_text.strip()
        
        if len(ref_text) < 20:  # Too short to be valid reference
            return None
        
        # Extract basic components using simple patterns
        parsed = {
            "reference_number": ref_number,
            "raw_text": ref_text,
            "authors": [],
            "year": "",
            "title": "",
            "journal": "",
            "volume": "",
            "pages": ""
        }
        
        # Extract year
        year_match = re.search(r'\((\d{4}[a-z]?)\)', ref_text)
        if year_match:
            parsed["year"] = year_match.group(1)
        
        # Extract DOI
        doi_match = re.search(r'doi[:\s]*(10\.\d+/[^\s]+)', ref_text, re.IGNORECASE)
        if doi_match:
            parsed["doi"] = doi_match.group(1)
        
        # Extract URL
        url_match = re.search(r'https?://[^\s]+', ref_text)
        if url_match:
            parsed["url"] = url_match.group(0)
        
        # Simple author extraction (first part before year)
        if year_match:
            author_part = ref_text[:year_match.start()].strip()
            # Remove reference numbers
            author_part = re.sub(r'^\[\d+\]\s*', '', author_part)
            author_part = re.sub(r'^\d+\.\s*', '', author_part)
            parsed["authors_raw"] = author_part
        
        return parsed
    
    @staticmethod
    def _classify_citation_type(citation: str) -> str:
        """Classify the type of citation"""
        if re.match(r'\[\d+\]', citation):
            return "numbered"
        elif re.match(r'\([A-Z]', citation):
            return "author_year"
        else:
            return "other"
    
    @staticmethod
    def _detect_citation_style(citations: List[Dict[str, Any]]) -> str:
        """Detect the predominant citation style"""
        if not citations:
            return "unknown"
        
        types = [c["type"] for c in citations]
        
        if types.count("numbered") > types.count("author_year"):
            return "numbered" 
        elif types.count("author_year") > types.count("numbered"):
            return "apa_harvard"
        else:
            return "mixed"
    
    @staticmethod
    async def get_citation_summary(pdf_path: str) -> Dict[str, Any]:
        """Get summary of citations for agent understanding"""
        citation_data = await CitationParser.extract_citations(pdf_path)
        
        return {
            "total_citations": citation_data["citation_count"],
            "total_references": citation_data["reference_count"],
            "citation_style": citation_data["citation_style"],
            "has_bibliography": citation_data["reference_count"] > 0,
            "heavily_cited": citation_data["citation_count"] > 20,
            "reference_years": CitationParser._extract_reference_years(citation_data["references"])
        }
    
    @staticmethod
    def _extract_reference_years(references: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract publication years from references"""
        years = []
        for ref in references:
            if ref["year"]:
                try:
                    year = int(ref["year"][:4])  # Remove letter suffixes
                    years.append(year)
                except ValueError:
                    continue
        
        if not years:
            return {"min_year": None, "max_year": None, "year_range": 0}
        
        return {
            "min_year": min(years),
            "max_year": max(years),
            "year_range": max(years) - min(years),
            "recent_references": sum(1 for y in years if y >= 2015)
        }