r"""
:class:`Holding`\s describe :class:`.Opinion`\s` attitudes toward :class:`.Rule`\s.

:class:`Holding`\s are text passages within :class:`.Opinion`\s
in which :class:`.Court` posits, or rejects, the validity of a
:class:`.Rule` within the :class:`.Court`\'s :class:`.Jurisdiction`,
or the :class:`.Court` asserts that the validity of the :class:`.Rule`
should be considered undecided.
"""

from __future__ import annotations

from itertools import chain
import operator
from typing import Any, Callable, Dict, Iterator, List
from typing import Optional, Sequence, Tuple, TypeVar, Union

from dataclasses import dataclass

from authorityspoke.comparisons import Comparable, ContextRegister
from authorityspoke.explanations import Explanation
from authorityspoke.factors import Factor, new_context_helper, contradicts
from authorityspoke.groups import ComparableGroup
from authorityspoke.formatting import indented, wrapped
from authorityspoke.procedures import Procedure
from authorityspoke.rules import Rule


@dataclass(frozen=True)
class Holding(Factor):
    """
    An :class:`.Opinion`\'s announcement that it posits or rejects a legal :class:`.Rule`.

    Note that if an opinion merely says the court is not deciding whether
    a :class:`.Rule` is valid, there is no :class:`Holding`, and no
    :class:`.Rule` object should be created. Deciding not to decide
    a :class:`Rule`\'s validity is not the same thing as deciding
    that the :class:`.Rule` is undecided.

    :param rule:
        a statement of a legal doctrine about a :class:`.Procedure` for litigation.

    :param rule_valid:
        ``True`` means the :class:`.Rule` is asserted to be valid (or
        useable by a court in litigation). ``False`` means it's asserted
        to be invalid.

    :param decided:
        ``False`` means that it should be deemed undecided
        whether the :class:`.Rule` is valid, and thus can have the
        effect of overruling prior holdings finding the :class:`.Rule`
        to be either valid or invalid. Seemingly, ``decided=False``
        should render the ``rule_valid`` flag irrelevant.

    :param exclusive:
        if True, the stated rule is asserted to be the only way to establish
        the output that is the output of the rule.

    :param generic:
        if True, indicates that the specific attributes of this holding
        are irrelevant in the context of a different holding that is
        referencing this holding.
    """

    rule: Rule
    rule_valid: bool = True
    decided: bool = True
    exclusive: bool = False
    generic: bool = False

    def __post_init__(self):
        if self.exclusive:
            if not self.rule_valid:
                raise NotImplementedError(
                    "The ability to state that it is not 'valid' to assert "
                    + "that a Rule is the 'exclusive' way to reach an output is "
                    + "not implemented, so 'rule_valid' cannot be False while "
                    + "'exclusive' is True. Try expressing this in another way "
                    + "without the 'exclusive' keyword."
                )
            if not self.decided:
                raise NotImplementedError(
                    "The ability to state that it is not 'decided' whether "
                    + "a Rule is the 'exclusive' way to reach an output is "
                    + "not implemented. Try expressing this in another way "
                    + "without the 'exclusive' keyword."
                )

    @property
    def procedure(self):
        """Get Procedure from Rule."""
        return self.rule.procedure

    @property
    def despite(self):
        """Get Factors that specifically don't preclude application of the Holding."""
        return self.rule.procedure.despite

    @property
    def inputs(self):
        """Get inputs from Procedure."""
        return self.rule.procedure.inputs

    @property
    def outputs(self):
        """Get outputs from Procedure."""
        return self.rule.procedure.outputs

    @property
    def enactments(self):
        """Get Enactments required to apply the Holding."""
        return self.rule.enactments

    @property
    def enactments_despite(self):
        """Get Enactments that specifically don't preclude application of the Holding."""
        return self.rule.enactments_despite

    @property
    def context_factors(self) -> Tuple:
        r"""
        Call :class:`Procedure`\'s :meth:`~Procedure.context_factors` method.

        :returns:
            context_factors from ``self``'s :class:`Procedure`
        """
        return self.rule.procedure.context_factors

    @property
    def generic_factors(self) -> List[Factor]:
        r"""
        Get :class:`.Factor`\s that can be replaced without changing ``self``\s meaning.

        :returns:
            generic :class:`.Factor`\s from ``self``'s :class:`Procedure`
        """
        return self.rule.generic_factors

    @property
    def mandatory(self) -> bool:
        """Whether court "MUST" apply holding when it is applicable."""
        return self.rule.mandatory

    @property
    def universal(self) -> bool:
        """Whether holding is applicable in "ALL" cases where inputs are present."""
        return self.rule.universal

    def add_if_not_exclusive(self, other: Holding) -> Optional[Holding]:
        """Show how first Holding triggers second, assumed not to be "exclusive" way to reach result."""
        new_rule = self.rule + other.rule
        if new_rule is None:
            return None
        return self.evolve({"rule": self.rule + other.rule})

    def add_holding(self, other: Holding) -> Optional[Holding]:
        """Show how first Holding triggers the second."""
        if not (self.decided and other.decided):
            raise NotImplementedError(
                "Adding is not implemented for Holdings that assert a Rule is not decided."
            )
        if not (self.rule_valid and other.rule_valid):
            raise NotImplementedError(
                "Adding is not implemented for Holdings that assert a Rule is not valid."
            )
        for self_holding in self.nonexclusive_holdings:
            for other_holding in other.nonexclusive_holdings:
                added = self_holding.add_if_not_exclusive(other_holding)
                if added is not None:
                    return added
        return None

    def __add__(self, other: Factor) -> Optional[Union[Rule, Holding]]:
        if isinstance(other, Rule):
            other = Holding(rule=other)
        if isinstance(other, Holding):
            return self.add_holding(other)
        return self.evolve({"rule": self.rule + other})

    def _explanations_contradiction_of_holding(
        self, other: Holding, context: ContextRegister
    ) -> Iterator[Explanation]:
        for self_holding in self.nonexclusive_holdings:
            for other_holding in other.nonexclusive_holdings:
                for register in self_holding._contradicts_if_not_exclusive(
                    other_holding, context=context
                ):
                    yield Explanation(
                        matches=[(self_holding, other_holding)],
                        context=register,
                        operation=contradicts,
                    )

    def explanations_contradiction(
        self, other: Factor, context: ContextRegister = None
    ) -> Iterator[Explanation]:
        r"""
        Find context matches that would result in a contradiction with other.

        Works by testing whether ``self`` would imply ``other`` if
        ``other`` had an opposite value for ``rule_valid``.

        This method takes three main paths depending on
        whether the holdings ``self`` and ``other`` assert that
        rules are decided or undecided.

        A ``decided`` :class:`Rule` can never contradict
        a previous statement that any :class:`Rule` was undecided.

        If rule A implies rule B, then a holding that B is undecided
        contradicts a prior :class:`Rule` deciding that
        rule A is valid or invalid.

        :param other:
            The :class:`.Factor` to be compared to self. Unlike with
            :meth:`~Holding.contradicts`\, this method cannot be called
            with an :class:`.Opinion` for `other`.

        :returns:
            a generator yielding :class:`.ContextRegister`\s that cause a
            contradiction.
        """

        if context is None:
            context = ContextRegister()
        if isinstance(other, Procedure):
            other = Rule(procedure=other)
        if isinstance(other, Rule):
            other = Holding(rule=other)
        if isinstance(other, self.__class__):
            yield from self._explanations_contradiction_of_holding(other, context)
        elif isinstance(other, Factor):
            yield from []  # no possible contradiction
        elif hasattr(other, "explanations_contradiction"):
            if context:
                context = context.reversed()
            yield from other.explanations_contradiction(self, context=context)
        else:
            raise TypeError(
                f"'Contradicts' test not implemented for types "
                f"{self.__class__} and {other.__class__}."
            )

    def _contradicts_if_not_exclusive(
        self, other: Holding, context: ContextRegister = None
    ) -> Iterator[ContextRegister]:
        if context is None:
            context = ContextRegister()
        if isinstance(other, Holding) and other.decided:
            if self.decided:
                yield from self._explanations_implies_if_not_exclusive(
                    other.negated(), context=context
                )
            else:
                yield from chain(
                    other._implies_if_decided(self),
                    other._implies_if_decided(self.negated()),
                )

    def _explanations_implies_if_not_exclusive(
        self, other: Factor, context: ContextRegister = None
    ) -> Iterator[ContextRegister]:
        if not isinstance(other, self.__class__):
            raise TypeError

        if self.decided and other.decided:
            yield from self._implies_if_decided(other, context)

        # A holding being undecided doesn't seem to imply that
        # any other holding is undecided, except itself and the
        # negation of itself.

        # It doesn't seem that any holding being undecided implies
        # that any holding is decided, or vice versa.

        elif not self.decided and not other.decided:
            yield from chain(
                self.explanations_same_meaning(other, context),
                self.explanations_same_meaning(other.negated(), context),
            )

    def __ge__(self, other: Optional[Factor]) -> bool:
        return self.implies(other)

    def implies(
        self, other: Optional[Comparable], context: ContextRegister = None
    ) -> bool:
        r"""
        Test for implication.

        See :meth:`.Procedure.implies_all_to_all`
        and :meth:`.Procedure.implies_all_to_some` for
        explanations of how ``inputs``, ``outputs``,
        and ``despite`` :class:`.Factor`\s affect implication.

        :param other:
            A :class:`Holding` to compare to self, or a :class:`.Rule` to
            convert into such a :class:`Holding` and then compare

        :returns:
            whether ``self`` implies ``other``
        """
        if other is None:
            return True
        if isinstance(other, (Rule, Procedure)):
            other = Holding(rule=other)
        if not isinstance(other, self.__class__):
            if hasattr(other, "implied_by"):
                if context:
                    context = context.reversed()
                return other.implied_by(self, context=context)
            return False
        return any(
            explanation is not None
            for explanation in self.explanations_implication(other, context)
        )

    def explanations_implication(
        self, other: Holding, context: Optional[ContextRegister] = None
    ) -> Iterator[ContextRegister]:
        """Yield contexts that would cause self and other to have same meaning."""
        if self.exclusive is other.exclusive is False:
            yield from self._explanations_implies_if_not_exclusive(
                other, context=context
            )
        else:
            yield from self.nonexclusive_holdings.explanations_implication(
                other.nonexclusive_holdings, context=context
            )

    def implied_by(
        self, other: Factor, context: Optional[ContextRegister] = None
    ) -> bool:
        r"""
        Test if other implies self.

        This function is for handling implication checks for classes
        that don't know the structure of the :class:`Holding` class,
        such as :class:`.Fact` and :class:`.Rule`\.
        """
        if context:
            context = context.reversed()
        if isinstance(other, Rule):
            return Holding(rule=other).implies(self, context=context)
        return other.implies(self, context=context)

    def _implies_if_decided(
        self, other: Holding, context: Optional[ContextRegister] = None
    ) -> Iterator[ContextRegister]:
        r"""
        Test if ``self`` implies ``other`` if they're both decided.

        This is a partial version of the
        :meth:`Holding.__ge__` implication function.

        :returns:
            whether ``self`` implies ``other``, assuming that
            ``self.decided == other.decided == True`` and that
            ``self`` and ``other`` are both :class:`Holding`\s,
            although ``rule_valid`` can be ``False``.
        """

        if self.rule_valid and other.rule_valid:
            yield from self.rule.explanations_implication(other.rule, context)

        elif not self.rule_valid and not other.rule_valid:
            yield from other.rule.explanations_implication(self.rule, context)

        # Looking for implication where self.rule_valid != other.rule_valid
        # is equivalent to looking for contradiction.

        # If decided rule A contradicts B, then B also contradicts A

        else:
            yield from self.rule.explanations_contradiction(other.rule, context)

    def __len__(self):
        r"""
        Count generic :class:`.Factor`\s needed as context for this :class:`Holding`.

        :returns:
            the number of generic :class:`.Factor`\s needed for
            self's :class:`.Procedure`.
        """

        return len(self.rule.procedure)

    @property
    def inferred_from_exclusive(self) -> List[Holding]:
        r"""
        Yield :class:`Holding`\s that can be inferred from the "exclusive" flag.

        The generator will be empty if `self.exclusive` is False.
        """
        if self.exclusive:
            return [
                Holding(rule=modified_rule)
                for modified_rule in self.rule.get_contrapositives()
            ]
        return []

    def evolve(self, changes: Union[str, Sequence[str], Dict[str, Any]]) -> Holding:
        """
        Make new object with attributes from ``self.__dict__``, replacing attributes as specified.

        :param changes:
            a :class:`dict` where the keys are names of attributes
            of self, and the values are new values for those attributes, or
            else an attribute name or :class:`list` of names that need to
            have their values replaced with their boolean opposite.

        :returns:
            a new object initialized with attributes from
            ``self.__dict__``, except that any attributes named as keys in the
            changes parameter are replaced by the corresponding value.
        """
        changes = self._make_dict_to_evolve(changes)
        changes = self._evolve_attribute(changes, "rule")
        new_values = self._evolve_from_dict(changes)
        return self.__class__(**new_values)

    def explanations_same_meaning(
        self, other: Factor, context: Optional[ContextRegister] = None
    ) -> Iterator[ContextRegister]:
        """Yield contexts that would cause self and other to have same meaning."""
        if (
            isinstance(other, self.__class__)
            and self.rule_valid == other.rule_valid
            and self.decided == other.decided
        ):
            yield from self.rule.explanations_same_meaning(other.rule, context)

    def negated(self):
        """Get new copy of ``self`` with an opposite value for ``rule_valid``."""
        return self.evolve({"rule_valid": not self.rule_valid, "exclusive": False})

    @new_context_helper
    def new_context(self, changes: ContextRegister) -> Factor:
        """
        Create new :class:`Holding`, replacing keys of ``changes`` with values.

        :returns:
            a version of ``self`` with the new context.
        """
        return Holding(
            rule=self.rule.new_context(changes),
            rule_valid=self.rule_valid,
            decided=self.decided,
        )

    @property
    def nonexclusive_holdings(self) -> HoldingGroup:
        r"""Yield all :class:`.Holding`\s with `exclusive is False` implied by self."""
        if not self.exclusive:
            return HoldingGroup([self])
        holdings = [self.evolve("exclusive")] + self.inferred_from_exclusive
        return HoldingGroup(holdings)

    def _union_if_not_exclusive(
        self, other: Holding, context: ContextRegister
    ) -> Optional[Holding]:
        if self.decided is other.decided is False:
            if self.rule.implies(other.rule, context=context):
                return other
            if other.rule.implies(self.rule, context=context.reversed()):
                return self
            return None

        if not self.decided or not other.decided:
            return None
        if self.rule_valid != other.rule_valid:
            return None

        if self.rule_valid is False:
            # If a Rule with input A present is not valid
            # and a Rule with input A absent is also not valid
            # then a version of the Rule with input A
            # omitted is also not valid.
            raise NotImplementedError(
                "The union operation is not yet implemented for Holdings "
                "that assert a Rule is not valid."
            )

        new_rule = self.rule.union(other.rule, context=context)
        if not new_rule:
            return None
        return self.evolve({"rule": new_rule, "exclusive": False})

    def _union_with_holding(
        self, other: Holding, context: ContextRegister
    ) -> Optional[Holding]:
        for self_holding in self.nonexclusive_holdings:
            for other_holding in other.nonexclusive_holdings:
                united = self_holding._union_if_not_exclusive(
                    other_holding, context=context
                )
                if united is not None:
                    return united
        return None

    def union(
        self, other: Union[Rule, Holding], context: Optional[ContextRegister] = None
    ) -> Optional[Holding]:
        """Infer a Holding from all inputs and outputs of self and other, in context."""
        context = context or ContextRegister()
        if isinstance(other, Rule):
            other = Holding(rule=other)
        if not isinstance(other, Holding):
            raise TypeError
        return self._union_with_holding(other, context=context)

    def __or__(self, other: Union[Rule, Holding]) -> Optional[Holding]:
        """Infer a Holding from all inputs and outputs of self and other."""
        return self.union(other)

    def own_attributes(self) -> Dict[str, Any]:
        """
        Return attributes of ``self`` that aren't inherited from another class.

        Used for getting parameters to pass to :meth:`~Holding.__init__`
        when generating a new object.
        """
        attrs = self.__dict__.copy()
        for group in Procedure.context_factor_names:
            attrs.pop(group, None)
        for group in Rule.enactment_attr_names:
            attrs.pop(group, None)
        attrs.pop("procedure", None)
        return attrs

    def __str__(self):
        action = (
            "consider UNDECIDED"
            if not self.decided
            else ("ACCEPT" if self.rule_valid else "REJECT")
        )
        exclusive = (
            (
                f" that the EXCLUSIVE way to reach "
                f"{self.rule.outputs[0].short_string} is"
            )
            if self.exclusive
            else ""
        )
        rule_text = indented(str(self.rule))
        text = wrapped(f"the Holding to {action}{exclusive}") + f"\n{rule_text}"
        return text


