# In-process market contract

No HTTP interface or durable storage format is introduced.

- Entities: rescue.market.models.<category>; aggregate: rescue.market.models.b3_market.
- Rules: rescue.market.models.<category>.rules. Former root facades have no re-exports.
- Inventory accepts tuples of structural CommitmentSource values; domain code imports no concrete mission type.
- Mutating rules return replacement B3Market values; DomainValidationError preserves original aggregate, run and histories.
- Exact existing parameter signatures remain authoritative in category functions. Caller changes migrate import paths only.

| Rule | Contract |
|---|---|
| publish_availability | Append valid publication, refuse conflicting same-time data |
| latest_availability | Latest publication for ship or None |
| find_rfq | Resolve RFQ identity, retain missing-ID error policy |
| hold_quote | Reserve only free capacity across all missions; append HELD |
| transfer_quote | Accept live held quote and append ACCEPTED with request ID; caller publishes pending request atomically |
| close_quote | Reject or expire held quote, releasing only its hold; append terminal change |
| quote_history | Immutable quote changes in append order |
| publish_offer_revision | Preserve revisions, highest number current |
| usage | Accounting snapshot from holds and supplied commitments |

Every public rule has a same-name Markdown document specifying purpose, timing, rationale, refusals and diagrams. Rules perform no I/O, clock access or store access.
