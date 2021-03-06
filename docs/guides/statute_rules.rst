``Legislative Rules``
===========================

This tutorial will show how to use
`AuthoritySpoke <https://authorityspoke.readthedocs.io/en/latest/>`__ to
model legal rules found in legislation. This is a departure from most of
the AuthoritySpoke documentation, which focuses on judicial holdings.

These examples are based on the fictional `Australian Beard Tax
(Promotion of Enlightenment Values) Act
1934 <https://github.com/ServiceInnovationLab/example-rules-as-code>`__,
which was created thanks to the New Zealand `Service Innovation
Lab <https://github.com/ServiceInnovationLab>`__, for a chrestomathy of
computable legal rule models.

And thanks to Meng Weng Wong `for the vocab word
“chrestomathy” <https://twitter.com/mengwong/status/1205720239406755840>`__.

The Service Innovation Lab’s version of the Beard Tax Act is `a
PDF <https://github.com/ServiceInnovationLab/example-rules-as-code/blob/master/legislation.pdf>`__.
AuthoritySpoke works best with XML input with an Akoma Ntoso or United
States Legislative Markup schema. So I’ll start by preparing and loading
`my own USLM version of the Act
<https://github.com/mscarey/AuthoritySpoke/blob/master/example_data/codes/beard_tax_act.xml>`__.

Even though the Beard Tax Act is uncodified, in AuthoritySpoke any
collection of legislation is an instance of the “Code” class.

.. code:: python

    from authorityspoke.io import loaders

    beard_act = loaders.load_and_read_code("beard_tax_act.xml")
    beard_act




.. parsed-literal::

    USLMCode(Australian Beard Tax (Promotion of Enlightenment Values) Act 1934)



Next, I’ll prepare annotations for the statute provisions `in a JSON
file <https://github.com/mscarey/AuthoritySpoke/blob/master/example_data/holdings/beard_rules.json>`__,
and then load them as a Python dictionary. AuthoritySpoke rules
are procedural, so they have one or more outputs, and zero or more
inputs. They can also have “despite” factors, which are factors that may
not support the output, but they don’t preclude the output either.

AuthoritySpoke rules are usually supported by enactments such as statute
sections. These can be represented with the URI-like identifiers used in
USLM. In this case, since the Beard Tax Act is Act 47 of 1934, the
identifier for Part 1 Section 4 of the Act is /au/act/1934/47/1/4.

The “universal” flag indicates whether the Rule is one that applies in
every case where all of the inputs are present, or only in some cases.
The default is False, but this Rule overrides that default and says it
applies in every case where all of the inputs are present.

.. code:: python

    beard_dictionary = loaders.load_holdings("beard_rules.json")
    beard_dictionary[0]




.. parsed-literal::

    {'inputs': [{'type': 'fact',
       'content': '{the suspected beard} was facial hair'},
      {'type': 'fact',
       'content': 'the length of the suspected beard was >= 5 millimetres'},
      {'type': 'fact',
       'content': 'the suspected beard occurred on or below the chin'}],
     'outputs': [{'type': 'fact',
       'content': 'the suspected beard was a beard',
       'name': 'the fact that the facial hair was a beard'}],
     'enactments': [{'source': '/au/act/1934/47/1/4/chapeau'},
      {'source': '/au/act/1934/47/1/4/a', 'suffix': ', or'}],
     'universal': True}



Now we can have AuthoritySpoke read this JSON and convert it to a list
of Rule objects. In particular, we’ll look at the first two Rules, which
describe two ways that an object can be defined to be a “beard”.

.. code:: python

    from authorityspoke.io import readers

    beard_rules = readers.read_rules(beard_dictionary, beard_act)
    print(beard_rules[0])
    print("")
    print(beard_rules[1])


