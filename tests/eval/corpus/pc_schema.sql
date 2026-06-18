-- Phase B eval seed schema — a minimal property & casualty claims model.
--
-- Read-only eval queries (the SQL-executability capability, plan §3.4) run
-- against a freshly seeded copy of this schema. Rows are deterministic so the
-- "executable ≥ 95%" measurement is reproducible. The schema deliberately
-- mirrors the domain in the existing intake fixtures (auto/property claims,
-- subrogation, FNOL timing) so the reference SQL in ``sql_cases.yaml`` reads
-- like real P&C analyst SQL. SQLite-compatible DDL only (the harness seeds an
-- on-disk SQLite database; see ``eval_corpus.seed_pc_schema``).

CREATE TABLE policies (
    policy_id        INTEGER PRIMARY KEY,
    line_of_business TEXT    NOT NULL,   -- 'auto' | 'property'
    state            TEXT    NOT NULL,
    inception_date   TEXT    NOT NULL,   -- ISO date
    annual_premium   REAL    NOT NULL
);

CREATE TABLE claims (
    claim_id         INTEGER PRIMARY KEY,
    policy_id        INTEGER NOT NULL REFERENCES policies(policy_id),
    line_of_business TEXT    NOT NULL,   -- denormalised for filter convenience
    loss_date        TEXT    NOT NULL,   -- ISO date
    fnol_date        TEXT    NOT NULL,   -- ISO date of first notice of loss
    paid_amount      REAL    NOT NULL,
    subro_eligible   INTEGER NOT NULL DEFAULT 0,  -- 0/1
    subro_recovered  REAL    NOT NULL DEFAULT 0,
    status           TEXT    NOT NULL,   -- 'open' | 'closed'
    state            TEXT    NOT NULL
);

INSERT INTO policies
    (policy_id, line_of_business, state, inception_date, annual_premium)
VALUES
    (100, 'auto',     'TX', '2023-11-01', 1450.0),
    (101, 'auto',     'TX', '2024-01-15', 1620.0),
    (102, 'auto',     'NY', '2023-09-20', 1875.0),
    (103, 'property', 'CA', '2024-02-01', 2310.0),
    (104, 'auto',     'TX', '2024-03-10', 1390.0),
    (105, 'property', 'TX', '2023-12-05', 1980.0),
    (106, 'auto',     'NY', '2024-04-22', 1705.0),
    (107, 'property', 'CA', '2024-05-30', 2540.0);

INSERT INTO claims
    (claim_id, policy_id, line_of_business, loss_date, fnol_date,
     paid_amount, subro_eligible, subro_recovered, status, state)
VALUES
    (1,  100, 'auto',     '2024-01-15', '2024-01-16',  5000.0, 1, 1200.0, 'closed', 'TX'),
    (2,  101, 'auto',     '2024-02-20', '2024-02-25',  8000.0, 1,    0.0, 'open',   'TX'),
    (3,  102, 'auto',     '2024-03-05', '2024-03-05',  2500.0, 0,  500.0, 'closed', 'NY'),
    (4,  103, 'property', '2024-04-11', '2024-04-18', 15000.0, 0,    0.0, 'open',   'CA'),
    (5,  104, 'auto',     '2024-05-22', '2024-05-23',  6200.0, 1, 3100.0, 'closed', 'TX'),
    (6,  100, 'auto',     '2024-06-30', '2024-07-02',  4100.0, 1,  900.0, 'closed', 'TX'),
    (7,  105, 'property', '2024-07-14', '2024-07-15',  9800.0, 0,    0.0, 'closed', 'TX'),
    (8,  102, 'auto',     '2024-08-09', '2024-08-20',  3300.0, 1,    0.0, 'open',   'NY'),
    (9,  106, 'auto',     '2024-09-01', '2024-09-01',  2750.0, 0,  250.0, 'closed', 'NY'),
    (10, 107, 'property', '2024-10-17', '2024-10-25', 12400.0, 0,    0.0, 'open',   'CA'),
    (11, 104, 'auto',     '2024-11-03', '2024-11-04',  5600.0, 1, 1800.0, 'closed', 'TX'),
    (12, 101, 'auto',     '2024-12-12', '2024-12-30',  7100.0, 1,    0.0, 'open',   'TX');
