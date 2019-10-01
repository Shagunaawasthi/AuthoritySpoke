from typing import Any, Dict, List, Optional, Tuple, Type, Union
import re

from marshmallow import Schema, fields, validate
from marshmallow import pre_dump, pre_load, post_dump, post_load
from marshmallow import ValidationError
from marshmallow_oneofschema import OneOfSchema

from pint import UnitRegistry

from authorityspoke.enactments import Enactment
from authorityspoke.entities import Entity
from authorityspoke.factors import Factor, TextLinkDict
from authorityspoke.facts import Fact
from authorityspoke.predicates import Predicate
from authorityspoke.selectors import TextQuoteSelector

ureg = UnitRegistry()


class SelectorSchema(Schema):
    __model__ = TextQuoteSelector
    prefix = fields.Str(missing=None)
    exact = fields.Str(missing=None)
    suffix = fields.Str(missing=None)

    def split_text(self, text: str) -> Tuple[str, ...]:
        """
        Break up shorthand text selector format into three fields.

        Tries to break up the string into :attr:`~TextQuoteSelector.prefix`,
        :attr:`~TextQuoteSelector.exact`,
        and :attr:`~TextQuoteSelector.suffix`, by splitting on the pipe characters.

        :param text: a string or dict representing a text passage

        :returns: a tuple of the three values
        """

        if text.count("|") == 0:
            return ("", text, "")
        elif text.count("|") == 2:
            return tuple([*text.split("|")])
        raise ValidationError(
            "If the 'text' field is included, it must be either a dict"
            + "with one or more of 'prefix', 'exact', and 'suffix' "
            + "a string containing no | pipe "
            + "separator, or a string containing two pipe separators to divide "
            + "the string into 'prefix', 'exact', and 'suffix'."
        )

    @pre_load
    def expand_shorthand(
        self, data: Union[str, Dict[str, str]], **kwargs
    ) -> Dict[str, str]:
        """Convert input from shorthand format to normal selector format."""
        if isinstance(data, str):
            data = {"text": data}
        text = data.get("text")
        if text:
            data["prefix"], data["exact"], data["suffix"] = self.split_text(text)
            del data["text"]
        return data

    @post_load
    def make_object(self, data, **kwargs):
        return self.__model__(**data)


class EnactmentSchema(Schema):
    __model__ = Enactment
    name = fields.String(missing=None)
    source = fields.Url(relative=True)
    selector = fields.Nested(SelectorSchema, missing=None)

    def move_selector_fields(self, data, **kwargs):
        """
        Nest fields used for :class:`SelectorSchema` model.

        If the fields are already nested, they need not to be moved.

        The fields can only be moved into a "selector" field with a dict
        value, not a "selectors" field with a list value.
        """
        # Dumping the data because it seems to need to be loaded all at once.
        if isinstance(data.get("selector"), TextQuoteSelector):
            data["selector"] = SelectorSchema().dump(data["selector"])

        selector_field_names = ["text", "exact", "prefix", "suffix"]
        for name in selector_field_names:
            if data.get(name):
                if not data.get("selector"):
                    data["selector"] = {}
                data["selector"][name] = data[name]
                del data[name]
        return data

    def fix_source_path_errors(self, source: str) -> str:
        """
        Fix errors in source path formatting, substituting code URI if needed.
        """
        if not source:
            source = self.context["code"].uri

        if source:
            if not source.startswith("/") or source.startswith("http"):
                source = "/" + source
            if source.endswith("/"):
                source = source.rstrip("/")
        return source

    @pre_load
    def format_data_to_load(self, data, **kwargs):
        data["source"] = self.fix_source_path_errors(data.get(source))
        return self.move_selector_fields(data)

    @post_load
    def make_object(self, data, **kwargs):
        return self.__model__(**data, code=self.context["code"])


def read_quantity(value: Union[float, int, str]) -> Union[float, int, ureg.Quantity]:
    """
    Create pint quantity object from text.

    See `pint tutorial <https://pint.readthedocs.io/en/0.9/tutorial.html>`_

    :param quantity:
        when a string is being parsed for conversion to a
        :class:`Predicate`, this is the part of the string
        after the equals or inequality sign.
    :returns:
        a Python number object or a :class:`Quantity`
        object created with `pint.UnitRegistry
        <https://pint.readthedocs.io/en/0.9/tutorial.html>`_.
    """
    if isinstance(value, (int, float)):
        return value
    quantity = value.strip()
    if quantity.isdigit():
        return int(quantity)
    float_parts = quantity.split(".")
    if len(float_parts) == 2 and all(
        substring.isnumeric() for substring in float_parts
    ):
        return float(quantity)
    return ureg.Quantity(quantity)


