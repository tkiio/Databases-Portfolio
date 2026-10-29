# Module 2 — ER modeling and schema auditing

This module studies entities, keys, relationships, cardinality, normalization, and integrity constraints by auditing a deliberately flawed maintenance database.

🎯 Learning Goals

This module gives you the opportunity to explore conceptual data modeling and requirements analysis and achieve competency in reading, critiquing, and formalizing a data model.

By the end of this module, you can:

- Reconstruct an ER/EER model (entities, attributes, keys, relationships, cardinalities) from an undocumented SQL schema.
- Identify integrity defects — missing foreign keys, orphan rows, redundant data, normalization violations — with queries, not intuition.
- Distinguish an entity relationship from an attribute, and a surrogate key from a natural key, and justify the choice.
- Express a schema as a code-first data contract (Pydantic / SQLAlchemy) that an application can enforce.
- Write the requirements the schema forgot: the business rules nobody encoded.


## Portfolio evidence

- [Study log](study-log.md) — references, findings, four ER sketches, and a verified sensor-count proof.
- [ER audit](er-audit.md) — entities, intended keys, reconstructed diagram, and observed cardinalities.
- [Rebuild the legacy database](setup_legacy.sql) — run with `sqlite3 module-02/legacy.db < module-02/setup_legacy.sql`.
- [Cardinality queries](cardinality.sql) and [integrity queries](integrity-audit.sql) — reproducible SQL evidence.
- [Integrity audit findings](integrity-audit.md) — query results and production impact.
- [Pydantic and SQLAlchemy contract](contract.py), [emitted DDL](contract-ddl.sql), and [design notes](contract-notes.md).
- [Inheritance comparison](inheritance.md) and [Mermaid lab](mermaid-lab.md).
- [Evidence notes](evidence/README.md) and [SQLite round-trip schema](roundtrip-schema.txt).
- [Reflection 2](../Reflections/ref02.md).

The generated `legacy.db` is local and ignored by Git; rebuild it from the setup script when needed.
