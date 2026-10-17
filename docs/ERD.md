# Entity–relationship diagram

12 tables in 6 apps, using all three Django relationship types. GitHub renders
the diagram below; to export an image for the report, paste
[`erd.dbml`](erd.dbml) into <https://dbdiagram.io> and use **Export → PNG**.

```mermaid
erDiagram
    accounts_user ||--o| staff_doctor : "is (1:1)"
    staff_department ||--o{ staff_doctor : "employs"
    patients_patient ||--o{ appointments_appointment : "books"
    staff_doctor ||--o{ appointments_appointment : "sees"
    appointments_appointment ||--o| appointments_medicalrecord : "produces (1:1)"
    appointments_medicalrecord ||--o{ pharmacy_prescription : "leads to"
    pharmacy_prescription ||--|{ pharmacy_prescriptionitem : "contains"
    pharmacy_medicine ||--o{ pharmacy_prescriptionitem : "is prescribed in"
    patients_patient ||--o{ billing_invoice : "is billed"
    appointments_appointment ||--o| billing_invoice : "is invoiced by (1:0..1)"
    billing_invoice ||--|{ billing_invoiceitem : "lists"
    pharmacy_medicine ||--o{ billing_invoiceitem : "is charged in"
    billing_invoice ||--o{ billing_payment : "is settled by"

    accounts_user {
        bigint id PK
        varchar username UK
        varchar first_name
        varchar last_name
        varchar email
        varchar phone
        varchar role "ADMIN | RECEPTIONIST | DOCTOR | PHARMACIST | ACCOUNTANT"
    }
    staff_department {
        bigint id PK
        varchar name UK
        text description
        varchar location
        datetime created_at
    }
    staff_doctor {
        bigint id PK
        bigint user_id FK "UNIQUE, PROTECT"
        bigint department_id FK "PROTECT"
        varchar specialization
        varchar license_number UK "RMDC licence"
        varchar phone
        decimal consultation_fee "CHECK > 0"
        bool is_available
        bool is_active
    }
    patients_patient {
        bigint id PK
        varchar patient_code UK "PAT-00001"
        varchar first_name
        varchar last_name
        char gender
        date date_of_birth
        varchar blood_group
        varchar phone
        varchar district "one of Rwanda's 30"
        varchar address
        varchar national_id UK "16 digits, nullable"
        varchar insurance_provider "Mutuelle, RSSB, MMI..."
        varchar insurance_number
        varchar emergency_contact_name
        varchar emergency_contact_phone
        bigint registered_by_id FK "SET_NULL"
        datetime created_at
    }
    appointments_appointment {
        bigint id PK
        bigint patient_id FK "PROTECT"
        bigint doctor_id FK "PROTECT"
        date appointment_date "indexed"
        time appointment_time
        varchar reason
        varchar status "SCHEDULED | COMPLETED | CANCELLED | NO_SHOW (indexed)"
        bigint created_by_id FK "SET_NULL"
        datetime created_at
    }
    appointments_medicalrecord {
        bigint id PK
        bigint appointment_id FK "UNIQUE, PROTECT"
        text symptoms
        varchar diagnosis
        text treatment_plan
        text notes
        date follow_up_date
        datetime created_at
    }
    pharmacy_medicine {
        bigint id PK
        varchar name UK
        varchar generic_name
        varchar category
        decimal unit_price "CHECK > 0"
        int stock_quantity "CHECK >= 0"
        int reorder_level "CHECK >= 0"
        date expiry_date
    }
    pharmacy_prescription {
        bigint id PK
        bigint medical_record_id FK "PROTECT"
        datetime issued_at
        text notes
        varchar status "PENDING | DISPENSED (indexed)"
        datetime dispensed_at
        bigint dispensed_by_id FK "SET_NULL"
    }
    pharmacy_prescriptionitem {
        bigint id PK
        bigint prescription_id FK "CASCADE"
        bigint medicine_id FK "PROTECT"
        varchar dosage
        varchar frequency
        int duration_days
        int quantity "CHECK > 0"
    }
    billing_invoice {
        bigint id PK
        varchar invoice_number UK "INV-2026-00001"
        bigint patient_id FK "PROTECT"
        bigint appointment_id FK "UNIQUE, nullable, PROTECT"
        date issue_date
        date due_date
        varchar status "UNPAID | PARTIALLY_PAID | PAID (indexed)"
        bigint created_by_id FK "SET_NULL"
    }
    billing_invoiceitem {
        bigint id PK
        bigint invoice_id FK "CASCADE"
        varchar item_type "CONSULTATION | MEDICINE | OTHER"
        varchar description
        int quantity "CHECK > 0"
        decimal unit_price "CHECK > 0"
        bigint medicine_id FK "nullable, PROTECT"
    }
    billing_payment {
        bigint id PK
        bigint invoice_id FK "PROTECT"
        decimal amount "CHECK > 0"
        varchar method "CASH | MOBILE_MONEY | CARD | INSURANCE"
        varchar reference "MoMo ID, receipt, claim no."
        datetime paid_at "indexed"
        bigint received_by_id FK "SET_NULL"
    }
```

`created_by`, `registered_by`, `dispensed_by` and `received_by` also point to
`accounts_user` (audit fields, `SET_NULL`); they are left off the diagram to
keep it readable.

## Relationship types to point out in the demo

| Type | Example | Django field |
|---|---|---|
| One-to-one | User ↔ Doctor | `OneToOneField` |
| One-to-one | Appointment ↔ MedicalRecord | `OneToOneField` |
| One-to-one (optional) | Appointment ↔ Invoice | `OneToOneField(null=True, blank=True)` |
| One-to-many | Department → Doctors, Patient → Appointments, Invoice → Payments | `ForeignKey` |
| Many-to-many with extra data | Prescription ↔ Medicine via PrescriptionItem (dosage, quantity) | `ManyToManyField(through="PrescriptionItem")` |

## Constraints

- `unique_doctor_slot`: (doctor, appointment_date, appointment_time) blocks double booking.
- `unique_medicine_per_prescription`: a medicine appears once per prescription.
- `CHECK` constraints: payment amount, unit prices, quantities and consultation fee must be > 0.
- `PROTECT` keeps history (a prescribed medicine or a patient with visits cannot be deleted);
  `CASCADE` only for child rows (PrescriptionItem, InvoiceItem); `SET_NULL` for audit fields.
