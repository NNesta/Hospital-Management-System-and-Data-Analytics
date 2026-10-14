"""python manage.py seed_data [--reset] [--seed 2026]

Creates, in order: staff logins (one demo login per role), 6 departments,
15 doctors, 40 medicines, 300 patients and about 1,200 appointments spread
over the last 12 months, then medical records for completed visits,
prescriptions, invoices and payments with a realistic mix of paid, partially
paid and unpaid bills.

Everything is fictional but Rwandan: Kinyarwanda names, Kigali sectors,
+250 phone numbers, 16-digit national IDs, Mutuelle de Santé / RSSB co-pays,
MTN MoMo and Airtel Money payments, prices in RWF.
"""

import datetime as dt
import random
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from faker import Faker

from accounts.models import Role, User
from analytics.queries import last_12_months
from appointments.models import TIME_SLOTS, Appointment, MedicalRecord
from billing.models import Invoice, InvoiceItem, Payment
from patients.models import Patient
from pharmacy.models import Medicine, Prescription, PrescriptionItem
from staff.models import Department, Doctor

from . import _rwanda_data as rw

WEEKDAY_WEIGHT = {0: 1.15, 1: 1.0, 2: 1.0, 3: 1.0, 4: 0.95, 5: 0.45, 6: 0.15}  # Mon..Sun
AGE_MIX = [((0, 4), 12), ((5, 14), 15), ((15, 24), 18), ((25, 44), 30), ((45, 64), 17), ((65, 85), 8)]
BLOOD_MIX = [("O+", 45), ("A+", 24), ("B+", 19), ("AB+", 4), ("O-", 2), ("A-", 1), ("B-", 1), ("UNK", 4)]
BATCH = 500


def next_id(model):
    return (model.objects.aggregate(m=Max("id"))["m"] or 0) + 1


def money(value) -> Decimal:
    return Decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


