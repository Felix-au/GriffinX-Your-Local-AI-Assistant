import json
import re
import logging
from llama_cpp import Llama
from core.model_manager import ensure_model

class LLMEngine:
    def __init__(self, model_path=None, n_ctx=4096):
        self.logger = logging.getLogger(__name__)
        self.model_path = model_path
        self.llm = None
        self.n_ctx = n_ctx
        
    def load_model(self):
        if not self.llm:
            # Auto-download if no model exists at path
            if self.model_path and not __import__('os').path.exists(self.model_path):
                self.logger.info("Model not found at configured path, downloading Qwen 3 4B...")
                downloaded = ensure_model("llm")
                if downloaded:
                    self.model_path = downloaded

            if not self.model_path:
                downloaded = ensure_model("llm")
                if downloaded:
                    self.model_path = downloaded
                else:
                    self.logger.error("No LLM model available.")
                    return

            self.logger.info(f"Loading LLM from {self.model_path}...")
            try:
                self.llm = Llama(
                    model_path=self.model_path,
                    n_ctx=self.n_ctx,
                    n_gpu_layers=-1, 
                    verbose=False
                )
            except Exception as e:
                self.logger.error(f"Failed to load LLM: {str(e)}")
                self.llm = None

    def _extract_json(self, text):
        """Robust JSON extraction handling nested objects and code fences."""
        cleaned = re.sub(r'```(?:json)?\s*', '', text).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        depth = 0
        start = -1
        for i, ch in enumerate(cleaned):
            if ch == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0 and start != -1:
                    try:
                        return json.loads(cleaned[start:i + 1])
                    except json.JSONDecodeError:
                        start = -1
        return None
                
    def get_intent(self, system_prompt, user_input, context_memory=""):
        if not self.llm:
            self.load_model()
        if not self.llm:
            return {"error": "Model not loaded", "intent": "none"}

        # Qwen 3 uses <|im_start|>/<|im_end|> chat template
        prompt = f"<|im_start|>system\n{system_prompt}\n"
        if context_memory:
            prompt += f"Recent Context:\n{context_memory}\n"
        prompt += f"<|im_end|>\n<|im_start|>user\n{user_input}<|im_end|>\n<|im_start|>assistant\n"
        
        self.logger.info("Running intent classification inference...")
        response = self.llm(
            prompt,
            max_tokens=1024,
            stop=["<|im_start|>", "<|im_end|>", "<|endoftext|>"],
            temperature=0.1
        )
        
        output_text = response['choices'][0]['text'].strip()
        self.logger.debug(f"LLM Output: {output_text}")

        # Strip /think blocks from Qwen 3 thinking mode (handle unclosed tags if max_tokens hit)
        think_start = output_text.find('<think>')
        if think_start != -1:
            think_end = output_text.find('</think>')
            if think_end != -1:
                output_text = output_text[:think_start] + output_text[think_end + 8:]
            else:
                output_text = output_text[:think_start]
                
        output_text = output_text.strip()
        
        result = self._extract_json(output_text)
        if result and isinstance(result, dict):
            if "intent" not in result:
                result["intent"] = "general_query"
            return result
        else:
            return {"intent": "general_query", "message": output_text}
