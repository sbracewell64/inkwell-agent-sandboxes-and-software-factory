# Derived-source provenance records

One JSON record per derived input, named `<record-id>.json`, conforming to
`docs/reference/DERIVED_SOURCE_PROVENANCE.md` and enforced by
`docs/validation/check_derived_source_provenance.py`.

**This registry is empty, and its emptiness is not a certification.**

An empty registry means the enumerated universe holds no derived source, so
there is nothing to certify. The validator reports that as `NOT_APPLICABLE`, a
form of could-not-observe. It is never reported as `PASS`, and no reader should
take a green check here as evidence that any derived source complies with
anything.

Adding a record does not authorise a migration. No migration is authorised.
This directory is a gate that a future import would have to satisfy, not a door
that makes one easier.