.. parsed-literal::

    the Rule that the court MAY ALWAYS impose the
      RESULT:
        the Fact that <the suspected beard> was a beard
      GIVEN:
        the Fact that <the suspected beard> was facial hair
        the Fact that the length of <the suspected beard> was at least 5
        millimeter
        the Fact that <the suspected beard> occurred on or below the chin
      GIVEN the ENACTMENTS:
        "In this Act, beard means any facial hair no shorter than 5
        millimetres in length that:" (Australian Beard Tax (Promotion of
        Enlightenment Values) Act 1934, /au/act/1934/47/1/4/chapeau)
        "occurs on or below the chin" (Australian Beard Tax (Promotion of
        Enlightenment Values) Act 1934, /au/act/1934/47/1/4/a)

    the Rule that the court MAY ALWAYS impose the
      RESULT:
        the Fact that <the suspected beard> was a beard
      GIVEN:
        the Fact that <the suspected beard> was facial hair
        the Fact that the length of <the suspected beard> was at least 5
        millimeter
        the Fact that <the suspected beard> existed in an uninterrupted line
        from the front of one ear to the front of the other ear below the nose
      GIVEN the ENACTMENTS:
        "In this Act, beard means any facial hair no shorter than 5
        millimetres in length that:" (Australian Beard Tax (Promotion of
        Enlightenment Values) Act 1934, /au/act/1934/47/1/4/chapeau)
        "exists in an uninterrupted line from the front of one ear to the
        front of the other ear below the nose." (Australian Beard Tax
        (Promotion of Enlightenment Values) Act 1934, /au/act/1934/47/1/4/b)


The difference between these two Rules is that the first one applies to
facial hair “on or below the chin” and the second applies to facial hair
“in an uninterrupted line from the front of one ear to the front of the
other ear below the nose”. I’ll rename them accordingly.

.. code:: python

    chin_rule = beard_rules[0]
    ear_rule = beard_rules[1]

Implication and Contradiction between Rules
-------------------------------------------

AuthoritySpoke doesn’t yet have a feature that directly takes a set of
known Facts, applies a Rule to them, and then infers legal conclusions.
Instead, in its current iteration, AuthoritySpoke can be used to combine
Rules together to make more Rules, or to check whether Rules imply or
contradict one another.

For instance, if we create a new Rule that’s identical to the first Rule
in the Beard Tax Act except that it applies to facial hair that’s
exactly 8 millimeters long instead of “no shorter than 5 millimetres”,
we can determine that the original “chin rule” implies our new Rule.

.. code:: python

    beard_dictionary[0]['inputs'][1]['content'] = 'the length of the suspected beard was = 8 millimetres'
    longer_hair_rule = readers.read_rule(beard_dictionary[0], beard_act)
    print(longer_hair_rule)


.. parsed-literal::

    the Rule that the court MAY ALWAYS impose the
      RESULT:
        the Fact that <the suspected beard> was a beard
      GIVEN:
        the Fact that <the suspected beard> was facial hair
        the Fact that the length of <the suspected beard> was exactly equal to
        8 millimeter
        the Fact that <the suspected beard> occurred on or below the chin
      GIVEN the ENACTMENTS:
        "In this Act, beard means any facial hair no shorter than 5
        millimetres in length that:" (Australian Beard Tax (Promotion of
        Enlightenment Values) Act 1934, /au/act/1934/47/1/4/chapeau)
        "occurs on or below the chin" (Australian Beard Tax (Promotion of
        Enlightenment Values) Act 1934, /au/act/1934/47/1/4/a)


.. code:: python

    chin_rule.implies(longer_hair_rule)




.. parsed-literal::

    True



Similarly, we can create a new Rule that says facial hair is *never* a
beard if its length is greater than 12 inches (we’ll use inches instead
of millimeters this time). And we can show that this new Rule
contradicts a Rule that came from the Beard Tax Act.

.. code:: python

    beard_dictionary[1]["despite"] = beard_dictionary[1]["inputs"][0]
    beard_dictionary[1]["inputs"] = {
        "type": "fact",
        "content": "the length of the suspected beard was >= 12 inches",
    }
    beard_dictionary[1]["outputs"][0]["truth"] = False
    beard_dictionary[1]["mandatory"] = True
    long_thing_is_not_a_beard = readers.read_rule(beard_dictionary[1], beard_act)
    print(long_thing_is_not_a_beard)


.. parsed-literal::

    the Rule that the court MUST ALWAYS impose the
      RESULT:
        the Fact it is false that <the suspected beard> was a beard
      GIVEN:
        the Fact that the length of <the suspected beard> was at least 12 inch
      DESPITE:
        the Fact that <the suspected beard> was facial hair
      GIVEN the ENACTMENTS:
        "In this Act, beard means any facial hair no shorter than 5
        millimetres in length that:" (Australian Beard Tax (Promotion of
        Enlightenment Values) Act 1934, /au/act/1934/47/1/4/chapeau)
        "exists in an uninterrupted line from the front of one ear to the
        front of the other ear below the nose." (Australian Beard Tax
        (Promotion of Enlightenment Values) Act 1934, /au/act/1934/47/1/4/b)


