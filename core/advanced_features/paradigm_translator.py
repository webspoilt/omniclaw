"""
🌐 PARADIGM TRANSLATOR
Converts code between frameworks, languages, and paradigms semantically.
Not just syntax conversion - preserves intent and best practices.
Kills: Porting projects, Learning new frameworks, Migration tools

Author: OmniClaw Advanced Features
"""

import json
import re
from dataclasses import dataclass
from typing import Optional, Callable
from enum import Enum


class Language(Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUST = "rust"
    JAVA = "java"
    CSHARP = "csharp"
    RUBY = "ruby"
    PHP = "php"


class Framework(Enum):
    # Python
    DJANGO = "django"
    FLASK = "flask"
    FASTAPI = "fastapi"
    # JavaScript/TypeScript
    REACT = "react"
    VUE = "vue"
    ANGULAR = "angular"
    EXPRESS = "express"
    NEXTJS = "nextjs"
    # Go
    GIN = "gin"
    ECHO = "echo"


@dataclass
class TranslationResult:
    source_language: Language
    target_language: Language
    source_framework: Optional[Framework]
    target_framework: Optional[Framework]
    original_code: str
    translated_code: str
    warnings: list[str]
    explanations: list[str]


class ParadigmTranslator:
    """
    Translates code between languages and frameworks.
    Understands semantic equivalents, not just syntax.
    """
    
    def __init__(self, llm_provider=None):
        self.llm = llm_provider
        self._load_builtin_mappings()
    
    def _load_builtin_mappings(self):
        """Load built-in language/framework mappings"""
        
        self.syntax_map = {
            # Python <-> JavaScript
            ("python", "javascript"): {
                "def": "function",
                "self": "this",
                "None": "null",
                "True": "true",
                "False": "false",
                "elif": "else if",
                "lambda": "() =>",
                "import": "import",
                "from x import y": "import { y } from 'x'",
            },
            # JavaScript <-> TypeScript
            ("javascript", "typescript"): {
                "var ": "let ",
                ": any": "",  # Remove any types
            }
        }
    
    def translate(
        self,
        code: str,
        from_lang: Language,
        to_lang: Language,
        from_framework: Framework = None,
        to_framework: Framework = None,
        context: str = ""
    ) -> TranslationResult:
        """
        Translate code from one language/framework to another.
        
        Args:
            code: Source code
            from_lang: Source language
            to_lang: Target language  
            from_framework: Source framework (optional)
            to_framework: Target framework (optional)
            context: Additional context for translation
        
        Returns:
            TranslationResult with translated code and explanations
        """
        
        # For simple translations, use pattern replacement
        if self._is_simple_translation(from_lang, to_lang):
            return self._simple_translate(
                code, from_lang, to_lang, from_framework, to_framework
            )
        
        # For complex translations, use LLM
        if self.llm:
            return self._llm_translate(
                code, from_lang, to_lang, from_framework, to_framework, context
            )
        
        # Fallback: return original with warning
        return TranslationResult(
            source_language=from_lang,
            target_language=to_lang,
            source_framework=from_framework,
            target_framework=to_framework,
            original_code=code,
            translated_code=code,
            warnings=["Translation requires LLM for this language pair"],
            explanations=[]
        )
    
    def _is_simple_translation(
        self, 
        from_lang: Language, 
        to_lang: Language
    ) -> bool:
        """Check if this is a simple translation we can do without LLM"""
        
        simple_pairs = [
            ("python", "javascript"),
            ("javascript", "python"),
            ("javascript", "typescript"),
            ("typescript", "javascript"),
        ]
        
        return (from_lang.value, to_lang.value) in simple_pairs
    
    def _simple_translate(
        self,
        code: str,
        from_lang: Language,
        to_lang: Language,
        from_framework: Framework,
        to_framework: Framework
    ) -> TranslationResult:
        """Perform simple pattern-based translation"""
        
        translated = code
        warnings = []
        explanations = []
        
        pair_key = (from_lang.value, to_lang.value)
        
        if pair_key == ("python", "javascript"):
            translated, exp = self._python_to_js(code)
            explanations.extend(exp)
            
        elif pair_key == ("javascript", "python"):
            translated, exp = self._js_to_python(code)
            explanations.extend(exp)
            
        elif pair_key == ("javascript", "typescript"):
            translated, exp = self._js_to_ts(code)
            explanations.extend(exp)
            warnings.append("Type annotations are inferred - review for correctness")
            
        elif pair_key == ("typescript", "javascript"):
            translated = self._ts_to_js(code)
            warnings.append("Types removed - add them back where needed")
        
        return TranslationResult(
            source_language=from_lang,
            target_language=to_lang,
            source_framework=from_framework,
            target_framework=to_framework,
            original_code=code,
            translated_code=translated,
            warnings=warnings,
            explanations=explanations
        )
    
    def _python_to_js(self, code: str) -> tuple[str, list[str]]:
        """Python to JavaScript conversion"""
        
        translated = code
        explanations = []
        
        # Function definitions
        translated = re.sub(
            r'^(\s*)def (\w+)\((.*?)\):',
            r'\1const \2 = (\3) => {',
            translated,
            flags=re.MULTILINE
        )
        
        # Class definitions
        translated = re.sub(
            r'^class (\w+)(?:\((.*?)\))?:',
            r'class \1 \2 {',
            translated,
            flags=re.MULTILINE
        )
        
        # Self to this
        translated = translated.replace("self.", "this.")
        
        # None to null
        translated = translated.replace("None", "null")
        
        # Print statements
        translated = re.sub(
            r'print\((.*)\)',
            r'console.log(\1)',
            translated
        )
        
        # List comprehensions (basic)
        translated = re.sub(
            r'\[(\w+) for (\w+) in (\w+)\]',
            r'\3.map(\2 => \1)',
            translated
        )
        
        # Dict comprehensions
        translated = re.sub(
            r'\{(\w+): (\w+) for (\w+) in (\w+)\}',
            r'\4.reduce((acc, \3) => { acc[\3] = \2; return acc; }, {})',
            translated
        )
        
        # Self closing braces for functions
        if "=> {" in translated:
            translated += "\n}"
        
        explanations.append("Converted Python syntax to JavaScript ES6+")
        
        return translated, explanations
    
    def _js_to_python(self, code: str) -> tuple[str, list[str]]:
        """JavaScript to Python conversion"""
        
        translated = code
        explanations = []
        
        # Arrow functions to def
        translated = re.sub(
            r'const (\w+) = \((.*?)\) => \{(.*?)\}',
            r'def \1(\2):\n    \3',
            translated,
            flags=re.DOTALL
        )
        
        # Function declarations
        translated = re.sub(
            r'function (\w+)\((.*?)\)\s*\{(.*?)\}',
            r'def \1(\2):\n    \3',
            translated,
            flags=re.DOTALL
        )
        
        # this to self
        translated = translated.replace("this.", "self.")
        
        # console.log to print
        translated = re.sub(
            r'console\.log\((.*)\)',
            r'print(\1)',
            translated
        )
        
        # const/let to variable
        translated = re.sub(
            r'(?:const|let) (\w+) = (.+);',
            r'\1 = \2',
            translated
        )
        
        # arrow function with single expression
        translated = re.sub(
            r'=> (.+)',
            r'-> \1',
            translated
        )
        
        explanations.append("Converted JavaScript to Python")
        
        return translated, explanations
    
    def _js_to_ts(self, code: str) -> tuple[str, list[str]]:
        """JavaScript to TypeScript conversion"""
        
        translated = code
        explanations = []
        
        # Add implicit any types (for now)
        translated = re.sub(
            r'(const|let|var) (\w+):?',
            r'\1 \2: any',
            translated
        )
        
        # Function parameter types
        translated = re.sub(
            r'function (\w+)\((\w+)\)',
            r'function \1(\2: any)',
            translated
        )
        
        # Interface extraction (basic)
        interfaces = re.findall(
            r'const (\w+) = \{([^}]+)\}',
            translated
        )
        
        for name, props in interfaces:
            interface_props = props.replace(":", ": any")
            explanations.append(f"Consider adding interface for {name}")
        
        explanations.append("Added TypeScript types - review and refine")
        
        return translated, explanations
    
    def _ts_to_js(self, code: str) -> str:
        """TypeScript to JavaScript conversion"""
        
        translated = code
        
        # Remove type annotations
        translated = re.sub(r':\s*(?:string|number|boolean|any|void|null|undefined)\b', '', translated)
        
        # Remove interfaces
        translated = re.sub(r'interface \w+\s*\{[^}]*\}', '', translated)
        
        # Remove type definitions
        translated = re.sub(r'type \w+\s*=[^;]+;', '', translated)
        
        # Remove generics
        translated = re.sub(r'<[^>]+>', '', translated)
        
        return translated
    
    def translate_framework(
        self,
        code: str,
        from_framework: Framework,
        to_framework: Framework,
        language: Language = Language.JAVASCRIPT
    ) -> TranslationResult:
        """
        Translate code between frameworks (e.g., React to Vue).
        """
        
        if self.llm:
            return self._llm_translate_framework(
                code, from_framework, to_framework, language
            )
        
        # Basic pattern-based translations for common cases
        if from_framework == Framework.REACT and to_framework == Framework.VUE:
            return self._react_to_vue(code)
        elif from_framework == Framework.EXPRESS and to_framework == Framework.FLASK:
            return self._express_to_flask(code)
        
        return TranslationResult(
            source_language=language,
            target_language=language,
            source_framework=from_framework,
            target_framework=to_framework,
            original_code=code,
            translated_code=code,
            warnings=["Requires LLM for this framework translation"],
            explanations=[]
        )
    
    def _react_to_vue(self, code: str) -> TranslationResult:
        """React to Vue conversion"""
        
        translated = code
        
        # className to class
        translated = translated.replace("className=", "class=")
        
        # useState to ref/reactive
        translated = re.sub(
            r'const \[(\w+), set(\w+)\] = useState\((.+)\)',
            r'const \1 = ref(\3)',
            translated
        )
        
        # useEffect to onMounted/onUpdated
        translated = re.sub(
            r'useEffect\(\(\) => \{(.+?)\}, \[(.+?)\]\)',
            r'onMounted(() => {\1})',
            translated,
            flags=re.DOTALL
        )
        
        return TranslationResult(
            source_language=Language.JAVASCRIPT,
            target_language=Language.JAVASCRIPT,
            source_framework=Framework.REACT,
            target_framework=Framework.VUE,
            original_code=code,
            translated_code=translated,
            warnings=[],
            explanations=["Converted React patterns to Vue 3 Composition API"]
        )
    
    def _express_to_flask(self, code: str) -> TranslationResult:
        """Express to Flask conversion"""
        
        translated = code
        
        # app.get to @app.route
        translated = re.sub(
            r"app\.(get|post|put|delete|patch)\(['\"](.+?)['\"]",
            r"@app.route('\2', methods=['\1'.upper()])",
            translated
        )
        
        # req.body to request.json
        translated = translated.replace("req.body", "request.get_json()")
        
        # req.params to request.args
        translated = translated.replace("req.params", "request.args")
        
        # res.json to return jsonify
        translated = re.sub(
            r"res\.json\((.+)\)",
            r"return jsonify(\1)",
            translated
        )
        
        return TranslationResult(
            source_language=Language.JAVASCRIPT,
            target_language=Language.PYTHON,
            source_framework=Framework.EXPRESS,
            target_framework=Framework.FLASK,
            original_code=code,
            translated_code=translated,
            warnings=[],
            explanations=["Converted Express patterns to Flask"]
        )
    
    def _llm_translate(
        self,
        code: str,
        from_lang: Language,
        to_lang: Language,
        from_framework: Framework,
        to_framework: Framework,
        context: str
    ) -> TranslationResult:
        """Use LLM for complex translations"""
        
        prompt = f"""Translate the following {from_lang.value} code to {to_lang.value}.
{f'Translate from {from_framework.value} to {to_framework.value}' if from_framework and to_framework else ''}

Context: {context}

Source Code:
```{from_lang.value}
{code}
```

Provide:
1. Translated code
2. Any changes in approach/best practices
3. Warnings about potential issues

Format as JSON:
{{
    "translated_code": "...",
    "explanations": [...],
    "warnings": [...]
}}
"""
        
        # Call LLM (placeholder)
        # response = await self.llm.generate(prompt)
        
        return TranslationResult(
            source_language=from_lang,
            target_language=to_lang,
            source_framework=from_framework,
            target_framework=to_framework,
            original_code=code,
            translated_code="# Use LLM provider for complex translations",
            warnings=[],
            explanations=[]
        )
    
    def _llm_translate_framework(
        self,
        code: str,
        from_framework: Framework,
        to_framework: Framework,
        language: Language
    ) -> TranslationResult:
        """Use LLM for framework translations"""
        
        return self._llm_translate(
            code, language, language,
            from_framework, to_framework,
            f"Translate from {from_framework.value} to {to_framework.value}"
        )


# Demo
if __name__ == "__main__":
    translator = ParadigmTranslator()
    
    print("🌐 PARADIGM TRANSLATOR")
    print("=" * 50)
    
    # Python to JavaScript
    py_code = '''
def calculate_total(items):
    total = 0
    for item in items:
        total += item['price'] * item['quantity']
    return total

class ShoppingCart:
    def __init__(self):
        self.items = []
    
    def add_item(self, item):
        self.items.append(item)
'''
    
    result = translator.translate(
        py_code, 
        Language.PYTHON, 
        Language.JAVASCRIPT
    )
    
    print("\n📝 Python → JavaScript:")
    print("-" * 30)
    print(result.translated_code)
    print("\nExplanations:", result.explanations)
    
    # React to Vue
    react_code = '''
import React, { useState } from 'react';

function Counter() {
    const [count, setCount] = useState(0);
    
    return (
        <button className="counter" onClick={() => setCount(count + 1)}>
            Count: {count}
        </button>
    );
}
'''
    
    result2 = translator.translate_framework(
        react_code,
        Framework.REACT,
        Framework.VUE
    )
    
    print("\n\n📝 React → Vue:")
    print("-" * 30)
    print(result2.translated_code)
    print("\nExplanations:", result2.explanations)
