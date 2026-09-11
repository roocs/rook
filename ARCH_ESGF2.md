# Rook Federation for ESGF-NG

## What is Rook?

**Rook** is a server-side processing service for climate data.

* It provides processing operations through WPS / OGC interfaces.
* Users work with **datasets**, rather than downloading all source files first.
* Typical operations include **subset, regrid and other climate-data transformations**.
* `orchestrate` accepts a simple JSON workflow and executes the requested processing chain.
* Processing runs close to the large data pools.

```mermaid
flowchart LR
    User[User / Service]
    Rook[Rook]
    Data[Climate Data Pool]

    User -->|dataset + workflow| Rook
    Rook -->|local access| Data
    Rook -->|result| User
```

> **Move the processing to the data instead of moving the data to the user.**

---

# Rook for Copernicus CDS

Rook is already used to provide server-side processing for the **Copernicus Climate Data Store (CDS)**.

* CDS sends a workflow describing the requested processing.
* Rook resolves CDS dataset IDs through an **Intake catalog backed by PostgreSQL**.
* DKRZ and IPSL provide equivalent data and processing capabilities.
* An AWS load balancer can therefore distribute requests between them.
* `orchestrate` executes the workflow at the selected site.

```mermaid
flowchart LR
    CDS[Copernicus CDS]
    LB[AWS Load Balancer]

    DE[Rook<br/>DKRZ]
    FR[Rook<br/>IPSL]

    DEData[CDS Data]
    FRData[CDS Data]

    CDS -->|workflow| LB

    LB --> DE
    LB --> FR

    DE --> DEData
    FR --> FRData
```

This works well because the two sites are effectively **interchangeable processing backends**.

**Links**

