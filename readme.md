# AuthoritySpoke

[![CircleCI](https://circleci.com/gh/mscarey/AuthoritySpoke.svg?style=svg)](https://circleci.com/gh/mscarey/AuthoritySpoke) [![Coverage Status](https://coveralls.io/repos/github/mscarey/AuthoritySpoke/badge.svg?branch=master)](https://coveralls.io/github/mscarey/AuthoritySpoke?branch=master)

AuthoritySpoke is the world's first open source legal authority automation tool.

## Installing AuthoritySpoke

AuthoritySpoke is a Python package [available on PyPI](https://pypi.org/project/AuthoritySpoke/), so you can install it with pip:

```
$ pip install authorityspoke
```

## Trying it Out

Here's an example that discovers contradictory legal holdings in `Oracle America, Inc. v. Google Inc., 750 F.3d 1339` (a famous case that dealt with a claim that the Android operating system infringed the copyright on the Java language) and `Lotus Development Corporation v. Borland International, 49 F.3d 807` (an older case about whether a user interface was copyrightable).

Copies of both opinions can be loaded from the `example_data` folder. (But you can also use AuthoritySpoke to retrieve opinions from the [Caselaw Access Project API](https://api.case.law/v1/).)

```python
from authorityspoke.io.loaders import load_and_read_decision

oracle = load_and_read_decision("oracle_h.json")
lotus = load_and_read_decision("lotus_h.json")
```

The `example_data` folder also contains legislation in XML files that can be organized by linking them to a `Regime` object.

```python
from authorityspoke import Regime

from authorityspoke.io.loaders import load_code

usa = Regime()

usa.set_code(load_code("constitution.xml"))
usa.set_code(load_code("usc17.xml"))
usa.set_code(load_code("cfr37.xml"))
```

Structured annotations about the holdings in _Oracle_ and _Lotus_ can also be loaded from the `example_data` folder, and can be linked to the `Opinion` objects.

```python
from authorityspoke.io.loaders import load_and_read_holdings

oracle.posit(*load_and_read_holdings("holding_oracle.json", regime=usa))
lotus.posit(*load_and_read_holdings("holding_lotus.json", regime=usa))
```

Now, each `Opinion` has a `.contradicts` method that can return a boolean indicating whether its holdings conflict with the holdings of another `Opinion`.

```python
print(lotus.contradicts(oracle))
```

```
True
```

That's good to know, but we don't want to take it on faith that a contradiction exists. Let's use the `explain_contradiction` method to find the contradictory Holdings posited by the _Oracle_ and _Lotus_ cases, and to generate a rudimentary explanation of why they contradict.

```python
explanation = lotus.explain_contradiction(oracle)
print(explanation)
```

```
an Explanation of why there is a contradiction between
  the Holding to ACCEPT
    the Rule that the court MUST ALWAYS impose the
      RESULT:
        the Fact it is false that <the Lotus menu command hierarchy> was
        copyrightable
      GIVEN:
        the Fact that <the Lotus menu command hierarchy> was a method of
        operation
      DESPITE:
        the Fact that a text described <the Lotus menu command hierarchy>
        the Fact that <the Lotus menu command hierarchy> was an original work
      GIVEN the ENACTMENTS:
        "In no case does copyright protection for an original work of
        authorship extend to any" (Title 17, /us/usc/t17/s102/b)
        "method of operation" (Title 17, /us/usc/t17/s102/b)
and
  the Holding to ACCEPT
    the Rule that the court MUST SOMETIMES impose the
      RESULT:
        the Fact that <the Java API> was copyrightable
      GIVEN:
        the Fact that <the Java language> was a computer program
        the Fact that <the Java API> was a set of application programming
        interface declarations
        the Fact that <the Java API> was an original work
        the Fact that <the Java API> was a non-literal element of <the Java
        language>
        the Fact that <the Java API> was the expression of an idea
        the Fact it is false that <the Java API> was essentially the only way
        to express the idea that it embodied
        the Fact that <the Java API> was creative
        the Fact that it was possible to use <the Java language> without
        copying <the Java API>
      DESPITE:
        the Fact that <the Java API> was a method of operation
        the Fact that <the Java API> contained short phrases
        the Fact that <the Java API> became so popular that it was the
        industry standard
        the Fact that there was a preexisting community of programmers
        accustomed to using <the Java API>
      GIVEN the ENACTMENT:
        "Copyright protection subsists, in accordance with this title, in
        original works of authorship fixed in any tangible medium of
        expression, now known or later developed, from which they can be
        perceived, reproduced, or otherwise communicated, either directly or
        with the aid of a machine or device." (Title 17, /us/usc/t17/s102/a)
      DESPITE the ENACTMENTS:
        "In no case does copyright protection for an original work of
        authorship extend to any" (Title 17, /us/usc/t17/s102/b)
        "method of operation" (Title 17, /us/usc/t17/s102/b)
        "The following are examples of works not subject to copyright and
        applications for registration of such works cannot be entertained: (a)
        Words and short phrases such as names, titles, and slogans;" (Code of
        Federal Regulations Title 37, /us/cfr/t37/s202.1)
is that <the Lotus menu command hierarchy> is like <the Java API>
```

## Learning about AuthoritySpoke

You can find the example above and much more information about using the AuthoritySpoke Python package in the [Introduction to AuthoritySpoke Jupyter notebook](notebooks/introduction.ipynb).

Use the button below to interact with the notebook online through Binder. If you use Binder, you'll be shown the directory structure of this repo. Navigate to the `notebooks` folder to find the tutorials.

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/mscarey/AuthoritySpoke/master)

You can also find static versions of the tutorial notebooks, the API documentation, and more [in the project documentation](https://authorityspoke.readthedocs.io/en/latest/).


## Contributing to AuthoritySpoke

Contributor documentation is coming soon!

All participants are expected to follow the [code of conduct](code_of_conduct.md). AuthoritySpoke uses the [Contributor Covenant, version 1.4](https://www.contributor-covenant.org/version/1/4/code-of-conduct.html).

Submitting a pull request or other code contribution to AuthoritySpoke requires acceptance of a [contributor license agreement](contributor_agreement.md). The agreement's provisions are based on the [Apache Software Foundation Individual Contributor License Agreement V2.0](http://www.apache.org/licenses/icla.pdf).
