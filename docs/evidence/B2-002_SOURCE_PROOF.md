\# B2-002 Live Source-Provenance Proof



\*\*Increment:\*\* B2-002 — Sandbox Source Contract  

\*\*Disposition:\*\* PASS  

\*\*Proof date:\*\* 2026-08-13



\## Candidate source



Canonical repository:



`https://github.com/sbracewell64/inkwell-agent-sandboxes-and-software-factory.git`



Candidate commit:



`0ad16d939366ad0b6bb9c2bdb28eea7799a8e8df`



Candidate branch:



`increment/b2-002-sandbox-source-contract`



The candidate commit was pushed to the canonical repository before the live sandbox proof.



\## Sandbox identity



Run ID:



`b2-002-source-proof-20260813-f9681a`



\## FILL proof



FILL was invoked without an explicit SHA argument.



It automatically resolved:



\- `source\_repo` = `https://github.com/sbracewell64/inkwell-agent-sandboxes-and-software-factory.git`

\- `source\_sha` = `0ad16d939366ad0b6bb9c2bdb28eea7799a8e8df`



FILL cloned the canonical repository and passed its exact-source gate:



`HEAD 0ad16d939366ad0b6bb9c2bdb28eea7799a8e8df matches pin 0ad16d939366ad0b6bb9c2bdb28eea7799a8e8df`



\## Durable run-record proof



The closed run record retained:



\- `source\_repo` = `https://github.com/sbracewell64/inkwell-agent-sandboxes-and-software-factory.git`

\- `source\_sha` = `0ad16d939366ad0b6bb9c2bdb28eea7799a8e8df`

\- `commit\_sha` = `0ad16d939366ad0b6bb9c2bdb28eea7799a8e8df`



Tracked evidence copy:



`docs/evidence/B2-002\_SOURCE\_PROOF\_RUN\_RECORD.json`



\## Independent guest proof



The guest checkout independently reported:



`origin`:



`https://github.com/sbracewell64/inkwell-agent-sandboxes-and-software-factory.git`



`HEAD`:



`0ad16d939366ad0b6bb9c2bdb28eea7799a8e8df`



`git status --porcelain` produced no output.



Therefore the guest repository, guest source commit, and clean working-tree state agreed with the host-selected provenance record.



\## SETUP gate proof



SETUP Gate A independently verified:



\- guest origin exactly matched recorded `source\_repo`;

\- guest HEAD exactly matched recorded `source\_sha` / `commit\_sha`;

\- guest working tree was clean.



Observed Gate A result:



`\[gate] A PASS  git integrity`



SETUP completed its overall gate and reported the sandbox healthy.



\## Unrelated known gate anomaly



During the same SETUP run, stock-roster model probes printed insufficient-credit failures while later C/D/E assertions still reported PASS.



That behavior predates B2-002 and remains a documented independent defect. It is not treated as evidence for or against the source-provenance contract.



\## Cleanup proof



Teardown was invoked with `--no-harvest` because no ADW work was performed.



Observed results:



\- spend recorded as `$0`;

\- runtime key revoked;

\- VM destroyed;

\- runtime key file shredded;

\- run record closed;

\- key-absence gate passed.



The closed run record contains:



`closed\_at = 2026-08-13T16:08:27Z`



After teardown:



`ssh exe.dev ls`



reported:



`No VMs found. Create one with 'new'.`



\## Acceptance conclusion



B2-002 proved that a fresh sandbox can derive source authority from the host checkout, clone the operator-owned canonical repository, execute an exact committed source revision, retain that provenance durably, independently re-verify it during SETUP, and cleanly destroy all temporary runtime resources afterward.



\*\*Result: PASS\*\*