.. code:: python

    long_thing_is_not_a_beard.contradicts(ear_rule)




.. parsed-literal::

    True



Addition between Rules
----------------------

Finally, let’s look at adding Rules. AuthoritySpoke currently only
allows Rules to be added if applying the first Rule would supply you
with all the input Factor you need to apply the second Rule as well.
Here’s an example.

The Beard Tax Act defines the offense of “improper transfer of
beardcoin”. This offense basically has three elements:

1. a transfer of beardcoin
2. the absence of a license, and
3. a counterparty who is not the Department of Beards.

But in section 7A of the Beard Tax Act, we also learn specifically that
a “loan” of the tokens called beardcoin counts as the kind of “transfer”
that will support a conviction of the offense. We can represent this
information as a separate Rule, and then add it to the Rule defining the
offense. The result is that we discover an alternate way of establishing
the offense:

1. a loan of beardcoin
2. the absence of a license, and
3. a counterparty who is not the Department of Beards.

Here are the two Rules we’ll be adding together.

.. code:: python

    elements_of_offense = beard_rules[11]
    print(elements_of_offense)


.. parsed-literal::

    the Rule that the court MUST ALWAYS impose the
      RESULT:
        the Fact that <the defendant> committed the offense of improper
        transfer of beardcoin
      GIVEN:
        the Fact that <the beardcoin transaction> was a transfer of beardcoin
        between <the defendant> and <the counterparty>
        absence of the Fact that <the beardcoin transaction> was a licensed
        beardcoin repurchase
        the Fact it is false that <the counterparty> was <the Department of
        Beards>
      DESPITE:
        the Fact that the token attributed to <the Department of Beards>,
        asserting the fact that <the Department of Beards> granted an
        exemption from the prohibition of wearing beards, was counterfeit
      GIVEN the ENACTMENTS:
        "It shall be an offence to buy, sell, lend, lease, gift, transfer or
        receive in any way a beardcoin from any person or body other than the
        Department of Beards, except as provided in Part 4." (Australian Beard
        Tax (Promotion of Enlightenment Values) Act 1934,
        /au/act/1934/47/3/7A)
        "It shall be no defense to a charge under section 7A that the
        purchase, sale, lease, gift, transfer or receipt was of counterfeit
        beardcoin rather than genuine beardcoin." (Australian Beard Tax
        (Promotion of Enlightenment Values) Act 1934, /au/act/1934/47/3/7B/2)
      DESPITE the ENACTMENT:
        "The Department of Beards may issue licenses to such barbers,
        hairdressers or other male grooming professionals as they see fit to
        purchase a beardcoin from a customer whose beard they have removed,
        and to resell those beardcoins to the Department of Beards"
        (Australian Beard Tax (Promotion of Enlightenment Values) Act 1934,
        /au/act/1934/47/4/11)


.. code:: python

    loan_is_transfer = beard_rules[7]
    print(loan_is_transfer)


.. parsed-literal::

    the Rule that the court MUST ALWAYS impose the
      RESULT:
        the Fact that <the beardcoin transaction> was a transfer of beardcoin
        between <the defendant> and <the counterparty>
      GIVEN:
        the Fact that <the beardcoin transaction> was <the defendant>'s loan
        of the token attributed to <the Department of Beards>, asserting the
        fact that <the Department of Beards> granted an exemption from the
        prohibition of wearing beards, to <the counterparty>
      GIVEN the ENACTMENT:
        "It shall be an offence to buy, sell, lend, lease, gift, transfer or
        receive in any way a beardcoin from any person or body other than the
        Department of Beards, except as provided in Part 4." (Australian Beard
        Tax (Promotion of Enlightenment Values) Act 1934,
        /au/act/1934/47/3/7A)


But there’s a problem. The ``loan_is_transfer`` Rule establishes only
one of the elements of the offense. In order to create a Rule that we
can add to ``elements_of_offense``, we’ll need to add Facts establishing
the two elements other than the “transfer” element. We’ll also need to
add one of the Enactments that the ``elements_of_offense`` Rule relies
upon.

.. code:: python

    loan_without_exceptions = (
            loan_is_transfer
            + elements_of_offense.inputs[1]
            + elements_of_offense.inputs[2]
            + elements_of_offense.enactments[1]
        )
    print(loan_without_exceptions)


