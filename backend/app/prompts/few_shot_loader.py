"""
Few-Shot Examples Loader
Loads real email examples for Few-Shot prompting
"""
import json
import random
from pathlib import Path
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class FewShotExamplesDB:
    """
    Loads and manages few-shot examples from parsed_examples.json
    Provides methods to retrieve relevant examples for different components
    """
    
    def __init__(self, examples_file: Optional[Path] = None):
        if examples_file is None:
            # Default path
            base_dir = Path(__file__).parent.parent.parent
            examples_file = base_dir / "data" / "parsed_examples.json"
        
        self.examples_file = examples_file
        self.examples = self._load_examples()
        
    def _load_examples(self) -> List[Dict]:
        """Load examples from JSON file"""
        if not self.examples_file.exists():
            logger.warning(f"Examples file not found: {self.examples_file}")
            return []
        
        try:
            with open(self.examples_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Loaded {len(data)} email examples from {self.examples_file}")
            return data
        except Exception as e:
            logger.error(f"Error loading examples: {str(e)}")
            return []
    
    def get_cta_examples(self, count: int = 10, randomize: bool = True) -> List[str]:
        """
        Get CTA examples for Few-Shot prompting
        All CTAs are normalized to UPPERCASE to match brand style
        
        Args:
            count: Number of examples to return
            randomize: If True, return random selection. If False, return first N.
        
        Returns:
            List of CTA text strings (all uppercase)
        """
        all_ctas = []
        for email in self.examples:
            for cta in email.get('ctas', []):
                text = cta.get('text', '').strip()
                # Normalize to uppercase for consistency
                text_upper = text.upper()
                if text_upper and text_upper not in all_ctas:  # Avoid duplicates
                    all_ctas.append(text_upper)
        
        if randomize:
            return random.sample(all_ctas, min(count, len(all_ctas)))
        else:
            return all_ctas[:count]
    
    def get_subject_examples(self, count: int = 10, randomize: bool = True) -> List[str]:
        """
        Get Subject line examples for Few-Shot prompting
        
        Args:
            count: Number of examples to return
            randomize: If True, return random selection
        
        Returns:
            List of subject line strings (cleaned of "Fwd:" and "TEST:" prefixes)
        """
        subjects = []
        for email in self.examples:
            subject = email.get('subject', '').strip()
            # Clean common prefixes
            subject = subject.replace('Fwd: ', '').replace('TEST: ', '').replace('TEST:', '')
            if subject and subject not in subjects:
                subjects.append(subject)
        
        if randomize:
            return random.sample(subjects, min(count, len(subjects)))
        else:
            return subjects[:count]
    
    def get_body_examples(self, count: int = 5, randomize: bool = True) -> List[str]:
        """
        Get Body section examples for Few-Shot prompting
        
        Args:
            count: Number of examples to return
            randomize: If True, return random selection
        
        Returns:
            List of body section text strings
        """
        all_sections = []
        for email in self.examples:
            for section in email.get('body_sections', []):
                if section and len(section) > 50:  # Only meaningful sections
                    all_sections.append(section)
        
        if randomize:
            return random.sample(all_sections, min(count, len(all_sections)))
        else:
            return all_sections[:count]
    
    def format_examples_for_prompt(
        self, 
        component_type: str, 
        count: int = 8,
        include_context: bool = False
    ) -> str:
        """
        Format examples for inclusion in AI prompt
        
        Args:
            component_type: Type of component ('cta', 'subject', 'body', 'preheader')
            count: Number of examples to include
            include_context: If True, include brief context about each example
        
        Returns:
            Formatted string ready for prompt injection
        """
        if component_type.lower() in ['cta', 'call_to_action']:
            examples = self.get_cta_examples(count=count, randomize=True)
            title = "CALL-TO-ACTION (CTA) EXAMPLES from successful campaigns:"
            items = "\n".join([f"  - \"{ex}\"" for ex in examples])
            
        elif component_type.lower() in ['subject', 'subject_line']:
            examples = self.get_subject_examples(count=count, randomize=True)
            title = "SUBJECT LINE EXAMPLES from successful campaigns:"
            items = "\n".join([f"  - \"{ex}\"" for ex in examples])
            
        elif component_type.lower() in ['body', 'body_section']:
            examples = self.get_body_examples(count=min(count, 3), randomize=True)  # Body is longer
            title = "BODY SECTION EXAMPLES from successful campaigns:"
            items = "\n".join([f"  - \"{ex[:150]}...\"" for ex in examples])
            
        elif component_type.lower() == 'preheader':
            # Manually curated pre-header examples from successful LuisaViaRoma campaigns
            # Source: Copy from your Google Sheet or email inbox previews
            examples = [
                "Minimal designs to elevate every corner of your home.",
                "Looks designed to make every moment unforgettable.",
                "Our Fall 2025 price drop is here.",
                "Your playbook for Fashion Week dressing.",
                "More looks. More style. Now waiting for you.",
                "The latest ready-to-wear edits for every wardrobe.",
                "Modern menswear essentials.",
                "Discover our exclusive resale service.",
                "Curated looks that define the moment.",
                "From frumpy fashion to green bags.",
                "Our curated selection of lower impact clothing and homewares.",
                "The curated selection of men's fashion.",
                "Lightweight layers and cool sneakers await.",
                "Dress to reinvent, not to fit in.",
                "Unveil the style that defines excellence.",
                "A curated selection, now at new prices.",
                "Quiet confidence, Italian ease.",
                "Discover the latest in skincare and more.",
                "More looks. More style. Now waiting for you."
            ]
            title = "PRE-HEADER EXAMPLES from successful campaigns:"
            items = "\n".join([f"  - \"{ex}\"" for ex in random.sample(examples, min(count, len(examples)))])
        
        else:
            return ""
        
        # Build the formatted string with component-specific instructions
        additional_instruction = ""
        if component_type.lower() in ['cta', 'call_to_action']:
            additional_instruction = "\n⚠️ IMPORTANT FOR CTAs: Always use UPPERCASE letters (e.g., 'SHOP NOW', 'DISCOVER MORE')."
        
        formatted = f"""
{title}
{items}
{additional_instruction}

IMPORTANT: Generate something UNIQUE and DIFFERENT from these examples. 
Use them for style inspiration, but create fresh, original content that fits the specific brief.
Do NOT copy these examples verbatim - they are references only.
"""
        return formatted
    
    def get_statistics(self) -> Dict:
        """Get statistics about loaded examples"""
        total_ctas = sum(len(email.get('ctas', [])) for email in self.examples)
        unique_ctas = len(self.get_cta_examples(count=1000, randomize=False))
        total_subjects = len([e for e in self.examples if e.get('subject')])
        
        return {
            'total_emails': len(self.examples),
            'total_ctas': total_ctas,
            'unique_ctas': unique_ctas,
            'total_subjects': total_subjects,
            'avg_ctas_per_email': total_ctas / len(self.examples) if self.examples else 0
        }


# Global instance (lazy loaded)
_few_shot_db = None

def get_few_shot_db() -> FewShotExamplesDB:
    """Get or create the global Few-Shot examples database"""
    global _few_shot_db
    if _few_shot_db is None:
        _few_shot_db = FewShotExamplesDB()
        stats = _few_shot_db.get_statistics()
        logger.info(f"Few-Shot DB loaded: {stats}")
    return _few_shot_db