H = TypeVar("H", bound="Holding")


class HoldingGroup(ComparableGroup[H]):
    def __new__(cls, value: Sequence = ()):
        if isinstance(value, Holding):
            value = (value,)
        return tuple.__new__(HoldingGroup, value)

    def explanations_implication(
        self, other: Comparable, context: Optional[ContextRegister] = None
    ) -> Iterator[Explanation]:
        if isinstance(other, Rule):
            other = Holding(rule=other)
        if isinstance(other, Holding):
            yield from self.verbose_comparison(
                operation=operator.ge, still_need_matches=[other]
            )
        elif isinstance(other, self.__class__):
            yield from self.verbose_comparison(
                operation=operator.ge, still_need_matches=list(other)
            )

    def explanations_implies_holding(
        self, other: Holding, context: Optional[ContextRegister] = None
    ) -> Iterator[Explanation]:
        for self_holding in self:
            if self_holding.implies(other):
                yield Explanation(matches=[(self_holding, other)])

    def verbose_comparison(
        self,
        operation: Callable,
        still_need_matches: Sequence[Factor],
        explanation: Explanation = None,
    ) -> Iterator[Explanation]:
        r"""
        Find one way for two unordered sets of :class:`.Factor`\s to satisfy a comparison.

        All of the elements of `other` need to fit the comparison. The elements of
        `self` don't all need to be used.

        Only returns one answer, to prevent expensive fruitless searching.

        :param context:
            a mapping of :class:`.Factor`\s that have already been matched
            to each other in the recursive search for a complete group of
            matches. Usually starts empty when the method is first called.

        :param still_need_matches:
            :class:`.Factor`\s that need to satisfy the comparison
            :attr:`comparison` with some :class:`.Factor` of :attr:`available`
            for the relation to hold, and have not yet been matched.

        :param explanation:
            an :class:`.Explanation` showing which :class:`.Factor`\s listed in the
            FactorGroups were matched to each other, and also including a
            :class:`.ContextRegister`\.

        :yields:
            context registers showing how each :class:`.Factor` in
            ``need_matches`` can have the relation ``comparison``
            with some :class:`.Factor` in ``available_for_matching``,
            with matching context.
        """
        still_need_matches = list(still_need_matches)

        if explanation is None:
            explanation = Explanation(matches=[], context=None, operation=operation)

        if not still_need_matches:
            yield explanation
        else:
            other_holding = still_need_matches.pop()
            for self_holding in self:
                if operation(self_holding, other_holding):
                    new_explanation = explanation.add_match(
                        (self_holding, other_holding)
                    )
                    next_step = iter(
                        self.verbose_comparison(
                            still_need_matches=still_need_matches,
                            operation=operation,
                            explanation=new_explanation,
                        )
                    )
                    yield next(next_step)