* [Copernicus Climate Data Store](https://cds.climate.copernicus.eu/)
* [ROOCS usage dashboard – all years](https://roocs.github.io/dashboard/summary-all-years/)

The ROOCS dashboard shows the operational use of the service over the years.

---

## Example: Rook from a notebook

Rook can also be used interactively from Python with **rooki**, the Python client for Rook.

This example uses a real C3S-CORDEX dataset and creates a small processing workflow:

```python
from rooki import operators as ops

tas = ops.Input(
    "tas",
    [
        "c3s-cordex.output.EUR-11.IPSL.IPSL-IPSL-CM5A-MR.rcp85."
        "r1i1p1.IPSL-WRF381P.v1.day.tas.v20190919"
    ],
)

subset = ops.Subset(
    tas,
    time="2006/2006",
    time_components="month:jan,feb,mar",
)

workflow = ops.Average(subset, dims="time")

response = workflow.orchestrate()
```

The workflow:

* selects a logical C3S-CORDEX dataset;
* subsets January–March 2006;
* calculates the average over time;
* sends the workflow to Rook using `orchestrate()`.

```mermaid
flowchart LR
    Notebook[rooki Notebook]
    Workflow[JSON Workflow]
    Rook[Rook orchestrate]
    Subset[Subset]
    Average[Average]
    Result[Result]

    Notebook --> Workflow
    Workflow --> Rook
    Rook --> Subset
    Subset --> Average
    Average --> Result
```

The user works with a **logical dataset ID and processing workflow**. Rook resolves and processes the underlying files close to the data.

**Complete example**

[Rendered C3S-CORDEX rooki notebook on GitHub](https://github.com/roocs/rooki/blob/master/notebooks/demo/demo-rooki-c3s-cordex.ipynb)

---

# From CDS to ESGF-NG

ESGF-NG introduces a different situation.

* DKRZ, IPSL and CEDA provide ESGF data pools.
* The pools **overlap, but are not identical**.
* A normal round-robin load balancer cannot know which Rook can process a particular dataset.
* Restricting processing to a fully replicated core would reduce ESGF data coverage.

```mermaid
flowchart LR
    DE[DKRZ<br/>Data Pool]
    FR[IPSL<br/>Data Pool]
    UK[CEDA<br/>Data Pool]

    DE <-. overlap .-> FR
    FR <-. overlap .-> UK
    DE <-. overlap .-> UK
```

The proposed solution adds **dataset-aware delegation to Rook itself**.

---

# ESGF-NG Rook Federation

## Design idea

Rook remains **one software deployment** serving CDS, ESGF-NG and potentially other use cases.

For ESGF-NG:

* DKRZ, IPSL and CEDA run identical Rook services.
* Every Rook can act as the entry point for a request.
* A lightweight `broker` WPS process chooses the appropriate Rook site.
* The existing AWS load balancer provides the stable public endpoint.
* No additional central broker or cloud service is required.

---

## 1. High-level architecture

```mermaid
flowchart LR
    Client[Client / ESGF Service]
    LB[AWS Load Balancer]

    DE[Rook<br/>DKRZ]
    FR[Rook<br/>IPSL]
    UK[Rook<br/>CEDA]

    Client --> LB

    LB --> DE
    LB --> FR
    LB --> UK

    DE <--> FR
    FR <--> UK
    DE <--> UK
```

The load balancer only needs to select an **available Rook**.

It does not need to understand dataset placement. The selected Rook handles this through its `broker` process.

---

## 2. Dataset knowledge at every site

Each Rook site maintains a PostgreSQL index with two kinds of information:

* **global dataset placement:** which ESGF sites provide a dataset;
* **local assets:** the actual files or aggregations available to the local Rook.

```mermaid
flowchart LR
    Kafka[ESGF-NG Kafka<br/>STAC records + patches]

    DB[Local PostgreSQL<br/>ESGF Index]

    Placement[Dataset Placement<br/>dataset → sites]
    Assets[Local Assets<br/>dataset → files]

    Kafka --> DB

    DB --> Placement
    DB --> Assets
```

* The existing ESGF-NG Kafka publication stream keeps the index synchronized.
* Rook becomes another direct consumer of the ESGF-NG publication infrastructure.
* Broker lookups normally use the local PostgreSQL database instead of querying STAC for every request.

---

## 3. STAC as fallback

The local index may occasionally be incomplete or out of sync.

The global ESGF-NG STAC catalog provides a fallback.

```mermaid
flowchart LR
    Rook[Rook Dataset Resolver]
    DB[Local PostgreSQL Index]
    STAC[Global ESGF-NG STAC]

    Rook --> DB

    DB -- found --> Rook
    DB -. missing / stale .-> STAC
    STAC -. result .-> Rook
    Rook -. repair .-> DB
```

* PostgreSQL is the normal lookup path.
* STAC can recover missing information.
* Information obtained from STAC can optionally repair the local index.
* Missing local data does **not** silently turn into remote HTTP processing.

---

## 4. Broker and orchestrate

`broker` uses the **same parameters and JSON workflow document as `orchestrate`**.

Their responsibilities are different:

```mermaid
flowchart LR
    Workflow[JSON Workflow]

    Broker[broker<br/>WHERE?]
    Orchestrate[orchestrate<br/>HOW?]
    Process[subset / regrid / ...]

    Workflow --> Broker
    Broker --> Orchestrate
    Orchestrate --> Process
```

### `broker`

* inspects the workflow and identifies the dataset;
* determines where the dataset can be processed;
* selects a local or remote Rook;
* submits `orchestrate` asynchronously at the selected site.

### `orchestrate`

* interprets the workflow;
* executes `subset`, `regrid`, etc.;
* does not make federation decisions.

> **broker decides WHERE — orchestrate decides HOW.**

---

## 5. From the existing workflow to federation

The important part is that the **workflow itself does not have to change**.

```mermaid
flowchart LR
    Client[rooki / Service]
    Workflow[Same JSON Workflow]

    subgraph CDS["Current CDS"]
        OrchestrateCDS[orchestrate]
        ProcessingCDS[Processing]
        OrchestrateCDS --> ProcessingCDS
    end

    subgraph ESGF["ESGF-NG"]
        Broker[broker]
        OrchestrateESGF[orchestrate<br/>selected site]
        ProcessingESGF[Processing]

        Broker --> OrchestrateESGF
        OrchestrateESGF --> ProcessingESGF
    end

    Client --> Workflow

    Workflow --> OrchestrateCDS
    Workflow --> Broker
```

For CDS today:

```text
workflow → orchestrate
```

For federated ESGF-NG processing:

```text
same workflow → broker → orchestrate @ selected site
```

This keeps the client-facing processing model simple.

---

## 6. Site selection

The broker combines **dataset placement** with current **Rook availability**.

```mermaid
flowchart TD
    Request[Broker Request]

    Local{Dataset local?}

    LocalRun[Use local Rook]
    Sites[Look up replica sites]
    Health[Check health / status]
    Candidate{Available site?}

    Remote[Choose remote Rook]
    Fail[Dataset currently<br/>not processable]

    Request --> Local

    Local -- Yes --> LocalRun

    Local -- No --> Sites
    Sites --> Health
    Health --> Candidate

    Candidate -- Yes --> Remote
    Candidate -- No --> Fail
```

Three pieces of information have separate responsibilities:

* **Dataset index:** where does the data exist?
* **health/status:** which Rook sites can currently accept work?
* **broker:** which site should execute this request?

Temporary downtime does not change the dataset placement metadata.

---

## 7. Local execution

If the receiving Rook has the dataset, the broker submits the workflow to its local `orchestrate`.

```mermaid
sequenceDiagram
    participant C as Client
    participant B as broker@DKRZ
    participant O as orchestrate@DKRZ

    C->>B: JSON workflow
    B->>B: Dataset is local
    B->>O: Submit async
    O-->>B: Job / status URL
    B-->>C: Job / status response
```

The broker performs delegation only. The actual processing remains with `orchestrate`.

---

## 8. Remote execution

If the dataset is not local, the broker selects another available site.

```mermaid
sequenceDiagram
    participant C as Client
    participant B as broker@DKRZ
    participant O as orchestrate@CEDA

    C->>B: JSON workflow
    B->>B: Select CEDA
    B->>O: Submit async
    O-->>B: Job / status URL
    B-->>C: Job / status response
```

* The remote request goes directly to `orchestrate`.
* It does **not** call the remote broker again.
* This prevents delegation loops.

---

## 9. Asynchronous processing

The broker only needs to remain active long enough to delegate the job.

```mermaid
flowchart LR
    Client[Client]
    Broker[broker]
    Job[orchestrate job]
    Status[Job Status / Result]

    Client -->|workflow| Broker
    Broker -->|async submit| Job
    Job -->|status URL| Broker
    Broker -->|status URL| Client

    Client -. later .-> Status
    Job -. updates .-> Status
```

The broker:

1. inspects the workflow;
2. selects a site;
3. submits `orchestrate`;
4. returns the actual job/status response.

It does **not** maintain a second broker-side copy of the job state.

The returned status URL belongs to the real processing job, regardless of whether it runs locally or remotely.

---

# Future improvement: advertise processing in STAC

The federation can work with the **existing ESGF-NG STAC catalog**.

> **No STAC changes are required to implement Rook federation.**

As a future improvement, STAC could explicitly advertise that processing is supported for a dataset.

```mermaid
flowchart LR
    Item[STAC Dataset]
    Capability[Processing Available]
    Service[Global Rook Endpoint]
    Broker[Rook Broker]

    Item --> Capability
    Capability --> Service
    Service --> Broker
```

This would mainly improve **discovery and user experience**:

* An ESGF portal could immediately offer a **Process** action.
* STAC advertises processing capability, not current runtime availability.
* This is similar to advertising a data-node URL without guaranteeing that the node is currently online.
* Runtime availability remains the responsibility of Rook `health/status` and the broker.
* The global load-balanced Rook endpoint can be advertised as the ESGF processing service.

A first version could be as simple as:

```json
{
  "esgf:processing": true
}
```

Alternatively, the processing service could be advertised through an appropriate STAC service link.

The representation can later evolve into richer processing/service metadata.

The important point remains:

> **Processing metadata in STAC is an optional discovery and UX improvement, not a requirement for Rook federation.**

---

# Summary

```mermaid
flowchart LR
    Publish[ESGF Publication]
    Kafka[Kafka]
    Index[Local ESGF Index]
    Broker[Rook Broker]
    Process[Rook Processing]

    Publish --> Kafka
    Kafka --> Index
    Index --> Broker
    Broker --> Process
```

The proposal builds largely on infrastructure that already exists:

* **Rook** provides server-side climate-data processing.
* **orchestrate** already executes JSON workflows.
* **AWS LB** already provides a highly available entry point.
* **Kafka** already distributes ESGF-NG publication events.
* **STAC** already describes datasets and their locations.
* **PostgreSQL** provides fast local dataset resolution.
* The new **broker** adds dataset-aware federation and delegation.

The result is a decentralized processing service that can use the **full distributed ESGF-NG data holdings** without requiring identical replicas at every processing site.
