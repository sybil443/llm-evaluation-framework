from dataclasses import dataclass, field


@dataclass
class TrieNode:
    children: dict[str, "TrieNode"] = field(default_factory=dict)
    is_terminal: bool = False


class TagTrie:
    """Trie for hierarchical failure-tag prefix lookup."""

    def __init__(self) -> None:
        self.root = TrieNode()

    def insert(self, tag: str) -> None:
        normalized_tag = self._normalize_tag(tag)

        if not normalized_tag:
            raise ValueError("Tag must be a non-empty string.")

        node = self.root

        for character in normalized_tag:
            node = node.children.setdefault(character, TrieNode())

        node.is_terminal = True

    def contains(self, tag: str) -> bool:
        normalized_tag = self._normalize_tag(tag)

        if not normalized_tag:
            return False

        node = self._find_node(normalized_tag)
        return node is not None and node.is_terminal

    def search_prefix(self, prefix: str) -> list[str]:
        normalized_prefix = self._normalize_prefix(prefix)

        node = self._find_node(normalized_prefix)
        if node is None:
            return []

        results: list[str] = []
        self._collect_tags(
            node=node,
            current=normalized_prefix,
            results=results,
        )

        return sorted(results)

    def _find_node(self, text: str) -> TrieNode | None:
        node = self.root

        for character in text:
            if character not in node.children:
                return None
            node = node.children[character]

        return node

    def _collect_tags(
        self,
        *,
        node: TrieNode,
        current: str,
        results: list[str],
    ) -> None:
        if node.is_terminal:
            results.append(current)

        for character, child in node.children.items():
            self._collect_tags(
                node=child,
                current=current + character,
                results=results,
            )

    @staticmethod
    def _normalize_tag(tag: str) -> str:
        if not isinstance(tag, str):
            raise TypeError("Tag must be a string.")

        return tag.strip().strip("/")

    @staticmethod
    def _normalize_prefix(prefix: str) -> str:
        if not isinstance(prefix, str):
            raise TypeError("Prefix must be a string.")

        return prefix.strip().lstrip("/")