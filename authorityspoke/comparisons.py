from __future__ import annotations

from abc import ABC
import logging
from typing import Dict, Iterator, Optional

logger = logging.getLogger(__name__)


class Comparable(ABC):
    def contradicts(
        self, other: Optional[Comparable], context: Optional[ContextRegister] = None
    ) -> bool:
        """
        Test whether ``self`` implies the absence of ``other``.

        :returns:
            ``True`` if self and other can't both be true at
            the same time. Otherwise returns ``False``.
        """

        if other is None:
            return False
        return any(
            explanation is not None
            for explanation in self.explanations_contradiction(other, context)
        )

    def implies(
        self, other: Optional[Comparable], context: Optional[ContextRegister] = None
    ) -> bool:
        """Test whether ``self`` implies ``other``."""
        if other is None:
            return True
        return any(
            register is not None
            for register in self.explanations_implication(other, context=context)
        )

    def means(
        self, other: Optional[Comparable], context: Optional[ContextRegister] = None
    ) -> bool:
        r"""
        Test whether ``self`` and ``other`` have identical meanings.

        :returns:
            whether ``other`` is another :class:`Factor`
            with the same meaning as ``self``. Not the same as an
            equality comparison with the ``==`` symbol, which simply
            converts ``self``\'s and ``other``\'s fields to tuples
            and compares them.
        """
        if other is None:
            return False
        return any(
            explanation is not None
            for explanation in self.explanations_same_meaning(other, context=context)
        )

    def explain_same_meaning(
        self, other: Comparable, context: Optional[ContextRegister] = None
    ) -> Optional[ContextRegister]:
        """Get one explanation of why self and other have the same meaning."""
        explanations = self.explanations_same_meaning(other, context=context)
        try:
            explanation = next(explanations)
        except StopIteration:
            return None
        return explanation

    def explain_contradiction(
        self, other: Comparable, context: Optional[ContextRegister] = None
    ) -> Optional[ContextRegister]:
        """Get one explanation of why self and other contradict."""
        explanations = self.explanations_contradiction(other, context=context)
        try:
            explanation = next(explanations)
        except StopIteration:
            return None
        return explanation

    def explain_implication(
        self, other: Comparable, context: Optional[ContextRegister] = None
    ) -> Optional[ContextRegister]:
        """Get one explanation of why self implies other."""
        explanations = self.explanations_implication(other, context=context)
        try:
            explanation = next(explanations)
        except StopIteration:
            return None
        return explanation

    def explanations_contradiction(
        self, other: Comparable, context: Optional[ContextRegister] = None
    ) -> Iterator[ContextRegister]:
        raise NotImplementedError

    def explanations_implication(
        self, other: Comparable, context: Optional[ContextRegister] = None
    ) -> Iterator[ContextRegister]:
        raise NotImplementedError

    def explanations_same_meaning(
        self, other: Comparable, context: Optional[ContextRegister] = None
    ) -> Iterator[ContextRegister]:
        raise NotImplementedError


class ContextRegister(Dict[Comparable, Comparable]):
    r"""
    A mapping of corresponding :class:`Factor`\s from two different contexts.

    When :class:`Factor`\s are matched in a ContextRegister, it indicates
    that their relationship can be described by a comparison function
    like :func:`means`, :meth:`Factor.implies`, or :meth:`Factor.consistent_with`\.
    """

    def __repr__(self) -> str:
        return "ContextRegister({})".format(super().__repr__())

    def __str__(self) -> str:
        item_names = [f"{str(k)} -> {str(v)}" for k, v in self.items()]
        items = ", ".join(item_names)
        return f"ContextRegister({items})"

    @property
    def prose(self) -> str:
        """Make statement matching analagous context factors of self and other."""
        similies = [
            f'{key} {"are" if key.__dict__.get("plural") is True else "is"} like {value}'
            for key, value in self.items()
        ]
        if len(similies) > 1:
            similies[-2:] = [", and ".join(similies[-2:])]
        return ", ".join(similies)

    def replace_keys(self, replacements: ContextRegister) -> ContextRegister:
        """Construct new :class:`ContextRegister` by replacing keys."""
        values = self.values()
        keys = [replacements.get(factor) or factor for factor in self.keys()]
        return ContextRegister(zip(keys, values))

    def reversed(self):
        """Swap keys for values and vice versa."""
        return ContextRegister({v: k for k, v in self.items()})

    def merged_with(
        self, incoming_mapping: ContextRegister
    ) -> Optional[ContextRegister]:
        r"""
        Create a new merged :class:`ContextRegister`\.

        :param incoming_mapping:
            an incoming mapping of :class:`Factor`\s
            from ``self`` to :class:`Factor`\s.

        :returns:
            ``None`` if the same :class:`Factor` in one mapping
            appears to match to two different :class:`Factor`\s in the other.
            Otherwise returns an updated :class:`ContextRegister` of matches.
        """
        self_mapping = ContextRegister(self.items())
        for in_key, in_value in incoming_mapping.items():

            if in_value:
                if self_mapping.get(in_key) and self_mapping.get(in_key) != in_value:
                    logger.debug(
                        f"{in_key} already in mapping with value "
                        + f"{self_mapping[in_key]}, not {in_value}"
                    )
                    return None
                self_mapping[in_key] = in_value
                if list(self_mapping.values()).count(in_value) > 1:
                    logger.debug("%s assigned to two different keys", in_value)
                    return None
        return self_mapping
