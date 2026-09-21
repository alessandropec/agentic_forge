"""Offline regression checks for the reusable changes recovered from COITO."""

import importlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from langchain_core.runnables import RunnableLambda

from agentic_forge import forge
from agentic_forge.core.refiner import Refiner
from agentic_forge.llm.forge import LlmManagerForge
from agentic_forge.llm.materials import LlmManagerMaterial, LlmProviderMaterial
from agentic_forge.llm.forged.provider import ForgedLlmProvider

provider_module = importlib.import_module("agentic_forge.llm.forged.provider")


class BackportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_missing_keys_do_not_block_catalog(self):
        material = LlmManagerMaterial(providers={"cloud": {
            "type": "openai", "api_key_file": str(self.root / "missing.yaml"),
            "models": {"vision": {"type": "chat", "name": "test", "supports_vision": True}},
        }})
        manager = LlmManagerForge().forge_from_material(material)
        self.assertTrue(manager.get_model_info("cloud:vision")["supports_vision"])
        self.assertEqual(len(manager.list_models()), 1)
        with self.assertRaisesRegex(FileNotFoundError, "API key file not found"):
            manager.get_model("cloud:vision")

    def test_inline_provider_inherits_directory(self):
        path = self.write("manager.yaml", """forge: llm_manager
providers:
  cloud:
    type: openai
    api_key_file: keys.yaml
    models: {}
""")
        manager = forge(path)
        self.assertEqual(Path(manager.providers["cloud"].material.base_dir), self.root)

    def test_referenced_provider_keeps_own_directory(self):
        self.write("nested/provider.yaml", "type: openai\napi_key_file: keys.yaml\nmodels: {}\n")
        path = self.write("manager.yaml", "forge: llm_manager\nproviders:\n  cloud:\n    ref: nested/provider.yaml\n")
        manager = forge(path)
        self.assertEqual(Path(manager.providers["cloud"].material.base_dir), self.root / "nested")

    def test_inline_dataset_inherits_directory(self):
        self.write("items.json", '[{"id": "a", "text": "hello"}]')
        path = self.write("runner.yaml", """forge: data_runner
dataset:
  path: items.json
  format: list
  key_field: id
""")
        self.assertEqual(forge(path).dataset[0]["text"], "hello")

    def test_local_images_in_format_messages_and_pipeline(self):
        self.write("image.png", "test fixture")
        path = self.write("prompt.yaml", """forge: chat_prompt
name: vision
messages:
  - role: human
    images: [image.png]
""")
        prompt = forge(path)
        messages = prompt.format_messages()
        url = messages[0].content[0]["image_url"]["url"]
        self.assertTrue(url.startswith("data:image/png;base64,"))
        pipeline_messages = (prompt | RunnableLambda(lambda x: x)).invoke({})
        self.assertEqual(pipeline_messages[0].content[0]["image_url"]["url"], url)
        compact = prompt.compact_for_display(messages)
        self.assertIn("<image:", compact[0].content[0]["image_url"]["url"])
        self.assertEqual(messages[0].content[0]["image_url"]["url"], url)

    def test_utf8_in_root_and_reference(self):
        self.write("message.yaml", "role: system\ncontent: Città, perché? 日本語\n")
        path = self.write("prompt.yaml", "name: città\nmessages:\n  - ref: message.yaml\n")
        data = Refiner.from_yaml(path)
        self.assertEqual(data["name"], "città")
        self.assertEqual(data["messages"][0]["content"], "Città, perché? 日本語")

    def test_chat_option_precedence_for_every_provider(self):
        for provider_type in ("openai", "openrouter", "ollama"):
            with self.subTest(provider=provider_type):
                provider = ForgedLlmProvider(LlmProviderMaterial(
                    type=provider_type, base_url="http://localhost:12345", models={"m": {
                        "type": "chat", "name": "test", "temperature": 0.6,
                        "top_p": 0.8, "max_tokens": 123,
                        "extra_options": {"temperature": 0.4, "timeout": 7},
                    }},
                ))
                constructor = "ChatOllama" if provider_type == "ollama" else "ChatOpenAI"
                with patch.object(provider_module, constructor, side_effect=lambda **kw: kw):
                    self.assertEqual(provider.get_model("m")["temperature"], 0.4)
                    options = provider.get_model("m", temperature=0.2, top_p=0.3, timeout=9)
                    self.assertEqual(options["temperature"], 0.2)
                    self.assertEqual(options["top_p"], 0.3)
                    self.assertEqual(options["timeout"], 9)
                    self.assertEqual(options["base_url"], "http://localhost:12345")
                    token_key = "num_predict" if provider_type == "ollama" else "max_tokens"
                    self.assertEqual(options[token_key], 123)

    def test_real_ollama_constructor_without_network(self):
        provider = ForgedLlmProvider(LlmProviderMaterial(type="ollama", models={"m": {
            "type": "chat", "name": "test", "temperature": 0.6, "max_tokens": 42,
        }}))
        model = provider.get_model("m", temperature=0.2)
        self.assertEqual(model.temperature, 0.2)
        self.assertEqual(model.num_predict, 42)

    def test_structured_model_propagates_inline_directories(self):
        self.write("image.png", "test fixture")
        path = self.write("structured.yaml", """forge: structured_model
model_selector: local:chat
llm_manager:
  providers:
    local:
      type: ollama
      models:
        chat:
          type: chat
          name: test
prompt_schema_pairs:
  - name: describe
    prompt:
      name: vision
      messages:
        - role: human
          images: [image.png]
    schema:
      name: Answer
      fields:
        - name: text
          type: str
          description: Image description
""")
        directories = []

        class FakeModel:
            def with_structured_output(self, schema):
                return RunnableLambda(lambda messages: messages)

        def fake_get_model(provider, model_key, **kwargs):
            directories.append(provider.material.base_dir)
            return FakeModel()

        with patch.object(ForgedLlmProvider, "get_model", fake_get_model):
            result = forge(path).invoke("describe", {})
        self.assertEqual(Path(directories[0]), self.root)
        self.assertTrue(result[0].content[0]["image_url"]["url"].startswith("data:"))


if __name__ == "__main__":
    unittest.main()
