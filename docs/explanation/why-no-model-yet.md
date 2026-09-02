# Why there is no model in this yet

The obvious way to turn a cookbook into structured data is to hand pages to a
language model and ask for JSON. This release deliberately does not, and the
reason is not cost.

## A parser establishes the bar

Escoffier structured his own book. Every preparation is numbered, titled, and
placed in a sequence, and he states his five mothers in a sentence you can
point at. A regular expression recovers 151 sauce preparations and links 57 of
them to a base.

That number is the bar. Any model applied to this source has to beat 57, and
until a parser has been run, nobody knows what "beating it" would mean. A
model that recovers 35 looks impressive in isolation and is nearly worthless
next to free.

Skipping this step is how projects end up unable to say whether their model is
adding anything.

## Errors that look like successes

A schema validates shape, not truth. A model asked for JSON will return
well-formed JSON, with a plausible parent for every preparation, including
the 94 where the source states none, or states two. Those outputs pass
validation, read correctly, and are wrong.

The parser cannot produce that failure. It resolves a parent only where the
opening paragraph names exactly one, so `parent` is `None` on 94 entries.
Unresolved is a visible, countable state. Confidently wrong is not.

## The unresolved entries are the finding

94 of 151 preparations do not state a base in their opening paragraph, or
state two names and mark neither as the base. That is not parser weakness —
it is what the source is like. Cardinal says "Boil one pint of Béchamel" and
then "finish ... with lobster butter". Escoffier assumed a reader who already
knew which of those is the base and which is the finish, so he did not write
it down. Ten sauces are unresolved for exactly that reason, and every one of
them was resolved before the butters were catalogued. Widening what the
parser can see lowered its score, and the lower score is the honest one.

Recovering knowledge an author assumed is exactly the work a model can do and
a parser cannot. That is the case for adding one — and it is a case that can
only be made by having run the parser first.

## What this constrains later

Three decisions here are load-bearing:

**Terms are tagged, never translated.** The 1907 translator left *espagnole*
and *velouté* in French because they are proper nouns for preparations. A
pipeline that normalises everything to English destroys distinctions it will
later need, and the further the corpus moves from Europe, the more it destroys.

**Every claim carries a source reference.** `entry 32, line 1680` can be
checked by hand, and the reference says which text it points into. One of the
two witnesses is a scan, so a claim from it is evidence about the scan rather
than about the book. Once a model is producing claims, provenance stops being
a nicety.

**`None` means unresolved.** Not "no parent". A later stage may fill it; a
stage that cannot distinguish "unknown" from "none" will fill it wrongly and
silently.
