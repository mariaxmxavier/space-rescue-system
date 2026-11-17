---
kind: rule
id: P-0002
type: constraint
strength: default
status: active
scope:
  - activity:coding
when: adding or moving classes in this repository
do: put one class per file, in nested folders grouped by role (e.g. adapters/ports/, adapters/memory/)
instead_of: several classes in one module
because: the owner wants each entity easy to find in its own file
source: "2026-11-16: 'all entities/ diffrent classes must be broken into nested files and folders format, docs string include in every code comment about what it dows, when is called, why'"
added: 2026-11-16
approved: 2026-11-16
last_confirmed: 2026-11-16
private: false
---
