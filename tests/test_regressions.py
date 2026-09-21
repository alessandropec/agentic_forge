"""Offline regressions for the bugs listed in the recovery handoff."""

import asyncio
import importlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from langchain_core.runnables import RunnableLambda

from agentic_forge import forge
from agentic_forge.core.refiner import Refiner
from agentic_forge.dataset.forged import ForgedItemDataset
from agentic_forge.data_runner.forged import ForgedDataRunner
from agentic_forge.llm.forged.provider import ForgedLlmProvider
from agentic_forge.llm.materials import LlmProviderMaterial
from agentic_forge.structured_output.forge.response_schema import ResponseSchemaForge
from agentic_forge.structured_output.material import ResponseSchemaMaterial

provider_module = importlib.import_module("agentic_forge.llm.forged.provider")
runner_module = importlib.import_module("agentic_forge.data_runner.forged")


class RegressionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_dataset_save_reload_synthetic_and_custom_keys(self):
        for field in (None, "record_id"):
            with self.subTest(field=field):
                dataset = ForgedItemDataset([{"text": "hello"}], keys=["first"])
                dataset.save(self.root / "saved.json", key_field=field)
                reloaded = forge(self.root / "saved.yaml")
                self.assertEqual(reloaded.get_key(0), "first")
                self.assertEqual(reloaded[0][field or "id"], "first")
                self.assertEqual(dataset._items, [{"text": "hello"}])

    def test_dataset_save_preserves_numeric_ids_and_preprocessed_keys(self):
        path = self.write("source.json", '[{"id": 17, "text": "hello"}]')
        dataset = ForgedItemDataset.from_json(path, key_field="id")
        dataset.save(self.root / "saved.json")
        self.assertEqual(forge(self.root / "saved.yaml")[0]["id"], 17)
        dataset.preprocess_and_save(
            self.root / "processed.json", keep_original=False,
            input_templates={"text": "{text}"},
        )
        self.assertEqual(forge(self.root / "processed.yaml").get_key(0), "17")

    def test_runner_skips_numeric_ids_without_progress_counter(self):
        class NullProgress:
            def update(self, *args): pass
            def set_postfix(self, **kwargs): pass
            def close(self): pass

        dataset = ForgedItemDataset([{"id": 1}, {"id": 2}, {"id": 3}])
        runner = ForgedDataRunner(dataset, default_skip_keys=["1"])
        output = self.root / "results.json"
        with patch.object(runner_module, "tqdm", return_value=NullProgress()):
            results = runner.run(
                lambda *, item: {"seen": item["id"]}, skip_keys=["2"],
                batch_size=2, save_every=1, save_path=str(output),
            )
        self.assertEqual(results, [{"seen": 3, "id": 3}])
        self.assertEqual(json.loads(output.read_text()), results)
        with self.assertRaisesRegex(ValueError, "batch_size"):
            runner.run(lambda **kw: {}, batch_size=0)

    def test_schema_descriptions_and_required_fields(self):
        fields = [
            {"name": "text", "type": "str", "description": "Body"},
            {"name": "kind", "type": "enum", "choices": ["a", "b"], "description": "Kind", "required": False},
            {"name": "child", "type": "obj", "description": "Child", "fields": [
                {"name": "count", "type": "int", "description": "Count"}]},
            {"name": "tags", "type": "list", "description": "Tags", "items":
                {"name": "tag", "type": "str", "description": "Tag"}},
        ]
        model = ResponseSchemaForge().forge_from_material(
            ResponseSchemaMaterial(name="Answer", fields=fields)
        ).schema
        schema = model.model_json_schema()
        for field in fields:
            self.assertEqual(schema["properties"][field["name"]]["description"], field["description"])
        child = next(iter(schema["$defs"].values()))
        self.assertEqual(child["properties"]["count"]["description"], "Count")
        self.assertEqual(schema["properties"]["tags"]["items"]["description"], "Tag")
        self.assertNotIn("kind", schema["required"])
        self.assertIsNone(model(text="hi", child={"count": 1}, tags=[]).kind)

    def test_yaml_direct_and_indirect_cycles(self):
        for target in ("a.yaml", "nested/b.yaml"):
            with self.subTest(target=target):
                path = self.write("a.yaml", f"ref: {target}\n")
                self.write("nested/b.yaml", "ref: ../a.yaml\n")
                with self.assertRaisesRegex(ValueError, "Cyclic YAML reference:.*a.yaml"):
                    Refiner.from_yaml(path)

    def test_yaml_repeated_refs_and_relative_overrides_are_valid(self):
        self.write("nested/base.yaml", "value: original\n")
        self.write("override.yaml", "value: overridden\n")
        path = self.write("root.yaml", """first:
  ref: nested/base.yaml
  child:
    ref: override.yaml
second:
  ref: nested/base.yaml
""")
        result = Refiner.from_yaml(path)
        self.assertEqual(result["first"]["child"]["value"], "overridden")
        self.assertEqual(result["second"]["value"], "original")

    def test_referenced_images_dynamic_partial_invoke_and_pipeline(self):
        self.write("nested/image.png", "nested fixture")
        self.write("image.png", "wrong root fixture")
        self.write("nested/message.yaml", "role: human\nimages: ['{image}']\n")
        path = self.write("prompt.yaml", "forge: chat_prompt\nname: vision\nmessages:\n  - ref: nested/message.yaml\n")
        prompt = forge(path)
        expected = "data:image/png;base64,bmVzdGVkIGZpeHR1cmU="
        payloads = [
            prompt.format_messages(image="image.png"),
            prompt.invoke({"image": "image.png"}).to_messages(),
            prompt.partial(image="image.png").invoke({}).to_messages(),
            (prompt | RunnableLambda(lambda value: value)).invoke({"image": "image.png"}),
            asyncio.run(prompt.ainvoke({"image": "image.png"})).to_messages(),
        ]
        for messages in payloads:
            self.assertEqual(messages[0].content[0]["image_url"]["url"], expected)
            compact = prompt.compact_for_display(messages)
            self.assertNotIn("base64,", compact[0].content[0]["image_url"]["url"])
            self.assertIn("from_path=", compact[0].content[0]["image_url"]["url"])
            self.assertEqual(messages[0].content[0]["image_url"]["url"], expected)
        url = "https://example.invalid/image.png"
        self.assertEqual(prompt.format_messages(image=url)[0].content[0]["image_url"]["url"], url)

    def test_provider_credentials_and_keep_alive_do_not_change_environment(self):
        for provider_type, env_name, key_name in (
            ("openai", "OPENAI_API_KEY", "openai_api_key"),
            ("openrouter", "OPENROUTER_API_KEY", "openrouter_api_key"),
        ):
            with self.subTest(provider=provider_type), patch.dict(os.environ, {env_name: "fake-env"}):
                providers = []
                for number in (1, 2):
                    path = self.write(f"fixture-{number}.yaml", f"{key_name}: fake-{number}\n")
                    providers.append(ForgedLlmProvider(LlmProviderMaterial(
                        type=provider_type, api_key_file=str(path), models={
                            "chat": {"type": "chat", "name": "test"},
                            "embed": {"type": "embedding", "name": "test"},
                        },
                    )))
                with patch.object(provider_module, "ChatOpenAI", side_effect=lambda **kw: kw), patch.object(
                    provider_module, "OpenAIEmbeddings", side_effect=lambda **kw: kw
                ):
                    for index in (0, 1, 0):
                        for model in ("chat", "embed"):
                            self.assertEqual(providers[index].get_model(model)["openai_api_key"], f"fake-{index + 1}")
                self.assertEqual(os.environ[env_name], "fake-env")
        with patch.dict(os.environ, {"OLLAMA_KEEP_ALIVE": "old"}):
            provider = ForgedLlmProvider(LlmProviderMaterial(type="ollama", keep_alive="5m", models={}))
            self.assertEqual(os.environ["OLLAMA_KEEP_ALIVE"], "old")

    def test_embedding_option_precedence_all_providers(self):
        for provider_type in ("openai", "openrouter", "ollama"):
            with self.subTest(provider=provider_type):
                provider = ForgedLlmProvider(LlmProviderMaterial(
                    type=provider_type, base_url="http://localhost:12345", keep_alive="5m",
                    models={"m": {"type": "embedding", "name": "test", "extra_options": {"model": "extra"}}},
                ))
                constructor = "OllamaEmbeddings" if provider_type == "ollama" else "OpenAIEmbeddings"
                with patch.object(provider_module, constructor, side_effect=lambda **kw: kw):
                    self.assertEqual(provider.get_model("m")["model"], "extra")
                    result = provider.get_model("m", model="explicit", base_url="http://localhost:54321")
                    self.assertEqual(result["model"], "explicit")
                    self.assertEqual(result["base_url"], "http://localhost:54321")
                    if provider_type == "ollama":
                        self.assertEqual(result["keep_alive"], "5m")


if __name__ == "__main__":
    unittest.main()