.. parsed-literal::

    the Rule that the court MUST ALWAYS impose the
      RESULT:
        the Fact that <the beardcoin transaction> was a transfer of beardcoin
        between <the defendant> and <the counterparty>
      GIVEN:
        the Fact that <the beardcoin transaction> was <the defendant>'s loan
        of the token attributed to <the Department of Beards>, asserting the
        fact that <the Department of Beards> granted an exemption from the
        prohibition of wearing beards, to <the counterparty>
        absence of the Fact that <the beardcoin transaction> was a licensed
        beardcoin repurchase
        the Fact it is false that <the counterparty> was <the Department of
        Beards>
      GIVEN the ENACTMENTS:
        "It shall be no defense to a charge under section 7A that the
        purchase, sale, lease, gift, transfer or receipt was of counterfeit
        beardcoin rather than genuine beardcoin." (Australian Beard Tax
        (Promotion of Enlightenment Values) Act 1934, /au/act/1934/47/3/7B/2)
        "It shall be an offence to buy, sell, lend, lease, gift, transfer or
        receive in any way a beardcoin from any person or body other than the
        Department of Beards, except as provided in Part 4." (Australian Beard
        Tax (Promotion of Enlightenment Values) Act 1934,
        /au/act/1934/47/3/7A)


With these changes, we can add together two Rules to get a new one.

.. code:: python

    loan_establishes_offense = loan_without_exceptions + elements_of_offense
    print(loan_establishes_offense)


.. parsed-literal::

    the Rule that the court MUST ALWAYS impose the
      RESULT:
        the Fact that <the beardcoin transaction> was a transfer of beardcoin
        between <the defendant> and <the counterparty>
        the Fact that <the defendant> committed the offense of improper
        transfer of beardcoin
      GIVEN:
        the Fact that <the beardcoin transaction> was <the defendant>'s loan
        of the token attributed to <the Department of Beards>, asserting the
        fact that <the Department of Beards> granted an exemption from the
        prohibition of wearing beards, to <the counterparty>
        absence of the Fact that <the beardcoin transaction> was a licensed
        beardcoin repurchase
        the Fact it is false that <the counterparty> was <the Department of
        Beards>
      GIVEN the ENACTMENTS:
        "It shall be no defense to a charge under section 7A that the
        purchase, sale, lease, gift, transfer or receipt was of counterfeit
        beardcoin rather than genuine beardcoin." (Australian Beard Tax
        (Promotion of Enlightenment Values) Act 1934, /au/act/1934/47/3/7B/2)
        "It shall be an offence to buy, sell, lend, lease, gift, transfer or
        receive in any way a beardcoin from any person or body other than the
        Department of Beards, except as provided in Part 4." (Australian Beard
        Tax (Promotion of Enlightenment Values) Act 1934,
        /au/act/1934/47/3/7A)


There will be additional methods for combining Rules in future versions
of AuthoritySpoke.

For now, try browsing through the beard_rules object to see how some of
the other provisions have been formalized. In all, there are 14 Rules in
the dataset.

.. code:: python

    len(beard_rules)




.. parsed-literal::

    14



Future Work
-----------

The Beard Tax Act example still presents challenges that AuthoritySpoke
hasn’t yet met. Two capabilities that should be coming to AuthoritySpoke
fairly soon are the ability to model remedies like the sentencing
provisions in /au/act/1934/47/3/9, and commencement dates like the one
in /au/act/1934/47/1/2.

But consider how you would model these more challenging details:

The “purpose” provisions in /au/act/1934/47/1/3 and /au/act/1934/47/4/10

Provisions delegating regulatory power, like /au/act/1934/47/2A/6B and
/au/act/1934/47/4/12

Provisions delegating permission to take administrative actions, like
/au/act/1934/47/2/6/1

Provisions delegating administrative responsibilities, like
/au/act/1934/47/2A/6D/1 and /au/act/1934/47/3/8/1

Provisions delegating fact-finding power, like /au/act/1934/47/2A/6D/2

Clauses limiting the effect of particular provisions to a certain
statutory scope, like the words “In this Act,” in /au/act/1934/47/1/4

Contact
~~~~~~~

If you have questions, comments, or ideas, please feel welcome to get in
touch via Twitter at
`@AuthoritySpoke <https://twitter.com/AuthoritySpoke>`__ or
`@mcareyaus <https://twitter.com/mcareyaus>`__, or via the `AuthoritySpoke
Github repo <https://github.com/mscarey/AuthoritySpoke>`__.
