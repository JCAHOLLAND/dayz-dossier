# Combat-pattern association model v2 (exploratory)

All kills and deaths contribute. Stable profile IDs combine aliases; names on separate IDs never merge. Confirmed groups are opt-in and empty by default. Weapon similarity is entirely excluded and changing every weapon label leaves inference identical.

## Candidate evidence

For each opponent, consider players who interact with that opponent within 180 seconds. Include shared kills, shared deaths and mixed kill/death trade sequences. Merge continuous supporting observations with gaps no greater than 30 minutes to reduce double-counting one fight. All-role event co-occurrence within 60 seconds supplies weak timing context. Even a single temporal/shared-opponent signal can appear as a low-scoring candidate. No actual proximity, session, login, sleep, location or real-world timezone is inferred.

## Exact score

Components before shrinkage:

- Shared-opponent evidence: 8 × min(windows, 10) × (0.7 + 0.3 × average opponent rarity). Rarity is inverse square root of the count of distinct players interacting with that opponent.
- Supporting UTC dates: 3 × min(days, 6).
- Timing excess: min(10, 2 × max(0, observed timing windows − expected timing windows)).
- Timing context: min(6, 2 × ln(1 + timing windows)).
- Role-pattern diversity: min(4, 2 × max(0, distinct role-pattern categories − 1)).
- Graph context: capped at 5; common repeated-pattern neighbours contribute 2 / sqrt(their repeated-pattern degree).
- UTC event-hour overlap: at most 4 points from histogram intersection, only with at least 5 events per player.
- Distance-habit overlap: at most 1.5 points from 100-metre distance-bin histogram intersection, only with at least 5 kills per player. No penalty for different habits.
- Direct combat: subtract min(40, 8 × direct kill events).

Expected timing windows = sum across shared 30-minute clock buckets of min(1, eventCountA × eventCountB / 15). This approximates random 60-second overlap under uniform timing within a bucket and is only a volume baseline; fights violate uniformity. It is not a significance test.

Sparse-evidence multiplier = 0.65 + 0.35 × n / (n + 3), where n is the number of continuous observation windows in the union of shared-opponent and timing evidence. Multiply component sum, clamp to 0–100, then round. Scores are uncalibrated heuristic indices, never probability percentages. A capped 100 is marked saturated. Several features remain correlated despite window deduplication and small context caps.

## Groups: maximum THREE total people

Candidate pairs need at least two shared-opponent windows, score at least 30 and no direct combat to qualify for inferred group membership. Generate all qualifying duos and fully connected trios; every internal pairing of a trio must qualify. Sort by total internal score, with deterministic size/ID tie breaks, and choose non-overlapping groups globally. Every profile belongs to at most one inferred group and sees the same members. The selected player has at most two inferred teammates. Other candidates remain separate; direct-combat candidates have negative evidence and cannot enter inferred groups. Historical membership changes are not reconstructed.

## Evidence and validation

The UI exposes component counts, approximate expected timing, sparse shrinkage, role counts, graph context, UTC hour overlap, distance overlap, direct-combat flags and up to three sample UTC encounters. It distinguishes sparse candidates and inferred groups. Model output is not proof of teammates.

Synthetic tests cover known repeated groups, unrelated disjoint activity, busy single-fight non-groups, consistent membership and max-three invariants, both killer/victim roles, direct-combat penalties, continuous-fight merging across clock boundaries, and complete independence from weapon labels.

Dataset-specific validation outputs are not included. Synthetic tests cover invariants and examples, not real-world accuracy. There are insufficient independent labels for precision, recall, probability calibration or optimal-threshold claims.