class Command(BaseCommand):
    help = "Fill the database with 12 months of realistic Rwandan demo data."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete existing hospital data and demo users first.")
        parser.add_argument("--seed", type=int, default=2026, help="Random seed (same seed = same data).")
        parser.add_argument("--patients", type=int, default=300)
        parser.add_argument("--appointments", type=int, default=1200)

    # ------------------------------------------------------------------------------------------

    def handle(self, *args, **options):
        self.rng = random.Random(options["seed"])
        Faker.seed(options["seed"])
        self.fake = Faker()
        self.today = timezone.localdate()
        self.now = timezone.localtime()

        if Patient.objects.exists() or Department.objects.exists():
            if not options["reset"]:
                raise CommandError("The database already has data. Run `python manage.py seed_data --reset` to wipe and reseed.")
            self.wipe()

        with transaction.atomic():
            self.create_staff()
            self.create_departments_and_doctors()
            self.create_medicines()
            self.create_patients(options["patients"])
            self.create_appointments(options["appointments"])
            self.create_records_and_prescriptions()
            self.create_invoices_and_payments()

        self.report()

    # --- helpers --------------------------------------------------------------------------------

    def weighted(self, pairs):
        values, weights = zip(*pairs)
        return self.rng.choices(values, weights=weights, k=1)[0]

    def aware(self, day: dt.date, time: dt.time) -> dt.datetime:
        return timezone.make_aware(dt.datetime.combine(day, time))

    def phone(self) -> str:
        prefix = self.weighted([("78", 50), ("79", 15), ("72", 25), ("73", 10)])
        return f"+250 {prefix}{self.rng.randint(0, 9)} {self.rng.randint(0, 999):03d} {self.rng.randint(0, 999):03d}"

    def national_id(self, birth_year: int, gender: str) -> str:
        while True:
            value = f"1{birth_year}{'8' if gender == 'M' else '7'}{self.fake.numerify('#######')}0{self.fake.numerify('##')}"
            if value not in self.used_nids:
                self.used_nids.add(value)
                return value

    def history_days(self):
        """Every day from 13 months ago to yesterday, with a weight that grows
        through the year and drops at weekends. The extra 13th month means the
        first month on the 12-month charts already has a normal workload."""
        first_day = last_12_months(self.today)[0] - dt.timedelta(days=31)
        days = [first_day + dt.timedelta(days=i) for i in range((self.today - first_day).days)]
        weights = [self.month_growth(d) * WEEKDAY_WEIGHT[d.weekday()] for d in days]
        return days, weights

    def month_growth(self, day: dt.date) -> float:
        """Intake grows through the year: 0.7x a year ago up to 1.3x this month."""
        months_ago = (self.today.year - day.year) * 12 + self.today.month - day.month
        return 0.7 + 0.6 * (11 - min(months_ago, 11)) / 11

    def free_slot(self, doctor_id, day, after: dt.time | None = None):
        slots = [t for t in TIME_SLOTS if (doctor_id, day, t) not in self.used_slots and (after is None or t >= after)]
        if not slots:
            return None
        slot = self.rng.choice(slots)
        self.used_slots.add((doctor_id, day, slot))
        return slot

    # --- wipe -----------------------------------------------------------------------------------

    def wipe(self):
        self.stdout.write("Deleting existing hospital data…")
        for model in [Payment, InvoiceItem, Invoice, PrescriptionItem, Prescription, MedicalRecord,
                      Appointment, Patient, Medicine, Doctor, Department]:
            model.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

    # --- staff ----------------------------------------------------------------------------------

    def create_staff(self):
        password = make_password(rw.DEMO_PASSWORD)  # hash once; every demo login shares it
        self.users_by_role = defaultdict(list)
        joined = timezone.now() - dt.timedelta(days=900)

        def upsert(username, first, last, role, superuser=False):
            user, _ = User.objects.update_or_create(
                username=username,
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "role": role,
                    "email": f"{first.split()[0].lower()}.{last.lower()}@ubuzima-hospital.rw",
                    "phone": self.phone(),
                    "password": password,
                    "is_active": True,
                    "is_staff": superuser,
                    "is_superuser": superuser,
                    "date_joined": joined + dt.timedelta(days=self.rng.randint(0, 600)),
                },
            )
            self.users_by_role[role].append(user)
            return user

        for username, first, last, role, superuser in rw.STAFF:
            upsert(username, first, last, role, superuser)
        self.doctor_users = {
            username: upsert(username, first, last, Role.DOCTOR) for username, first, last, *_ in rw.DOCTORS
        }

    # --- departments and doctors -------------------------------------------------------------------

    def create_departments_and_doctors(self):
        self.departments = {}
        created = timezone.now() - dt.timedelta(days=800)
        for spec in rw.DEPARTMENTS:
            self.departments[spec["key"]] = Department.objects.create(
                name=spec["name"], location=spec["location"], description=spec["description"], created_at=created
            )
        self.doctors_by_dept = defaultdict(list)
        self.doctors = []
        for username, _first, _last, _gender, dept, specialization, licence, fee, available in rw.DOCTORS:
            doctor = Doctor.objects.create(
                user=self.doctor_users[username],
                department=self.departments[dept],
                specialization=specialization,
                license_number=licence,
                phone=self.doctor_users[username].phone,
                consultation_fee=Decimal(fee),
                is_available=available,
                created_at=created,
            )
            doctor.dept_key = dept
            self.doctors.append(doctor)
            self.doctors_by_dept[dept].append(doctor)
        # One doctor is on leave: no appointments in the last six weeks or from now on.
        self.leave_start = self.today - dt.timedelta(days=42)

    def doctors_for(self, dept, day):
        return [d for d in self.doctors_by_dept[dept] if d.is_available or day < self.leave_start]

    # --- medicines ---------------------------------------------------------------------------------

    def create_medicines(self):
        start = next_id(Medicine)
        created = timezone.now() - dt.timedelta(days=400)
        rows = []
        for offset, (name, generic, category, price, reorder, stock) in enumerate(rw.MEDICINES):
            rows.append(
                Medicine(
                    id=start + offset,
                    name=name,
                    generic_name=generic,
                    category=category,
                    unit_price=Decimal(price),
                    stock_quantity=stock,
                    reorder_level=reorder,
                    expiry_date=self.today + dt.timedelta(days=self.rng.randint(120, 900)),
                    created_at=created,
                )
            )
        Medicine.objects.bulk_create(rows)
        self.medicines = {m.name: m for m in rows}

    # --- patients ----------------------------------------------------------------------------------

    def create_patients(self, count):
        self.used_nids = set()
        start = next_id(Patient)
        receptionists = self.users_by_role[Role.RECEPTIONIST]

        # A quarter are long-standing patients registered 1-3 years ago; the rest
        # registered during the history window (growing, fewer at weekends).
        days, weights = self.history_days()
        existing = count // 4
        reg_days = sorted(
            [self.today - dt.timedelta(days=self.rng.randint(400, 1100)) for _ in range(existing)]
            + self.rng.choices(days, weights=weights, k=count - existing)
        )

        self.patients = []
        for offset, reg_day in enumerate(reg_days):
            gender = "F" if self.rng.random() < 0.54 else "M"
            low, high = self.weighted(AGE_MIX)
            age = self.rng.randint(low, high)
            dob = self.today - dt.timedelta(days=age * 365 + self.rng.randint(0, 364))
            child = age < 15
            if child:
                given = self.rng.choice(rw.CHILD_FEMALE_GIVEN if gender == "F" else rw.CHILD_MALE_GIVEN)
            else:
                given = self.rng.choice(rw.FEMALE_GIVEN if gender == "F" else rw.MALE_GIVEN)
            family = self.rng.choice(rw.FEMALE_KINYARWANDA if gender == "F" else rw.MALE_KINYARWANDA)
            district = self.weighted(rw.DISTRICT_WEIGHTS.items())
            insurance = self.weighted(rw.INSURANCE_MIX)

            contact_gender = self.rng.choice("MF")
            contact_name = (
                f"{self.rng.choice(rw.FEMALE_GIVEN if contact_gender == 'F' else rw.MALE_GIVEN)} "
                f"{self.rng.choice(rw.FEMALE_KINYARWANDA if contact_gender == 'F' else rw.MALE_KINYARWANDA)}"
            )
            relation = self.rng.choice(["mother", "father"]) if child else self.rng.choice(rw.RELATIONS)
            contact_phone = self.phone()

            registered_at = self.aware(reg_day, dt.time(self.rng.randint(7, 15), self.rng.choice([0, 10, 20, 30, 40, 50])))
            pk = start + offset
            patient = Patient(
                id=pk,
                patient_code=f"PAT-{pk:05d}",
                first_name=given,
                last_name=family,
                gender=gender,
                date_of_birth=dob,
                blood_group=self.weighted(BLOOD_MIX),
                phone=contact_phone if child else self.phone(),
                email=(
                    f"{given.split()[0].lower()}.{family.lower()}{self.rng.randint(1, 99)}@example.com"
                    if not child and self.rng.random() < 0.2 else ""
                ),
                district=district,
                address=f"{self.rng.choice(rw.DISTRICT_SECTORS[district])} Sector, {self.rng.choice(rw.VILLAGES)} Village",
                national_id=self.national_id(dob.year, gender) if age >= 16 else None,
                insurance_provider=insurance,
                insurance_number=self.insurance_number(insurance, district),
                emergency_contact_name=f"{contact_name} ({relation})",
                emergency_contact_phone=contact_phone,
                registered_by=self.rng.choice(receptionists),
                created_at=registered_at,
            )
            patient.age_now = age
            self.patients.append(patient)
        Patient.objects.bulk_create(self.patients, batch_size=BATCH)

    def insurance_number(self, insurance, district):
        if insurance == "MUTUELLE":
            return f"CBHI/{district[:3].upper()}/{self.fake.numerify('#######')}"
        if insurance == "RSSB":
            return f"RSSB-{self.fake.numerify('########')}"
        if insurance == "MMI":
            return f"MMI-{self.fake.numerify('######')}"
        if insurance == "PRIVATE":
            return f"{self.rng.choice(rw.PRIVATE_INSURERS)}-{self.fake.numerify('#######')}"
        return ""

    # --- appointments ------------------------------------------------------------------------------

    def eligible(self, patient, dept):
        age = patient.age_now
        return {
            "PED": age < 15,
            "OBG": patient.gender == "F" and 15 <= age <= 49,
            "IM": age >= 15,
            "SUR": age >= 10,
            "EMR": True,
            "DEN": age >= 3,
        }[dept]

    def first_visit_department(self, patient):
        age = patient.age_now
        if age < 15:
            options = [("PED", 70), ("EMR", 15), ("DEN", 10), ("SUR", 5)]
        elif patient.gender == "F" and age <= 49:
            options = [("OBG", 35), ("IM", 35), ("EMR", 12), ("DEN", 10), ("SUR", 8)]
        else:
            options = [("IM", 60), ("EMR", 15), ("SUR", 12), ("DEN", 13)]
        return self.weighted([(d, w) for d, w in options if self.eligible(patient, d)])

    def create_appointments(self, total):
        self.used_slots = set()
        self.appointments = []
        self.case_of = {}
        receptionists = self.users_by_role[Role.RECEPTIONIST]
        dept_weights = [(spec["key"], spec["weight"]) for spec in rw.DEPARTMENTS]
        next_pk = next_id(Appointment)

        def add(patient, doctor, day, slot, status, created_at, dept):
            nonlocal next_pk
            case = self.rng.choice(rw.CASES[dept])
            appt = Appointment(
                id=next_pk,
                patient=patient,
                doctor=doctor,
                appointment_date=day,
                appointment_time=slot,
                reason=case[0],
                status=status,
                created_by=self.rng.choice(receptionists),
                created_at=created_at,
            )
            appt.dept_key = dept
            self.case_of[next_pk] = case
            self.appointments.append(appt)
            next_pk += 1
            return appt

        def past_status():
            return self.weighted([(Appointment.Status.COMPLETED, 82), (Appointment.Status.NO_SHOW, 9),
                                  (Appointment.Status.CANCELLED, 9)])

        # 1) New patients' first visit happens on the day they registered.
        window_start = self.history_days()[0][0]
        for patient in self.patients:
            day = patient.created_at.date()
            if day < window_start:
                continue  # long-standing patient, first seen before the history window
            dept = self.first_visit_department(patient)
            doctors = self.doctors_for(dept, day)
            reg_time = timezone.localtime(patient.created_at).time()
            for doctor in self.rng.sample(doctors, len(doctors)):
                slot = self.free_slot(doctor.pk, day, after=reg_time) or self.free_slot(doctor.pk, day)
                if slot:
                    add(patient, doctor, day, slot, past_status(), patient.created_at, dept)
                    break

        # 2) Today: a full clinic. The demo doctor ("doctor" login) has up to two
        #    morning visits done and three consultations still open to demo.
        def ended(slot):
            return self.aware(self.today, slot) + dt.timedelta(minutes=30) <= self.now

        def booked_for(patient, slot):
            booked = min(self.now, self.aware(self.today, slot)) - dt.timedelta(
                days=self.rng.randint(0, 6), hours=self.rng.randint(1, 5)
            )
            return max(booked, patient.created_at)

        demo_doctor = next(d for d in self.doctors if d.user.username == "doctor")
        adults = [p for p in self.patients if p.age_now >= 15] or self.patients
        demo_slots = sorted(self.free_slot(demo_doctor.pk, self.today) for _ in range(5))
        for index, slot in enumerate(demo_slots):
            done = index < 2 and ended(slot)
            patient = self.rng.choice(adults)
            status = Appointment.Status.COMPLETED if done else Appointment.Status.SCHEDULED
            add(patient, demo_doctor, self.today, slot, status, booked_for(patient, slot), "IM")

        others = [d for d in self.doctors if d.is_available and d is not demo_doctor]
        for doctor in self.rng.sample(others, min(9, len(others))):
            pool = [p for p in self.patients if self.eligible(p, doctor.dept_key)]
            if not pool:
                continue
            patient = self.rng.choice(pool)
            slot = self.free_slot(doctor.pk, self.today)
            status = Appointment.Status.COMPLETED if ended(slot) else Appointment.Status.SCHEDULED
            add(patient, doctor, self.today, slot, status, booked_for(patient, slot), doctor.dept_key)

        # 3) The next two weeks: scheduled follow-ups and new bookings.
        future_days = [self.today + dt.timedelta(days=i) for i in range(1, 15)]
        future_count = 45
        for _ in range(future_count):
            day = self.rng.choice(future_days)
            dept = self.weighted(dept_weights)
            if day.weekday() == 6 and dept != "EMR":
                day += dt.timedelta(days=1)
            doctors = [d for d in self.doctors_by_dept[dept] if d.is_available]
            pool = [p for p in self.patients if self.eligible(p, dept)]
            if not doctors or not pool:
                continue
            doctor, patient = self.rng.choice(doctors), self.rng.choice(pool)
            slot = self.free_slot(doctor.pk, day)
            if slot:
                booked = self.now - dt.timedelta(days=self.rng.randint(0, 10), hours=self.rng.randint(0, 6))
                add(patient, doctor, day, slot, Appointment.Status.SCHEDULED, max(booked, patient.created_at), dept)

        # 4) Return visits over the history window until we reach the target total.
        days, weights = self.history_days()
        attempts = 0
        while len(self.appointments) < total and attempts < total * 10:
            attempts += 1
            day = self.rng.choices(days, weights=weights, k=1)[0]
            dept = self.weighted(dept_weights)
            if day.weekday() == 6 and dept != "EMR":
                continue
            pool = [p for p in self.patients if p.created_at.date() < day and self.eligible(p, dept)]
            doctors = self.doctors_for(dept, day)
            if not pool or not doctors:
                continue
            patient, doctor = self.rng.choice(pool), self.rng.choice(doctors)
            slot = self.free_slot(doctor.pk, day)
            if not slot:
                continue
            booked = self.aware(day, slot) - dt.timedelta(days=self.rng.randint(0, 10), hours=self.rng.randint(1, 6))
            add(patient, doctor, day, slot, past_status(), max(booked, patient.created_at), dept)

        Appointment.objects.bulk_create(self.appointments, batch_size=BATCH)

    # --- medical records and prescriptions -------------------------------------------------------------

    def create_records_and_prescriptions(self):
        pharmacists = self.users_by_role[Role.PHARMACIST]
        record_pk = next_id(MedicalRecord)
        rx_pk = next_id(Prescription)
        records, prescriptions, items = [], [], []
        self.rx_by_appt = defaultdict(list)
        yesterday = self.today - dt.timedelta(days=1)

        for appt in self.appointments:
            if appt.status != Appointment.Status.COMPLETED:
                continue
            reason, symptoms, diagnosis, plan, meds = self.case_of[appt.pk]
            seen_at = self.aware(appt.appointment_date, appt.appointment_time) + dt.timedelta(minutes=self.rng.randint(15, 35))
            chronic = any(word in diagnosis for word in ("hypertension", "diabetes", "antenatal", "Anaemia"))
            follow_up = None
            if chronic:
                follow_up = appt.appointment_date + dt.timedelta(days=28)
            elif self.rng.random() < 0.15:
                follow_up = appt.appointment_date + dt.timedelta(days=14)
            record = MedicalRecord(
                id=record_pk,
                appointment=appt,
                symptoms=symptoms,
                diagnosis=diagnosis,
                treatment_plan=plan,
                notes=self.rng.choice(["", "", "", "Patient counselled; understands the plan.",
                                       "Insurance card verified at reception.", "Advised to return if symptoms worsen."]),
                follow_up_date=follow_up,
                created_at=seen_at,
            )
            records.append(record)
            record_pk += 1
            if not meds:
                continue

            if appt.appointment_date == self.today:
                dispensed = False
            elif appt.appointment_date == yesterday:
                dispensed = self.rng.random() < 0.7
            else:
                dispensed = True
            issued = seen_at + dt.timedelta(minutes=5)
            rx = Prescription(
                id=rx_pk,
                medical_record=record,
                issued_at=issued,
                notes=self.rng.choice(["", "", "Take with food.", "Complete the full course."]),
                status=Prescription.Status.DISPENSED if dispensed else Prescription.Status.PENDING,
                dispensed_at=issued + dt.timedelta(minutes=self.rng.randint(15, 90)) if dispensed else None,
                dispensed_by=self.rng.choice(pharmacists) if dispensed else None,
            )
            prescriptions.append(rx)
            self.rx_by_appt[appt.pk].append(rx)
            rx.lines = []
            for name, dosage, frequency, days, quantity in meds:
                line = PrescriptionItem(
                    prescription=rx,
                    medicine=self.medicines[name],
                    dosage=dosage,
                    frequency=frequency,
                    duration_days=days,
                    quantity=quantity,
                )
                items.append(line)
                rx.lines.append(line)
            rx_pk += 1

        MedicalRecord.objects.bulk_create(records, batch_size=BATCH)
        Prescription.objects.bulk_create(prescriptions, batch_size=BATCH)
        PrescriptionItem.objects.bulk_create(items, batch_size=BATCH)
        self.counts = {"records": len(records), "prescriptions": len(prescriptions)}

    # --- invoices and payments -----------------------------------------------------------------------

    def create_invoices_and_payments(self):
        accountants = self.users_by_role[Role.ACCOUNTANT]
        invoice_pk = next_id(Invoice)
        invoices, invoice_items, payments = [], [], []
        receipt_no = 1

        for appt in self.appointments:
            if appt.status != Appointment.Status.COMPLETED:
                continue
            age_days = (self.today - appt.appointment_date).days
            all_dispensed = all(rx.status == Prescription.Status.DISPENSED for rx in self.rx_by_appt[appt.pk])
            if age_days == 0 or (age_days < 3 and (not all_dispensed or self.rng.random() < 0.5)):
                continue  # left in the accountant's "Visits to bill" queue

            visit_end = self.aware(appt.appointment_date, appt.appointment_time) + dt.timedelta(minutes=45)
            created = min(visit_end + dt.timedelta(minutes=self.rng.randint(20, 120)), timezone.now())
            invoice = Invoice(
                id=invoice_pk,
                invoice_number=f"INV-{appt.appointment_date.year}-{invoice_pk:05d}",
                patient=appt.patient,
                appointment=appt,
                issue_date=appt.appointment_date,
                due_date=appt.appointment_date + dt.timedelta(days=7),
                created_by=self.rng.choice(accountants),
                created_at=created,
            )
            invoice_pk += 1
            lines = [
                InvoiceItem(
                    invoice=invoice,
                    item_type=InvoiceItem.ItemType.CONSULTATION,
                    description=f"Consultation - {appt.doctor} ({appt.doctor.department.name})",
                    quantity=1,
                    unit_price=appt.doctor.consultation_fee,
                )
            ]
            for rx in self.rx_by_appt[appt.pk]:
                for line in rx.lines:
                    lines.append(
                        InvoiceItem(
                            invoice=invoice,
                            item_type=InvoiceItem.ItemType.MEDICINE,
                            description=line.medicine.name,
                            quantity=line.quantity,
                            unit_price=line.medicine.unit_price,
                            medicine=line.medicine,
                        )
                    )
            invoice_items.extend(lines)
            total = sum(line.quantity * line.unit_price for line in lines)

            new_payments = self.payments_for(invoice, total, created, accountants, receipt_no)
            receipt_no += len(new_payments)
            payments.extend(new_payments)
            paid = sum(p.amount for p in new_payments)
            if paid <= 0:
                invoice.status = Invoice.Status.UNPAID
            elif paid < total:
                invoice.status = Invoice.Status.PARTIALLY_PAID
            else:
                invoice.status = Invoice.Status.PAID
            invoices.append(invoice)

        Invoice.objects.bulk_create(invoices, batch_size=BATCH)
        InvoiceItem.objects.bulk_create(invoice_items, batch_size=BATCH)
        Payment.objects.bulk_create(payments, batch_size=BATCH)
        self.counts.update(invoices=len(invoices), payments=len(payments))

    def payments_for(self, invoice, total, billed_at, accountants, receipt_no):
        """Pick the bill's outcome by its age, then create matching payments.

        Insured patients pay their co-pay (ticket modérateur) at the cashier and
        the insurer reimburses its share weeks later, so recent bills are often
        only partly paid. Some patients leave without paying at all.
        """
        age_days = (self.today - invoice.issue_date).days
        if age_days > 60:
            outcome = self.weighted([("PAID", 88), ("PARTIAL", 7), ("UNPAID", 5)])
        elif age_days > 14:
            outcome = self.weighted([("PAID", 62), ("PARTIAL", 26), ("UNPAID", 12)])
        else:
            outcome = self.weighted([("PAID", 30), ("PARTIAL", 45), ("UNPAID", 25)])
        if outcome == "UNPAID":
            return []

        insurance = invoice.patient.insurance_provider
        insurer_part = money(total * Decimal(str(rw.INSURER_SHARE[insurance])))
        patient_part = total - insurer_part
        latest = timezone.now()
        result = []

        def pay(amount, method, when, reference):
            if amount > 0:
                result.append(
                    Payment(invoice=invoice, amount=amount, method=method, reference=reference,
                            paid_at=min(when, latest), received_by=self.rng.choice(accountants))
                )

        cashier_time = billed_at + dt.timedelta(minutes=self.rng.randint(2, 25))
        method = self.weighted([(Payment.Method.MOBILE_MONEY, 55), (Payment.Method.CASH, 35), (Payment.Method.CARD, 10)])

        if insurance == "NONE":
            if outcome == "PAID" and self.rng.random() < 0.8:
                pay(total, method, cashier_time, self.reference(method, cashier_time, receipt_no))
            else:
                # Pays part now (and, if PAID, the rest a few days later by MoMo).
                first = money(total * Decimal(str(self.rng.choice([0.3, 0.5, 0.6]))))
                pay(first, method, cashier_time, self.reference(method, cashier_time, receipt_no))
                if outcome == "PAID":
                    later = cashier_time + dt.timedelta(days=self.rng.randint(2, 20))
                    pay(total - first, Payment.Method.MOBILE_MONEY, later,
                        self.reference(Payment.Method.MOBILE_MONEY, later, receipt_no + 1))
            return result

        # Insured: co-pay at the cashier, insurer settles 10-60 days later.
        pay(patient_part, method, cashier_time, self.reference(method, cashier_time, receipt_no))
        if outcome == "PAID":
            delay = self.rng.randint(10, 60) if age_days > 60 else self.rng.randint(1, max(1, age_days))
            settled = self.aware(invoice.issue_date + dt.timedelta(days=delay), dt.time(self.rng.randint(9, 15), 0))
            pay(insurer_part, Payment.Method.INSURANCE, settled,
                f"{insurance}-CLM-{settled.year}-{self.fake.numerify('######')}")
        return result

    def reference(self, method, when, receipt_no):
        if method == Payment.Method.MOBILE_MONEY:
            network = self.weighted([("MTN-MOMO", 75), ("AIRTEL-MONEY", 25)])
            return f"{network}-{self.fake.numerify('##########')}"
        if method == Payment.Method.CARD:
            return f"POS-{self.fake.numerify('######')}"
        return f"RCT-{when.year}-{receipt_no:06d}"

    # --- summary -------------------------------------------------------------------------------------

    def report(self):
        status_counts = defaultdict(int)
        for appt in self.appointments:
            status_counts[appt.get_status_display()] += 1
        self.stdout.write(self.style.SUCCESS("Seeded Ubuzima Referral Hospital demo data:"))
        self.stdout.write(f"  departments   {len(self.departments)}")
        self.stdout.write(f"  doctors       {len(self.doctors)}")
        self.stdout.write(f"  medicines     {len(self.medicines)}")
        self.stdout.write(f"  patients      {len(self.patients)}")
        self.stdout.write(f"  appointments  {len(self.appointments)}  ({', '.join(f'{k}: {v}' for k, v in status_counts.items())})")
        self.stdout.write(f"  records       {self.counts['records']}")
        self.stdout.write(f"  prescriptions {self.counts['prescriptions']}")
        self.stdout.write(f"  invoices      {self.counts['invoices']}")
        self.stdout.write(f"  payments      {self.counts['payments']}")
        self.stdout.write("")
        self.stdout.write(f"Demo logins (password for every account: {rw.DEMO_PASSWORD}):")
        for username in ["admin", "receptionist", "doctor", "pharmacist", "accountant"]:
            user = User.objects.get(username=username)
            self.stdout.write(f"  {username:<13} {user.get_full_name():<22} {user.get_role_display()}")