def dump_quantity(obj: Predicate) -> Union[float, int, str]:
    """
    Convert quantity to string if it's a pint `ureg.Quantity` object.
    """
    quantity = obj.quantity
    if quantity is None:
        return None
    if isinstance(quantity, (int, float)):
        return quantity
    return f"{quantity.magnitude} {quantity.units}"


class PredicateSchema(Schema):
    __model__ = Predicate
    content = fields.Str()
    truth = fields.Bool(missing=True)
    reciprocal = fields.Bool(missing=False)
    comparison = fields.Str(
        missing="",
        validate=validate.OneOf([""] + list(Predicate.opposite_comparisons.keys())),
    )
    quantity = fields.Function(dump_quantity, deserialize=read_quantity)

    def get_quantity_from_content(self, data, normalized_operators):
        """
        Extract equality operator and use it to split the content phrase.
        """
        placeholder = "{}"
        # dict insert order matters, must try normalized_operators first
        for item in {**normalized_operators, **Predicate.opposite_comparisons}:
            if item in data["content"]:
                data["comparison"] = item
                data["content"], data["quantity"] = data["content"].split(item)
                data["content"] += placeholder
        return data

    def normalize_comparison(self, data, normalized_operators):
        if data.get("quantity") and not data.get("comparison"):
            data["comparison"] = "="

        if data.get("comparison") is None:
            data["comparison"] = ""

        if data.get("comparison") in normalized_operators:
            data["comparison"] = normalized_operators[data["comparison"]]

        return data

    @pre_load
    def format_data_to_load(self, data, **kwargs):
        normalized_operators = {"==": "=", "!=": "<>"}
        data = self.get_quantity_from_content(data, normalized_operators)
        data = self.normalize_comparison(data, normalized_operators)
        return data

    @post_load
    def make_object(self, data, **kwargs):
        return self.__model__(**data)


def get_references_from_string(content: str) -> Tuple[str, List[Entity]]:
    r"""
    Make :class:`.Entity` context :class:`.Factor`\s from string.

    This function identifies context :class:`.Factor`\s by finding
    brackets around them, while :func:`get_references_from_mentioned`
    depends on knowing the names of the context factors in advance.
    Also, this function works only when all the context_factors
    are type :class:`.Entity`.

    Despite "placeholder" being defined as a variable elsewhere,
    this function isn't compatible with any placeholder string other
    than "{}".

    This function no longer updates the "mentioned" :class:`.TextLinkDict`\.
    That update should instead happen after loading of each item in
    context_factors.

    :param content:
        a string containing a clause making an assertion.
        Curly brackets surround the names of :class:`.Entity`
        context factors to be created.

    :returns:
        a :class:`Predicate` and :class:`.Entity` objects
        from a string that has curly brackets around the
        context factors and the comparison/quantity.
    """
    pattern = r"\{([^\{]+)\}"
    entities_as_text = re.findall(pattern, content)

    context_factors = []
    for entity_name in entities_as_text:
        entity = {"type": "Entity", "name": entity_name}
        content = content.replace(entity_name, "")
        context_factors.append(entity)

    return content, context_factors


class BaseSchema(Schema):
    def get_from_mentioned(self, data, **kwargs):
        """
        Replaces data to load with any object with same name in "mentioned".
        """

        self.context["mentioned"] = self.context.get("mentioned") or {}
        name = ""
        if isinstance(data, str):
            name = data
        elif data.get("name"):
            name = data["name"]
        if name:
            for item in self.context["mentioned"]:
                if name == item.name:
                    return self.dump(item)
        return data

    def save_to_mentioned(self, obj, **kwargs):
        if obj not in self.context["mentioned"]:
            self.context["mentioned"][obj] = []
        return obj


