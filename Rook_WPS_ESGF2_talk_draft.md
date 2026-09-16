# Rook/WPS for ESGF2

Processing climate data close to the archive

## Talk outline — 10 minutes

| Slide | Topic | Time |
| --- | --- | ---: |
| 1 | Why provide a Compute Node? | 1:00 |
| 2 | Processing capabilities | 1:00 |
| 3 | Rook in the Copernicus CDS today | 1:15 |
| 4 | Planned ESGF2 broker | 2:00 |
| 5 | Notebook: today and proposed broker | 2:00 |
| 6 | Deployment today | 1:00 |
| 7 | Discovery, AAI and next steps | 1:45 |

The horizontal rules separate slides. HTML comments contain presenter notes.

---

## 1. Why provide a Compute Node?

**Example: How does regional mean temperature change over time?**

- Select only the region and period needed.
- Process the data close to the archive.
- Retrieve the small, usable result.
- Integrate processing into scientific workflows and applications.

```mermaid
flowchart LR
    User["User or application"] -->|"Processing request"| Rook["Rook/WPS"]
    Archive[("Climate archive")] --> Rook
    Rook -->|"Requested result"| User
```

<!-- 1:00. A Compute Node is an additional access route for ESGF users. It
complements file download: users can still retrieve complete files when that is
what they need. Avoid implying complete CMIP7 coverage today. -->

---

## 2. Processing capabilities

- **Subset:** select space, time and levels.
- **Average:** reduce data for an analysis.
- **Regrid:** transform data to a target grid.
- **Orchestrate:** combine operations in one workflow.
- **Woodpecker:** apply known fixes to datasets with compliance issues.

```mermaid
flowchart LR
    Request["Workflow request"] --> Subset["Subset"]
    Subset --> Average["Average"]
    Average --> Result["Regional time series"]
```

<!-- 1:00. Rook exposes the processing API; clisops provides the main data
operations. Mention Woodpecker by name and purpose so that people recognize it.
Do not explain its internal architecture. -->

---

## 3. Rook in the Copernicus CDS today

**Operational today**

- CDS submits workflows to Rook.
- DKRZ and IPSL provide equivalent data and processing.
- A load balancer distributes requests between the sites.
- Each site processes its local data.

```mermaid
flowchart LR
    CDS["Copernicus CDS"] --> LB["Load balancer"]
    LB --> DE["Rook at DKRZ"]
    LB --> FR["Rook at IPSL"]
    DEData[("Local data")] --> DE
    FRData[("Local data")] --> FR
```

<!-- 1:15. This is the existing model for supported CDS datasets. Equivalent
holdings make both sites interchangeable. ESGF2 needs smarter routing because
participating sites will not necessarily hold the same datasets. -->

---

## 4. Planned ESGF2 broker

**Route processing to a site that holds the requested dataset**

- Add a `broker` process to Rook.
- Accept the same workflow document used by `orchestrate`.
- Select a site using dataset placement and service availability.
- Submit the processing job asynchronously.
- Return the selected site's job-status URL directly.

```mermaid
flowchart LR
    Kafka["ESGF2 Kafka events"] --> Piddi["Piddiplatsch"]
    Piddi --> Index[("Local inventory")]
    Client["Client"] -->|"Dataset + workflow"| Broker["Rook broker"]
    Broker --> Index
    Broker -->|"Delegate"| Site["Selected Rook site"]
    Site -->|"Job URL"| Client
```

<!-- 2:00. Planned architecture. Kafka publication, update and deletion events
keep a local PostgreSQL inventory current through a Piddiplatsch plugin. Kafka
is not part of the synchronous request path. The selected site may run a single
process or an orchestrated workflow. The broker is only a delegation layer: it
does not mirror remote job state and must not create broker-to-broker loops. -->

---

## 5. Notebook: today and proposed broker

**Current implementation — executable with Rooki**

```python
from rooki.client import Rooki

rook = Rooki("https://rook.dkrz.de/wps", mode="async")

response = rook.subset(
    collection=(
        "c3s-cmip6.CMIP.IPSL.IPSL-CM6A-LR.historical."
        "r1i1p1f1.Amon.rlds.gr.v20180803"
    ),
    time="1985-01-01/2014-12-30",
    area="-10,35,30,70",
)

response.ok
response.download_urls()
dataset = response.datasets()[0]
```

**Proposed ESGF2 broker — same user intent, automatic site selection**

```python
workflow = {
    "process": "subset",
    "inputs": {
        "collection": "<same-dataset-id>",
        "time": "1985-01-01/2014-12-30",
        "area": "-10,35,30,70",
    },
}

job = rook.broker(workflow=workflow)  # proposed API
job.status_url
```

**Today the client selects the service. The broker will select the site.**

<!-- 2:00. Run only the first example. It uses the dataset from the documented
Rooki example; verify the endpoint and dataset before the talk and prepare the
completed result as a fallback. response.download_urls() and response.datasets() are part
of the current Rooki interface. The broker call is deliberately labelled as a
proposed API sketch. Its exact Python signature is not implemented or fixed yet.
For a multi-step subset/average example, pass an orchestrate-style workflow
document instead; the architectural point remains the same. -->

---

## 6. Deployment today

**Current operational deployment**

- **Ansible** provisions Rook/WPS on **VMs**.
- **Slurm** schedules processing jobs.
- Jobs access data available at the site.
- The same model can be deployed at further ESGF2 sites.

```mermaid
flowchart LR
    Client["Client"] --> VM["Rook/WPS VM"]
    VM --> Slurm["Slurm"]
    Slurm --> Job["Processing job"]
    Data[("Site data")] --> Job
```

<!-- 1:00. Describe only the current deployment. Docker, Kubernetes and Helm
are an alternative deployment path to prepare during ESGF2, not the present
production architecture. -->

---

## 7. Discovery, AAI and next steps

- **STAC:** optionally advertise processing with a small flag or service link.
- **Portal:** MetaGrid or another client discovers the endpoint through STAC.
- **AAI proxy:** protect Rook and delegate identity with OAuth2/Keycloak.
- **Next:** validate CMIP7 workflows and prepare a container deployment.

```mermaid
flowchart TD
    STAC["STAC catalogue"] -->|"Optional processing link"| Portal["MetaGrid or client"]
    Portal --> Proxy["AAI proxy"]
    Keycloak["OAuth2 / Keycloak"] <--> Proxy
    Proxy --> Broker["Rook broker"]
```

**STAC provides discovery. AAI protects access. Rook provides processing.**

<!-- 1:45. Rook's integration boundary is the processing API and optional STAC
information. Portal integration belongs to MetaGrid or its successor. A small
processing indicator or service link is sufficient and can be added later via
an ESGF2 Kafka update; do not propose an exact STAC schema in this talk.

AAI is a required layer between clients and the processing services, especially
when a portal acts on behalf of a user. It does not start from scratch. Earlier
deployments used an AAI proxy with OAuth2 delegation to Keycloak. CEDA developed
an Nginx/Python proxy. Twitcher offers more OGC-aware functionality, including
service registration, OAuth2 and certificate support, and is actively used by
Ouranos in Canada. ESGF2 still needs to review these components and define the
required user-to-service and service-to-service delegation patterns. Do not
imply that a proxy has already been selected. -->

<!-- Preparation references:

- Local broker/CDS design: ARCH_ESGF2.md
- Process catalogue: docs/source/processes.rst
- Woodpecker configuration: docs/source/configuration.rst
- Twitcher: https://github.com/bird-house/twitcher/blob/master/README.rst
-->
