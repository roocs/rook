## Rook federation for ESGF-NG

Rook should remain a **single software deployment** that can serve multiple use cases such as CDS and ESGF-NG.

For ESGF-NG, each Rook site maintains a **local PostgreSQL inventory** of datasets and assets available in its local data pool. This inventory is updated from the ESGF-NG Kafka stream carrying STAC records and patches.

Normal processing requests use a **logical dataset ID**, not a list of file URLs. Rook resolves the dataset to local NetCDF files or aggregations through a generic dataset resolver.

If a dataset is missing from the local inventory, Rook may optionally query the **global ESGF-NG STAC catalog**. If STAC confirms that the dataset is available at the local site, Rook can reconstruct the local source information and optionally repair the local inventory. Remote HTTP assets should not be used silently as a fallback.

For federated processing, every Rook instance exposes the same lightweight **broker WPS process**. The public ESGF endpoint can use the existing AWS load balancer to send a request to any available Rook instance. The broker then decides whether to process the request locally or delegate it to another Rook site that has the dataset and is currently available.

Dataset placement and service health remain separate:

* **STAC** tells Rook where a dataset is available.
* **health/status processes** tell Rook which sites are currently ready for processing.
* The **broker** combines both pieces of information and selects a suitable site.

Delegated requests are sent directly to the target processing process, not to the target broker, which prevents routing loops.

### Architecture overview

```mermaid
flowchart TD
    Client[Client / ESGF Portal]
    LB[AWS Load Balancer]

    Client --> LB

    LB --> DE[Rook DKRZ]
    LB --> FR[Rook IPSL]
    LB --> UK[Rook CEDA]

    STAC[Global ESGF-NG STAC Catalog]

    DE --> DEB[Broker WPS Process]
    FR --> FRB[Broker WPS Process]
    UK --> UKB[Broker WPS Process]

    DEB --> STAC
    FRB --> STAC
    UKB --> STAC

    DE --> DEDB[Local PostgreSQL Inventory]
    FR --> FRDB[Local PostgreSQL Inventory]
    UK --> UKDB[Local PostgreSQL Inventory]

    DEDB --> DEPOOL[DKRZ Data Pool]
    FRDB --> FRPOOL[IPSL Data Pool]
    UKDB --> UKPOOL[CEDA Data Pool]

    KAFKA[ESGF-NG Kafka STAC Stream]

    KAFKA --> DEDB
    KAFKA --> FRDB
    KAFKA --> UKDB
```

### Processing flow

```mermaid
flowchart TD
    A[Broker receives request]
    B{Dataset available locally?}
    C[Execute process locally]
    D[Query global STAC]
    E{Which sites have the dataset?}
    F[Check health/status of candidate Rook sites]
    G{Healthy candidate available?}
    H[Select suitable site]
    I[Delegate directly to target process]
    J[Return result]
    K[Fail: dataset unavailable for processing]

    A --> B

    B -- Yes --> C
    C --> J

    B -- No --> D
    D --> E
    E --> F
    F --> G

    G -- Yes --> H
    H --> I
    I --> J

    G -- No --> K
```

This keeps the architecture decentralized: there is **no dedicated central broker service**. Every Rook deployment contains the same federation logic, while the AWS load balancer only provides a stable and highly available entry point.