class FactSchema(BaseSchema):
    __model__: Type = Fact
    predicate = fields.Nested(PredicateSchema)
    context_factors = fields.Nested("FactorSchema", many=True)
    standard_of_proof = fields.Str(missing=None)
    name = fields.Str(missing=None)
    absent = fields.Bool(missing=False)
    generic = fields.Bool(missing=False)

    def nest_predicate_fields(self, data, **kwargs):
        """
        Make sure predicate-related fields are in a dict under "predicate" key.
        """
        if data.get("content") and not data.get("predicate"):
            data["predicate"] = {}
            for predicate_field in [
                "content",
                "truth",
                "reciprocal",
                "comparison",
                "quantity",
            ]:
                if data.get(predicate_field):
                    data["predicate"][predicate_field] = data[predicate_field]
                    del data[predicate_field]
        return data

    def supply_name(self, truth: Optional[bool], content: str) -> str:
        """
        Provide a name for the :class:`.Fact` if none is provided.
        """
        name = f'{"false " if not truth else ""}{content}'
        return name.replace("{", "").replace("}", "")

    def get_references_from_mentioned(
        self, content: str, placeholder: str = "{}"
    ) -> Tuple[str, List[Dict]]:
        r"""
        Retrieve known context :class:`Factor`\s for new :class:`Fact`.

        :param content:
            the content for the :class:`Fact`\'s :class:`Predicate`.

        :param mentioned:
            list of :class:`Factor`\s with names that could be
            referenced in content

        :param placeholder:
            a string to replace the names of
            referenced :class:`Factor`\s in content

        :returns:
            the content string with any referenced :class:`Factor`\s
            replaced by placeholder, and a list of referenced
            :class:`Factor`\s in the order they appeared in content.
        """
        mentioned = self.context.get("mentioned") or {}
        sorted_mentioned = sorted(
            mentioned.keys(), key=lambda x: len(x.name) if x.name else 0, reverse=True
        )
        context_with_indices: Dict[Union[Enactment, Factor], int] = {}
        for factor in sorted_mentioned:
            if factor.name and factor.name in content and factor.name != content:
                factor_index = content.find(factor.name)
                for named_factor in context_with_indices:
                    if context_with_indices[named_factor] > factor_index:
                        context_with_indices[named_factor] -= len(factor.name) - len(
                            placeholder
                        )
                context_with_indices[factor] = factor_index
                new_content = content.replace(factor.name, placeholder)
        sorted_factors = sorted(context_with_indices, key=context_with_indices.get)
        return new_content, [factor.__dict__ for factor in sorted_factors]

    def extract_context_factors(
        self, content: str, placeholder: str
    ) -> Tuple[str, List[Dict]]:
        if placeholder[0] in content:
            content, context_factors = get_references_from_string(content)
        else:
            content, context_factors = self.get_references_from_mentioned(
                content, placeholder
            )
        return content, context_factors

    @pre_load
    def format_data_to_load(self, data, **kwargs):
        data = self.nest_predicate_fields(data)
        if not data.get("name"):
            data["name"] = self.supply_name(
                truth=data["predicate"].get("truth"),
                content=data["predicate"]["content"],
            )

        placeholder = "{}"  # to be replaced in the Fact's string method
        if not data.get("context_factors"):
            data["predicate"]["content"], data[
                "context_factors"
            ] = self.extract_context_factors(data["predicate"]["content"], placeholder)

        return data

    @post_load
    def make_fact(self, data, **kwargs):
        answer = Fact(**data)
        return (
            (answer, self.context["mentioned"])
            if self.context.get("report_mentioned")
            else answer
        )


class EntitySchema(BaseSchema):
    __model__: Type = Entity
    name = fields.Str(missing=None)
    generic = fields.Bool(missing=True)
    plural = fields.Bool(missing=False)

    @pre_load
    def format_data_to_load(self, data, **kwargs):
        data = self.get_from_mentioned(data)
        return data

    @post_load
    def make_entity(self, data, **kwargs):
        answer = Entity(**data)
        self.save_to_mentioned(answer)
        return (
            (answer, self.context["mentioned"])
            if self.context.get("report_mentioned")
            else answer
        )


class FactorSchema(OneOfSchema):
    type_schemas = {"Entity": EntitySchema, "Fact": FactSchema}

    def get_obj_type(self, obj):
        return obj.__class__.__name__.capitalize()


SCHEMAS = [schema for schema in BaseSchema.__subclasses__()]


def get_schema_for_factor_record(typename: str) -> Schema:
    """
    Find the Marshmallow schema for an AuthoritySpoke object.
    """
    for option in SCHEMAS:
        if typename.lower() == option.__model__.__name__.lower():
            return option(unknown="EXCLUDE")
    return None


def get_schema_for_item(item: Any) -> Schema:
    """
    Find the Marshmallow schema for an AuthoritySpoke object.
    """
    for option in SCHEMAS:
        if hasattr(option, "__model__") and item.__class__ == option.__model__:
            return option()
    return None
