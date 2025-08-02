# app/prompt.py

import yaml

class PromptManager:
    """
    Verwaltet das Laden und die Erstellung von Prompts aus einer YAML-Vorlage.
    """
    def __init__(self, prompt_file: str):
        self.prompt_file = prompt_file
        self._template = self._load_template()

    def _load_template(self):
        """Lädt die Prompt-Vorlage aus der YAML-Datei."""
        with open(self.prompt_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return data.get("prompt_template", "")

    def create_prompt(self, interests: dict) -> str:
        """
        Erstellt den finalen Prompt, indem die Interessen in die Vorlage eingefügt werden.
        """
        active_interests = [key for key, value in interests.items() if value]
        interests_string = ", ".join(active_interests)
        return self._template.format(interests=interests_string)

