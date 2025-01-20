from typing import Any

from pydantic import BaseModel
from yara import Match, StringMatch, StringMatchInstance


class YaraStringInstance(BaseModel):
    matched_length: int
    offset: int
    plaintext: str | None = None


class YaraString(BaseModel):
    identifier: str
    instances: list[YaraStringInstance] | None = None

    def add_instances(self, instances: list[StringMatchInstance]):
        self.instances = []
        for _instance in instances:
            instance = YaraStringInstance(
                matched_length=_instance.matched_length,
                offset=_instance.offset,
                plaintext=_instance.plaintext(),
            )
            self.instances.append(instance)


class YaraMatch(BaseModel):
    rule: str
    tags: list[str] | None = None
    namespace: str | None = None
    meta: dict[str, Any] | None = None
    strings: list[YaraString] | None = None

    def add_strings(self, strings: list[StringMatch]):
        self.strings = []
        for _string in strings:
            string = YaraString(
                identifier=_string.identifier
            )
            string.add_instances(_string.instances)
            self.strings.append(string)


class YaraResult(BaseModel):
    rules: str
    matches: list[YaraMatch] | None = None

    def add_matches(self, matches: list[Match]):
        self.matches = []
        for _match in matches:
            match = YaraMatch(
                rule=_match.rule,
                tags=_match.tags,
                meta=_match.meta,
                namespace=_match.namespace
            )
            match.add_strings(_match.strings)
            self.matches.append(match)

