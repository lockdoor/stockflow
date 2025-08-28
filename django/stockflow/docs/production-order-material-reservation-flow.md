# Production Order Material Reservation Flow


```mermaid
flowchart TD
    A[Draft] -->|Submit| B[Created]
    B -->|Start Production| C[In Progress]
    C -->|Pause| D[Paused]
    D -->|Resume| C
    C -->|Complete| E[Completed]
    B -->|Cancel| F[Cancelled]
    C -->|Cancel| F
    D -->|Cancel| F

    %% Reservation/Consumption logic
    B -.->|Reserve material by BOM| R[Material Reservation]
    C -.->|Consume material within reservation| S[Stock Movement]
    C -.->|Consume more than reserved| S2[Stock Movement Over Reservation]
    E -.->|Release unused reservation| X[Release Reservation]
    F -.->|Release all reservation| X

    %% Notes
    B:::reserve
    C:::consume
    S2:::overconsume
    E:::release
    F:::release

    classDef reserve fill:#e0f7fa,stroke:#00796b,stroke-width:2px;
    classDef consume fill:#fff3e0,stroke:#f57c00,stroke-width:2px;
    classDef overconsume fill:#ffebee,stroke:#d32f2f,stroke-width:2px,stroke-dasharray: 5 2;
    classDef release fill:#fce4ec,stroke:#c2185b,stroke-width:2px;
```

> หมายเหตุ:
> - Created: จองวัสดุตาม BOM
> - In Progress: เบิกวัสดุจริง (เบิกเท่าไหร่ก็ได้)
> - หากเบิกเกินที่จอง จะลด stock จริงโดยตรง (Stock Movement (Over Reservation))
> - Completed/Cancelled: คืนวัสดุที่จองไว้ (ถ้ามี)
