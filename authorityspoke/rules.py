"""
Statements of legal doctrines.

:class:`.Court`/s may posit them as holdings, and they
may describe procedural moves available in litigation.
"""

from __future__ import annotations

from itertools import chain
from typing import Any, ClassVar, Dict, Iterable, Iterator
from typing import List, Optional, Sequence, Tuple, Union

from dataclasses import dataclass

from authorityspoke.enactments import Enactment, consolidate_enactments
from authorityspoke.factors import Factor, ContextRegister
from authorityspoke.procedures import Procedure


@dataclass(frozen=True)
class Rule(Factor):
    r"""
    A statement of a legal doctrine about a :class:`.Procedure` for litigation.

    May decide some aspect of current litigation, and also potentially
    may be cided and reused by future courts. When :class:`Rule`\s appear as
    judicial holdings they are often hypothetical and don't necessarily
    imply that the court accepts the :class:`.Fact` assertions or other
    :class:`.Factor`\s that make up the inputs or outputs of the
    :class:`.Procedure` mentioned in the :class:`Rule`.

    :param procedure:
        a :class:`.Procedure` containing the inputs, and despite
        :class:`.Factor`\s and resulting outputs when this rule
        is triggered.

    :param enactments:
        the :class:`.Enactment`\s cited as authority for
        invoking the ``procedure``.

    :param enactments_despite:
        the :class:`.Enactment`\s specifically cited as failing
        to preclude application of the ``procedure``.

    :param mandatory:
        whether the ``procedure`` is mandatory for the
        court to apply whenever the :class:`.Rule` is properly invoked.
        ``False`` means that the ``procedure`` is "discretionary".

    :param universal:
        ``True`` if the ``procedure`` is applicable whenever
        its inputs are present. ``False`` means that the ``procedure`` is
        applicable in "some" situation where the inputs are present.

    :param generic:
        whether the :class:`Rule` is being mentioned in a generic
        context. e.g., if the :class:`Rule` is being mentioned in
        an :class:`.Argument` object merely as an example of the
        kind of :class:`Rule` that might be mentioned in such an
        :class:`.Argument`.

    :param name:
        an identifier used to retrieve this :class:`Rule` when
        needed for the composition of another :class:`.Factor`
        object.
    """

    procedure: Procedure = Procedure()
    enactments: Iterable[Enactment] = ()
    enactments_despite: Iterable[Enactment] = ()
    mandatory: bool = False
    universal: bool = False
    generic: bool = False
    name: Optional[str] = None
    outputs: Iterable[Factor] = ()
    inputs: Iterable[Factor] = ()
    despite: Iterable[Factor] = ()

    context_factor_names: ClassVar = ("procedure",)
    enactment_attr_names: ClassVar = ("enactments", "enactments_despite")

    def __post_init__(self):
        for attr in self.enactment_attr_names:
            value = self.__dict__[attr]
            if isinstance(value, Enactment):
                object.__setattr__(self, attr, self._wrap_with_tuple(value))

        if self.procedure is None:
            if self.outputs is None:
                raise ValueError(
                    "To construct a Rule you must specify either a Procedure "
                    + "or output/input/despite Factors for use in constructing "
                    + "a Procedure (including at least one output)."
                )
            object.__setattr__(
                self,
                "procedure",
                Procedure(
                    outputs=self.outputs, inputs=self.inputs, despite=self.despite
                ),
            )
        else:
            if not self.outputs == self.inputs == self.despite == None:
                new_procedure = Procedure(
                    outputs=self.outputs or self.procedure.outputs,
                    inputs=self.inputs or self.procedure.inputs,
                    despite=self.despite or self.procedure.despite,
                )
                object.__setattr__(self, "procedure", new_procedure)
        object.__setattr__(self, "outputs", self.procedure.outputs)
        object.__setattr__(self, "inputs", self.procedure.inputs)
        object.__setattr__(self, "despite", self.procedure.despite)

    def __add__(self, other) -> Optional[Rule]:
        r"""
        Create new :class:`Rule` if ``self`` can satisfy the :attr:`inputs` of ``other``.

        If both ``self`` and ``other`` have False for :attr:`universal`,
        then returns ``None``. Otherwise:

        If the union of the :attr:`inputs` and :attr:`outputs` of ``self``
        would trigger ``other``, then return a new version of ``self``
        with the output :class:`.Factor`\s of ``other`` as well as the
        outputs of ``self``.

        The new ``universal`` and ``mandatory`` values are the
        lesser of the old values for each.

        Don't test whether ``self`` could be triggered by the outputs
        of other. Let user do ``other + self`` for that.

        :param other:
            another :class:`Rule` to try to add to ``self``

        :returns:
            a combined :class:`Rule` that extends the procedural
            move made in ``self``, if possible. Otherwise ``None``.
        """
        if not isinstance(other, Rule):
            if isinstance(other, Factor):
                return self.add_factor(other)
            if isinstance(other, Enactment):
                return self.add_enactment(other)
            raise TypeError
        if self.universal is False and other.universal is False:
            return None

        if not other.needs_subset_of_enactments(self):
            return None

        new_procedure = self.procedure + other.procedure
        if new_procedure is not None:
            return self.evolve(
                {
                    "procedure": new_procedure,
                    "universal": min(self.universal, other.universal),
                    "mandatory": min(self.mandatory, other.mandatory),
                }
            )
        return None

    def get_contrapositives(self) -> Iterator[Rule]:
        r"""
        Make contrapositive forms of this :class:`Rule`.

        Used when converting from JSON input containing the entry
        ``"exclusive": True``, which means the specified :class:`~Rule.inputs``
        are the only way to reach the specified output. When that happens,
        it can be inferred that in the absence of any of the inputs, the output
        must also be absent. (Multiple :class:`~Rule.outputs` are not allowed
        when the ``exclusive`` flag is ``True``.) So, this generator will
        yield one new :class:`Rule` for each input.

        :returns:
            iterator yielding :class:`Rule`\s.
        """

        if len(self.outputs) != 1:
            raise ValueError(
                "The 'exclusive' attribute is not allowed for Rules "
                + "with more than one 'output' Factor. If the set of Factors "
                + "in 'inputs' is really the only way to reach any of the "
                + "'outputs', consider making a separate 'exclusive' entry "
                + "for each output."
            )
        if self.outputs[0].absent:
            raise ValueError(
                "The 'exclusive' attribute is not allowed for Rules "
                + "with an 'absent' 'output' Factor. This would indicate "
                + "that the output can or must be present in every litigation "
                + "unless specified inputs are present, which is unlikely."
            )
        if not self.inputs:
            raise ValueError(
                "The 'exclusive' attribute is not allowed for Rules "
                + "with no 'input' Factors."
            )

        for input_factor in self.inputs:
            yield self.evolve(
                {
                    "mandatory": not self.mandatory,
                    "universal": not self.universal,
                    "inputs": [input_factor.evolve("absent")],
                    "outputs": [self.outputs[0].evolve({"absent": True})],
                }
            )

    @property
    def context_factors(self) -> Tuple:
        """
        Call :class:`Procedure`\'s :meth:`~Procedure.context_factors` method.

        :returns:
            context_factors from ``self``'s :class:`Procedure`
        """
        return self.procedure.context_factors

    @property
    def generic_factors(self) -> List[Optional[Factor]]:
        r"""
        Get :class:`.Factor`\s that can be replaced without changing ``self``\s meaning.

        :returns:
            generic :class:`.Factor`\s from ``self``'s :class:`Procedure`
        """
        if self.generic:
            return [self]
        return self.procedure.generic_factors

    def add_enactment(self, incoming: Enactment, role: str = "enactments") -> Rule:
        """
        Make new version of ``self`` with an :class:`.Enactment` added.

        :param incoming:
            the new :class:`.Enactment` to be added to enactments or
            enactments_despite

        :param role:
            specifies whether the new :class:`.Enactment` should be added
            to enactments or enactments_despite

        :returns:
            a new version of ``self`` with the specified change
        """
        if role not in self.enactment_attr_names:
            raise ValueError(f"'role' must be one of {self.enactment_attr_names}")

        if not isinstance(incoming, Enactment):
            raise TypeError

        return self.evolve({role: list(self.__dict__[role]) + [incoming]})

    def add_factor(self, incoming: Factor, role: str = "inputs") -> Rule:
        """
        Make new version of ``self`` with an added input, output, or despite :class:`.Factor`.

        :param incoming:
            the new :class:`.Factor` to be added to input, output, or despite

        :param role:
            specifies whether the new :class:`.Factor` should be added to input, output, or despite

        :returns:
            a new version of ``self`` with the specified change
        """
        return self.evolve({"procedure": self.procedure.add_factor(incoming, role)})

    def contradicts(self, other, context: Optional[ContextRegister] = None) -> bool:
        """
        Test if ``self`` contradicts ``other``.

        :returns:
            whether ``self`` contradicts ``other``, if each is posited by a
            :class:`.Holding` with :attr:`~Holding.rule_valid``
            and :attr:`~Holding.decided`
        """
        if not isinstance(other, self.__class__):
            raise TypeError()

        if not self.mandatory and not other.mandatory:
            return False

        if not self.universal and not other.universal:
            return False

        return any(
            register is not None
            for register in self.explain_contradiction(other, context)
        )

    def explain_contradiction(
        self, other, context: Optional[ContextRegister] = None
    ) -> Iterator[ContextRegister]:
        if context is None:
            context = ContextRegister()

        self_to_other = self.procedure.explain_contradiction_some_to_all(
            other.procedure, context
        )
        other_to_self = (
            register.reversed
            for register in other.procedure.explain_contradiction_some_to_all(
                self.procedure, context.reversed
            )
        )

        if other.universal and not self.universal:
            yield from self_to_other

        if self.universal and not other.universal:
            yield from other_to_self

        # This last option is for the ALL contradicts ALL case
        # (regardless of MAY or MUST).
        # It could use more tests.

        yield from chain(self_to_other, other_to_self)

    def needs_subset_of_enactments(self, other) -> bool:
        r"""
        Test whether ``self``\'s :class:`.Enactment` support is a subset of ``other``\'s.

        A :class:`Rule` makes a more powerful statement if it relies on
        fewer :class:`.Enactment`\s (or applies despite more :class:`.Enactment`\s).

        So this method must return ``True`` for ``self`` to imply ``other``.
        """

        if not all(
            any(other_e >= e for other_e in other.enactments) for e in self.enactments
        ):
            return False

        if not all(
            any(e >= other_d for e in self.enactments + self.enactments_despite)
            for other_d in other.enactments_despite
        ):
            return False
        return True

    def explain_implication(
        self, other, context: Optional[ContextRegister] = None
    ) -> Iterator[ContextRegister]:
        if (
            self.needs_subset_of_enactments(other)
            and self.mandatory >= other.mandatory
            and self.universal >= other.universal
        ):

            if self.universal > other.universal:
                yield from self.procedure.explain_implication_all_to_some(
                    other.procedure, context
                )

            elif other.universal:
                yield from self.procedure.explain_implication_all_to_all(
                    other.procedure, context
                )

            else:
                yield from self.procedure.explain_implication(other.procedure, context)

    def implies(self, other, context: Optional[ContextRegister] = None) -> bool:
        r"""
        Test if ``self`` implies ``other`` if posited in valid and decided :class:`.Holding`\s.

        If ``self`` relies for support on some :class:`.Enactment` text
        that ``other`` doesn't, then ``self`` doesn't imply ``other``.

        Also, if ``other`` specifies that it applies notwithstanding
        some :class:`.Enactment` not mentioned by ``self``, then
        ``self`` doesn't imply ``other``.

        This will be called as part of the
        :meth:`Holding.__ge__` implication function.

        :returns:
            whether ``self`` implies ``other``, assuming that
            both are :class:`Rule`/s, and
            ``rule_valid`` and ``decided`` are ``True`` for both of them.
        """

        return any(self.explain_implication(other, context))

    def __ge__(self, other: Factor) -> bool:
        return self.implies(other)

    def __len__(self):
        r"""
        Count generic :class:`.Factor`\s needed as context for this :class:`Rule`.

        :returns:
            the number of generic :class:`.Factor`\s needed for
            self's :class:`.Procedure`.
        """

        return len(self.procedure)

    def has_all_same_enactments(self, other: Rule) -> bool:
        r"""
        Test if ``self`` has :class:`.Enactment`\s with same meanings as ``other``\'s.

        :param other:
            another :class:`Rule` to compare to ``self``.

        :returns:
            whether the :meth:`~.Enactment.means` test passes for all :class:`.Enactment`\s
        """
        for enactment_group in self.enactment_attr_names:
            if not all(
                any(other_e.means(self_e) for self_e in self.__dict__[enactment_group])
                for other_e in other.__dict__[enactment_group]
            ):
                return False
        return True

    def means(self, other: Rule) -> bool:
        """
        Test whether ``other`` has the same meaning as ``self``.

        :returns:
            whether ``other`` is a :class:`Rule` with the
            same meaning as ``self``.
        """
        if not self.__class__ == other.__class__:
            return False

        if not self.procedure.means(other.procedure):
            return False

        if not self.has_all_same_enactments(other):
            return False
        if not other.has_all_same_enactments(self):
            return False

        return self.mandatory == other.mandatory and self.universal == other.universal

    def __or__(self, other: Rule) -> Optional[Rule]:
        r"""
        Create new :class:`Rule` showing combined effect of all inputs of ``self`` and ``other``.

        This operation is destructive in the sense that the new :class:`Rule` may not
        contain all the information that was available in ``self`` and ``other``.

        This seems to work differently when one Rule
        implies the other. That could mean there is a
        union to return even when both Rules are SOME
        rules. Or it could mean an ALL rule should be
        returned even though ``implied`` is SOME, because
        implied contributes no information that wasn't
        already in ``greater``.

        :param other: a :class:`Rule` to be combined with ``self``.

        :returns:
            a :class:`Rule` indicating the combined effect of the ``input`` and ``despite``
            :class:`.Factor`\s of ``self`` and ``other``
        """

        if other is None:
            return self

        if not isinstance(other, Rule):
            raise TypeError

        new_procedure = self.procedure | other.procedure
        if new_procedure is None:
            return None

        enactments = consolidate_enactments(
            list(self.enactments) + list(other.enactments)
        )
        enactments_despite = consolidate_enactments(
            list(self.enactments_despite) + list(other.enactments_despite)
        )

        if self.procedure.implies_all_to_all(
            other.procedure
        ) or other.procedure.implies_all_to_all(self.procedure):
            return Rule(
                procedure=new_procedure,
                enactments=enactments,
                enactments_despite=enactments_despite,
                mandatory=max(self.mandatory, other.mandatory),
                universal=max(self.universal, other.universal),
            )

        if self.universal == other.universal == False:
            return None

        return Rule(
            procedure=new_procedure,
            enactments=enactments,
            enactments_despite=enactments_despite,
            mandatory=min(self.mandatory, other.mandatory),
            universal=min(self.universal, other.universal),
        )

    def own_attributes(self) -> Dict[str, Any]:
        """
        Return attributes of ``self`` that aren't inherited from another class.

        Used for getting parameters to pass to :meth:`~Rule.__init__`
        when generating a new object.
        """
        attrs = self.__dict__.copy()
        for group in Procedure.context_factor_names:
            attrs.pop(group, None)
        return attrs

    def __str__(self):
        def factor_catalog(factors: List[Union[Factor, Enactment]], tag: str) -> str:
            lines = [f"{tag}: {factor}\n" for factor in factors]
            return "".join(lines)

        newline = "\n"
        despite_enactment_text = ""
        if self.enactments_despite:
            despite_enactment_text += "and despite the legislation\n"
            despite_enactment_text += str(
                factor_catalog(self.enactments_despite, "DESPITE")
            )

        return (
            "the rule that the court "
            + f"{'MUST' if self.mandatory else 'MAY'} "
            + f"{'ALWAYS' if self.universal else 'SOMETIMES'} "
            + f"accept the result{newline}"
            + f"{str(factor_catalog(self.procedure.outputs, 'RESULT'))}"
            + f"{'based on the input' + newline}"
            + f"{str(factor_catalog(self.procedure.inputs, 'GIVEN')) if self.procedure.inputs else ''}"
            + f"{str(factor_catalog(self.procedure.despite, 'DESPITE')) if self.procedure.despite else ''}"
            + f"{'according to the legislation' + newline if self.enactments else ''}"
            + f"{str(factor_catalog(self.enactments, 'GIVEN')) if self.enactments else ''}"
            + despite_enactment_text
        )


class Attribution:
    """
    An assertion about the meaning of a prior :class:`.Opinion`.

    Either a user or an :class:`.Opinion` may make an Attribution
    to an :class:`.Opinion`. An Attribution may attribute either a
    :class:`.Rule` or a further Attribution.
    """
