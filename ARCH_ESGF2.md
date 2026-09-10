## Rook federation for ESGF-NG

Rook remains a **single software deployment** serving multiple use cases such as CDS and ESGF-NG.

For ESGF-NG, each site maintains a **local PostgreSQL inventory** of datasets and assets available in its local data pool. The inventory is updated from the ESGF-NG Kafka stream carrying STAC records and patches.

Normal processing requests use a **logical dataset ID**. Rook resolves the dataset to local NetCDF files or aggregations through a generic dataset resolver.

If the dataset is missing from the local inventory, Rook may optionally query the **global ESGF-NG STAC catalog**. If STAC confirms that the dataset is available at the local site, Rook can reconstruct the local source information and optionally repair the local inventory. Remote HTTP assets should not silently become a processing fallback.

For federation, every Rook instance exposes the same lightweight **broker WPS process**. The existing AWS load balancer can send a request to any available Rook instance. The broker then either processes locally or delegates the request to another Rook site that has the dataset and is currently available.

Dataset placement and service availability stay separate:

* **STAC** describes where datasets are available.
* **health/status processes** describe whether a Rook site is currently usable.
* The **broker** combines both and selects a suitable execution site.

Delegated requests go directly to the target processing process, not to the target broker.

## High-level overview

```mermaid
flowchart LR
    Client[Client / ESGF Portal]
    LB[AWS Load Balancer]
    Rooks[Rook Federation<br/>DKRZ · IPSL · CEDA]
    Data[Local ESGF Data Pools]
    STAC[Global ESGF-NG STAC]

    Client --> LB
    LB --> Rooks
    Rooks --> Data
    Rooks --> STAC
```

The AWS load balancer provides a stable entry point. The intelligence for dataset-aware routing remains inside the identical Rook deployments.

## Local dataset resolution

```mermaid
flowchart LR
    Request[Dataset ID]
    Resolver[Dataset Resolver]
    DB[Local PostgreSQL Inventory]
    Pool[Local Data Pool]
    STAC[Global STAC Fallback]

    Request --> Resolver
    Resolver --> DB
    DB --> Pool

    Resolver -. local miss .-> STAC
    STAC -. local representation found .-> Resolver
```

The local inventory is the normal resolution path. STAC is an optional fallback when the local inventory is temporarily out of sync.

## Keeping the local inventory up to date

```mermaid
flowchart LR
    Nodes[ESGF Data Nodes]
    Kafka[Kafka<br/>STAC records + patches]
    DB[Local PostgreSQL Inventory]
    Rook[Rook Dataset Resolver]

    Nodes --> Kafka
    Kafka --> DB
    DB --> Rook
```

Each Rook site maintains its own local view of the ESGF publication state.

## Federated request routing

```mermaid
flowchart LR
    LB[AWS Load Balancer]
    Entry[Any Rook Broker]
    STAC[Global STAC]
    Health[Remote Rook<br/>health / status]
    Local[Local Processing]
    Remote[Remote Rook Process]

    LB --> Entry

    Entry --> STAC
    Entry --> Health

    Entry --> Local
    Entry --> Remote
```

The load balancer does not need to understand dataset placement. It only needs to deliver the request to an available Rook instance.

## Processing decision

```mermaid
flowchart TD
    A[Broker receives request]
    B{Dataset available locally?}

    A --> B

    B -- Yes --> C[Execute locally]
    C --> Z[Return result]

    B -- No --> D[Query global STAC]
    D --> E[Find sites holding dataset]
    E --> F[Check Rook health / status]
    F --> G{Healthy candidate?}

    G -- Yes --> H[Select site]
    H --> I[Call target process directly]
    I --> Z

    G -- No --> X[Return unavailable]
```

This keeps the architecture decentralized: there is **no dedicated central broker service**. Every Rook installation contains the same resolution and federation logic, while the AWS load balancer only provides the stable public entry point.
