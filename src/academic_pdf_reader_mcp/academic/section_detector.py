"""
Academic section detection for research papers
"""
import re
from typing import Dict, List, Any, Optional
from ..core.pdf_processor import PDFProcessor

class SectionDetector:
    """Detects and extracts academic paper sections"""
    
    # Common academic section patterns
    SECTION_PATTERNS = {
        "abstract": [
            r"^ABSTRACT\s*$",
            r"^Abstract\s*$", 
            r"^\d+\.\s*ABSTRACT",
            r"^\d+\.\s*Abstract"
        ],
        "introduction": [
            r"^INTRODUCTION\s*$",
            r"^Introduction\s*$",
            r"^\d+\.\s*INTRODUCTION",
            r"^\d+\.\s*Introduction",
            r"^1\.\s*Introduction"
        ],
        "methods": [
            r"^METHODS?\s*$",
            r"^Methods?\s*$",
            r"^METHODOLOGY\s*$",
            r"^Methodology\s*$",
            r"^\d+\.\s*METHODS?",
            r"^\d+\.\s*Methods?",
            r"^\d+\.\s*METHODOLOGY",
            r"^\d+\.\s*Methodology"
        ],
        "results": [
            r"^RESULTS?\s*$",
            r"^Results?\s*$",
            r"^FINDINGS\s*$",
            r"^Findings\s*$",
            r"^\d+\.\s*RESULTS?",
            r"^\d+\.\s*Results?",
            r"^\d+\.\s*FINDINGS",
            r"^\d+\.\s*Findings"
        ],
        "discussion": [
            r"^DISCUSSION\s*$",
            r"^Discussion\s*$",
            r"^\d+\.\s*DISCUSSION",
            r"^\d+\.\s*Discussion"
        ],
        "conclusion": [
            r"^CONCLUSION\s*$",
            r"^Conclusion\s*$",
            r"^CONCLUSIONS\s*$",
            r"^Conclusions\s*$",
            r"^\d+\.\s*CONCLUSION",
            r"^\d+\.\s*Conclusion",
            r"^\d+\.\s*CONCLUSIONS",
            r"^\d+\.\s*Conclusions"
        ],
        "references": [
            r"^REFERENCES\s*$",
            r"^References\s*$",
            r"^BIBLIOGRAPHY\s*$",
            r"^Bibliography\s*$",
            r"^\d+\.\s*REFERENCES",
            r"^\d+\.\s*References"
        ]
    }
    
    @staticmethod
    async def detect_sections(pdf_path: str) -> Dict[str, Any]:
        """Detect academic sections in the PDF"""
        text = await PDFProcessor.extract_raw_text(pdf_path)
        lines = text.split('\n')
        
        sections = {}
        current_section = None
        section_content = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Check if line matches any section pattern
            detected_section = SectionDetector._match_section_pattern(line)
            
            if detected_section:
                # Save previous section
                if current_section and section_content:
                    sections[current_section] = {
                        "content": '\n'.join(section_content).strip(),
                        "line_start": i - len(section_content),
                        "line_end": i - 1,
                        "word_count": len(' '.join(section_content).split())
                    }
                
                # Start new section
                current_section = detected_section
                section_content = []
            else:
                # Add to current section
                if current_section:
                    section_content.append(line)
        
        # Save last section
        if current_section and section_content:
            sections[current_section] = {
                "content": '\n'.join(section_content).strip(),
                "line_start": len(lines) - len(section_content),
                "line_end": len(lines) - 1,
                "word_count": len(' '.join(section_content).split())
            }
        
        return {
            "sections": sections,
            "sections_found": list(sections.keys()),
            "total_sections": len(sections)
        }
    
    @staticmethod
    def _match_section_pattern(line: str) -> Optional[str]:
        """Check if line matches any section pattern"""
        for section_name, patterns in SectionDetector.SECTION_PATTERNS.items():
            for pattern in patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    return section_name
        return None
    
    @staticmethod
    async def extract_abstract(pdf_path: str) -> Dict[str, Any]:
        """Extract abstract specifically"""
        sections = await SectionDetector.detect_sections(pdf_path)
        
        if "abstract" in sections["sections"]:
            abstract_data = sections["sections"]["abstract"]
            return {
                "abstract": abstract_data["content"],
                "word_count": abstract_data["word_count"],
                "found": True
            }
        
        # Fallback: look for abstract in first few paragraphs
        text = await PDFProcessor.extract_raw_text(pdf_path)
        paragraphs = text.split('\n\n')[:5]  # First 5 paragraphs
        
        for para in paragraphs:
            if len(para.split()) > 50 and len(para.split()) < 300:  # Abstract length
                if any(word in para.lower() for word in ['study', 'research', 'analysis', 'investigation']):
                    return {
                        "abstract": para.strip(),
                        "word_count": len(para.split()),
                        "found": True,
                        "method": "heuristic"
                    }
        
        return {"abstract": "", "found": False}
    
    @staticmethod
    async def extract_key_sections(pdf_path: str) -> Dict[str, str]:
        """Extract key academic sections for agent understanding"""
        sections_data = await SectionDetector.detect_sections(pdf_path)
        sections = sections_data["sections"]
        
        key_sections = {}
        
        # Priority sections for agents
        priority_sections = ["abstract", "introduction", "methods", "results", "conclusion"]
        
        for section in priority_sections:
            if section in sections:
                content = sections[section]["content"]
                # Truncate very long sections for agent consumption
                if len(content.split()) > 500:
                    words = content.split()[:500]
                    content = ' '.join(words) + "... [truncated]"
                key_sections[section] = content
        
        return key_sections
    
    @staticmethod
    async def get_section_summary(pdf_path: str) -> Dict[str, Any]:
        """Get a summary of detected sections"""
        sections_data = await SectionDetector.detect_sections(pdf_path)
        sections = sections_data["sections"]
        
        summary = {
            "has_abstract": "abstract" in sections,
            "has_introduction": "introduction" in sections,
            "has_methods": "methods" in sections,
            "has_results": "results" in sections,
            "has_discussion": "discussion" in sections,
            "has_conclusion": "conclusion" in sections,
            "has_references": "references" in sections,
            "total_sections": len(sections),
            "estimated_structure": "academic_paper" if len(sections) >= 4 else "other_document"
        }
        
        # Calculate section word counts
        section_stats = {}
        for section_name, section_data in sections.items():
            section_stats[section_name] = {
                "word_count": section_data["word_count"],
                "percentage": round(section_data["word_count"] / sum(s["word_count"] for s in sections.values()) * 100, 1)
            }
        
        summary["section_statistics"] = section_stats
        
        return summary