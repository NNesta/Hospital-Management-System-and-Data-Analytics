# User guide

One page per role at **Ubuzima Referral Hospital**. Sign in at
<http://127.0.0.1:8000/accounts/login/>. After running `seed_data`, every demo
account uses the password **`Ubuzima@2026`**.

Common to everyone:

- The **sidebar** only shows the pages your role may use. Opening any other
  page directly gives a *403 Access denied* page.
- Use the **sun/moon icon** in the top bar to switch between light, dark and
  automatic colour mode.
- **Sign out** from the menu under your name (top right).
- Every list has a **search box** (name, code, phone…) and pages of 10 rows.
- Money is shown in Rwandan francs (RWF).

---

## Receptionist: `receptionist` (Aline Uwase)

You register patients and manage the appointment book.

1. **Register a patient**: *Patients → Register patient*. Enter the name,
   gender, date of birth, phone (+250 7xx…), district and sector/village.
   The national ID (Indangamuntu) is 16 digits; leave it empty for children.
   If the patient is insured (Mutuelle de Santé, RSSB, MMI…), the membership
   number is required. The system gives the patient a code such as `PAT-00301`.
2. **Book an appointment**: open the patient and click **Book appointment**
   (the patient is filled in), choose a doctor, date and 30-minute slot
   (08:00–16:30) and the reason.
   - A slot that is already taken for that doctor is refused with a clear message.
   - Past dates and doctors marked *unavailable* (on leave) are refused.
3. **Reschedule / cancel / no-show**: open the appointment. While it is
   *Scheduled* you can **Reschedule**, **Cancel** (after a confirmation page) or
   **Mark as no-show**.
4. You can see invoices (to answer patient questions) but not change them.

## Doctor: `doctor` (Dr. Eric Mugisha, Internal Medicine)

You only see your own appointments and the patients you treat.

1. *Appointments* lists **your** visits. Filter by *Today* to see your clinic list.
2. Click the green **clipboard button** (or *Start consultation*) on a
   scheduled visit. Write the symptoms, diagnosis, treatment plan and an
   optional follow-up date, then **Save and complete visit**. The appointment
   becomes *Completed*. The patient's recent history is shown on the right.
3. **Write a prescription**: on the completed visit click **Write
   prescription**. Add one row per medicine (dosage, frequency, days, quantity);
   use **Add row** for more. **Send to pharmacy**. You can edit or delete it
   while it is still *Pending*.
4. *Medical records* shows the history of your patients. Only the author of
   a record can edit it.
5. Your dashboard shows **your own** numbers: your patients, your visits
   today, revenue from your consultations.

## Pharmacist: `pharmacist` (Josiane Ingabire)

You manage stock and dispense prescriptions.

1. *Prescriptions* is your **dispensing queue**. Filter by *Pending*.
2. Open a prescription: each medicine shows the stock left. Click
   **Dispense & deduct stock**. Stock goes down for every line at once; if
   any medicine is short, nothing is deducted and you see which one.
3. After dispensing, a **Low stock** warning appears for any medicine that fell
   to its reorder level.
4. *Medicines & stock*: medicines at or below the reorder level have a **red
   badge**; tick *Low stock only* to see them. Use **Edit / restock** to update
   quantities. A medicine that was ever prescribed cannot be deleted.
5. Your dashboard shows the pharmacy section first (top medicines, low stock).

## Accountant: `accountant` (Patrick Habimana)

You bill completed visits and record payments.

1. *Visits to bill* lists completed consultations without an invoice. Click
   **Generate invoice**: it adds the doctor's consultation fee and every
   **dispensed** medicine, with an invoice number like `INV-2026-00951`.
2. Open the invoice and click **Record payment**. Choose the method:
   - **Mobile money**: enter the MTN MoMo / Airtel Money transaction ID.
   - **Insurance**: enter the claim number (Mutuelle pays 90%, RSSB/MMI 85%;
     the patient pays the rest at the cashier).
   - **Cash** or **Card**.
   The amount cannot be more than the balance. The invoice status updates
   automatically: *Unpaid → Partially paid → Paid*.
3. **Printable invoice** opens the print layout with the hospital's TIN; use
   *Print* (the sidebar and buttons are hidden on paper).
4. *Manual invoice* creates an invoice with free lines (e.g. lab fees).
   Invoices can be edited only while *Unpaid*.
5. *Reports*: filter by dates, department, doctor or status and **Download
   CSV** for Excel. Your dashboard shows finance first.

## Admin: `admin` (Jean Paul Kamanzi)

You see everything and manage the hospital structure.

1. **Users & roles**: create staff logins, change roles, reset passwords
   and **deactivate** people who leave (their history is kept).
2. **Departments**: add or edit departments. A department can only be
   deleted when it has no doctors.
3. **Doctors**: first create a user with the *Doctor* role, then *New doctor*
   to add the department, RMDC licence number and consultation fee. Untick
   *Is available* when a doctor is on leave; *Deactivate* when they leave.
4. Admins can also delete patients without history, payments and unpaid
   invoices without payments.
5. **Django admin** (sidebar) is a backup tool for fixing data; daily work
   happens in the AdminLTE pages.
