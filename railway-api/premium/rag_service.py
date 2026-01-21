
import os
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Path to the knowledge base (relative to this script or absolute)
# We assume it's stored in .agent/knowledge/thumbnail_rag_context.md
# But for runtime, we might need to load it from a known location.
# For now, we point to the absolute path where we copied it.
KNOWLEDGE_PATH = "/Users/yvesromano/AiRAG/.agent/knowledge/thumbnail_rag_context.md"

class ThumbnailRAGService:
    def __init__(self, knowledge_path: str = KNOWLEDGE_PATH):
        self.knowledge_path = knowledge_path
        self.content = ""
        self.sections = {}
        self._load_knowledge()

    def _load_knowledge(self):
        """Load and parse the markdown knowledge base."""
        if not os.path.exists(self.knowledge_path):
            logger.error(f"RAG Knowledge Base not found at {self.knowledge_path}")
            return

        try:
            with open(self.knowledge_path, 'r', encoding='utf-8') as f:
                self.content = f.read()
                
            # Parse sections roughly by Headers
            # We want to index "NICHE-SPECIFIC GUIDELINES" specifically
            self._parse_sections()
            logger.info("Loaded Thumbnail RAG Knowledge Base.")
        except Exception as e:
            logger.error(f"Failed to load RAG knowledge: {e}")

    def _parse_sections(self):
        """Simple parsing of the markdown into sections."""
        # This is a naive parser based on the known structure
        lines = self.content.split('\n')
        current_header = "Intro"
        buffer = []
        
        for line in lines:
            if line.startswith('## '):
                # New main section
                self.sections[current_header] = '\n'.join(buffer)
                current_header = line.strip().replace('## ', '')
                buffer = []
            elif line.startswith('### '):
                # Sub-section (we might want to index these for Niches)
                self.sections[current_header] = '\n'.join(buffer) # Save previous
                # Compound key for subsections? 
                # For now, let's just append to buffer, OR detecting niche headers
                if "NICHE-SPECIFIC" in current_header:
                     # If we are inside Niche Guidelines, treat ### as specific niches
                     sub_header = line.strip().replace('### ', '')
                     self.sections[f"Niche:{sub_header}"] = "" # Mark start
                     current_header = f"Niche:{sub_header}"
                     buffer = []
                else:
                    buffer.append(line)
            else:
                buffer.append(line)
                
        # Flush last
        self.sections[current_header] = '\n'.join(buffer)

    def get_guidelines(self, niche: str) -> str:
        """
        Retrieve relevant guidelines for a specific niche.
        Returns a prompt-ready string containing:
        1. Core High-Level Principles (Universal)
        2. Niche-Specific Guidelines (if found)
        3. Critical Mistakes to Avoid
        """
        response_parts = []
        
        # 1. Universal Principles (Core Framework)
        core = self.sections.get("CORE FRAMEWORK: WHAT MAKES THUMBNAILS EFFECTIVE", "")
        if core:
            response_parts.append("### CORE PRINCIPLES\n" + core[:1000] + "...") # Limit length?
            
        # 2. Niche Specifics
        # Map input niche to known keys
        # Known keys like "Niche:Gaming Content", "Niche:Educational Content"
        target_key = None
        for key in self.sections:
            if key.startswith("Niche:") and niche.lower() in key.lower().replace("content", ""):
                target_key = key
                break
        
        if target_key:
            response_parts.append(f"\n### {target_key.upper()} GUIDELINES\n" + self.sections[target_key])
        else:
            # Fallback?
            response_parts.append(f"\n### GENERAL BEST PRACTICES\n(No specific guidelines found for {niche}, using general rules)")
            
        # 3. Trends (2025)
        trends = self.sections.get("2025 TRENDS & FUTURE DIRECTIONS", "")
        if trends:
             response_parts.append("\n### 2025 TRENDS\n" + trends[:1500])

        return "\n".join(response_parts)

if __name__ == "__main__":
    service = ThumbnailRAGService()
    print("--- GAMING GUIDELINES TEST ---")
    output = service.get_guidelines("Gaming")
    print(output[:2000])
    print("\n--- END TEST ---")
