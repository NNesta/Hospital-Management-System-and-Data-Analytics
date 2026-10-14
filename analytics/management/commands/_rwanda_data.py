"""Reference data for `seed_data`: Rwandan names, places, departments, cases
and medicines. All people are fictional; no real patient data is used.

(The leading underscore stops Django from treating this module as a command.)
"""

# --- People --------------------------------------------------------------------------------

# Rwandans usually carry a Kinyarwanda name plus a Christian/French/English one.
MALE_GIVEN = [
    "Jean Claude", "Jean de Dieu", "Jean Bosco", "Jean Paul", "Emmanuel", "Eric", "Patrick", "Olivier",
    "Innocent", "Theogene", "Celestin", "Aimable", "Fidele", "Valens", "Gilbert", "Didier", "Samuel",
    "Pacifique", "Fabrice", "Thierry", "Alexis", "Janvier", "Faustin", "Vianney", "Damascene", "Felix",
    "Augustin", "Viateur", "Claude", "Yves", "Kevin", "Arsene", "Placide", "Gaspard", "Elie", "Moise",
]
FEMALE_GIVEN = [
    "Alice", "Aline", "Claudine", "Diane", "Divine", "Grace", "Josiane", "Clarisse", "Vestine", "Solange",
    "Chantal", "Yvonne", "Esperance", "Immaculee", "Beatha", "Odette", "Jeanne", "Marie Claire", "Annonciata",
    "Consolata", "Florence", "Delphine", "Sandrine", "Nadine", "Ange", "Belyse", "Kevine", "Liliane",
    "Jacqueline", "Francine", "Josephine", "Agnes", "Speciose", "Donatille", "Pascasie", "Claudette",
]
# Kinyarwanda names (used as the family/last name field).
MALE_KINYARWANDA = [
    "Mugisha", "Niyonzima", "Habimana", "Nshimiyimana", "Hakizimana", "Bizimana", "Munyaneza", "Rukundo",
    "Ntwari", "Gatete", "Kamanzi", "Muhire", "Shema", "Cyusa", "Ganza", "Manzi", "Gasana", "Karangwa",
    "Murenzi", "Ndayisaba", "Twagirimana", "Nsengiyumva", "Habiyaremye", "Hategekimana", "Ndagijimana",
    "Nzabonimpa", "Mbonigaba", "Byiringiro", "Nsabimana", "Ntaganda", "Rwigema", "Kalisa", "Sibomana",
    "Nkurunziza", "Habumugisha", "Niyomugabo", "Uwimana", "Tuyishime", "Iradukunda", "Ishimwe",
]
FEMALE_KINYARWANDA = [
    "Uwase", "Mukamana", "Uwamahoro", "Kayitesi", "Ingabire", "Umutoni", "Keza", "Mukeshimana", "Uwera",
    "Mutoni", "Iribagiza", "Uwamariya", "Mukandayisenga", "Nyirahabimana", "Nyiramana", "Uwizeye",
    "Umuhoza", "Umwali", "Uwineza", "Mukashema", "Uwingabire", "Mukamurenzi", "Nyiransabimana", "Akimana",
    "Isimbi", "Teta", "Kirezi", "Ineza", "Mahoro", "Uwamwezi", "Uwimana", "Tuyishime", "Iradukunda",
    "Ishimwe", "Niyonsaba", "Mukarugwiza", "Uwitonze", "Umulisa",
]
# Kinyarwanda given names that children often go by.
CHILD_MALE_GIVEN = ["Ganza", "Shema", "Cyusa", "Gisa", "Hirwa", "Ishimwe", "Kwizera", "Mugabo", "Ntwari", "Sano"]
CHILD_FEMALE_GIVEN = ["Keza", "Teta", "Isimbi", "Ineza", "Kirezi", "Gisa", "Ishimwe", "Uwase", "Mahoro", "Shimwa"]

# --- Places --------------------------------------------------------------------------------

# District -> real sectors. The hospital is in Kigali, so Kigali and the
# neighbouring districts carry most of the weight.
DISTRICT_SECTORS = {
    "Gasabo": ["Kimironko", "Remera", "Kacyiru", "Kimihurura", "Gisozi", "Kinyinya", "Ndera", "Rusororo", "Jali", "Bumbogo", "Gatsata", "Jabana"],
    "Kicukiro": ["Gikondo", "Kagarama", "Kanombe", "Kicukiro", "Niboye", "Nyarugunga", "Masaka", "Gahanga", "Gatenga", "Kigarama"],
    "Nyarugenge": ["Nyamirambo", "Gitega", "Kimisagara", "Muhima", "Nyakabanda", "Nyarugenge", "Rwezamenyo", "Kigali", "Mageragere", "Kanyinya"],
    "Bugesera": ["Nyamata", "Ntarama", "Gashora", "Rilima", "Mayange", "Ruhuha"],
    "Rwamagana": ["Kigabiro", "Muhazi", "Gishari", "Musha", "Fumbwe"],
    "Kamonyi": ["Runda", "Gacurabwenge", "Rugalika", "Musambira"],
    "Rulindo": ["Shyorongi", "Bushoki", "Base", "Ntarabana"],
    "Muhanga": ["Nyamabuye", "Shyogwe", "Cyeza", "Muhanga"],
    "Musanze": ["Muhoza", "Cyuve", "Kinigi", "Musanze"],
    "Huye": ["Ngoma", "Tumba", "Mukura", "Huye"],
    "Rubavu": ["Gisenyi", "Rubavu", "Nyamyumba", "Rugerero"],
    "Nyagatare": ["Nyagatare", "Karangazi", "Rwimiyaga", "Matimba"],
    "Kayonza": ["Mukarange", "Kabarondo", "Rwinkwavu", "Murundi"],
    "Gicumbi": ["Byumba", "Kageyo", "Rukomo", "Rubaya"],
    "Rusizi": ["Kamembe", "Gihundwe", "Mururu", "Nyakarenzo"],
    "Ngoma": ["Kibungo", "Remera", "Rukira", "Zaza"],
    "Nyanza": ["Busasamana", "Mukingo", "Nyagisozi", "Cyabakamyi"],
    "Karongi": ["Bwishyura", "Rubengera", "Gashari", "Mubuga"],
}
DISTRICT_WEIGHTS = {
    "Gasabo": 26, "Kicukiro": 20, "Nyarugenge": 17, "Bugesera": 7, "Rwamagana": 4, "Kamonyi": 4,
    "Rulindo": 3, "Muhanga": 3, "Musanze": 2, "Huye": 2, "Rubavu": 2, "Nyagatare": 2, "Kayonza": 2,
    "Gicumbi": 2, "Rusizi": 1, "Ngoma": 1, "Nyanza": 1, "Karongi": 1,
}
# Common village (umudugudu) names across Rwanda.
VILLAGES = [
    "Amahoro", "Ubumwe", "Isangano", "Urumuri", "Itetero", "Ineza", "Imena", "Intwari", "Umucyo",
    "Umurava", "Ituze", "Ubwiza", "Inyange", "Kabeza", "Gatare", "Rebero", "Byimana", "Nyagatovu",
    "Kamahoro", "Ubutare", "Iterambere", "Agatare", "Indatwa", "Umutekano",
]

# --- Hospital ---------------------------------------------------------------------------------

DEPARTMENTS = [
    {
        "key": "IM",
        "name": "Internal Medicine",
        "location": "Block A, ground floor",
        "description": "Adult outpatient consultations: malaria, hypertension, diabetes and infections.",
        "weight": 30,
    },
    {
        "key": "PED",
        "name": "Paediatrics",
        "location": "Block B, 1st floor",
        "description": "Care for children under 15: fevers, respiratory illness, diarrhoea and nutrition.",
        "weight": 20,
    },
    {
        "key": "OBG",
        "name": "Gynaecology & Obstetrics",
        "location": "Maternity wing, Block C",
        "description": "Antenatal and postnatal care, family planning and women's health.",
        "weight": 17,
    },
    {
        "key": "SUR",
        "name": "General Surgery",
        "location": "Block D, 2nd floor (theatre level)",
        "description": "Surgical consultations, minor procedures and post-operative follow-up.",
        "weight": 10,
    },
    {
        "key": "EMR",
        "name": "Emergency & Trauma",
        "location": "Emergency wing, ground floor (open 24/7)",
        "description": "Accidents and emergencies, including road traffic injuries from motos.",
        "weight": 13,
    },
    {
        "key": "DEN",
        "name": "Dental Care",
        "location": "Block A, 1st floor",
        "description": "Dental check-ups, fillings, extractions and gum treatment.",
        "weight": 10,
    },
]

# username, first, last, gender, department key, specialization, licence, fee, available
DOCTORS = [
    ("doctor", "Eric", "Mugisha", "M", "IM", "Internal medicine", "RMDC/MD/2014/0457", 10000, True),
    ("dr.uwamahoro", "Claudine", "Uwamahoro", "F", "IM", "General practitioner", "RMDC/MD/2018/1132", 5000, True),
    ("dr.niyonzima", "Jean de Dieu", "Niyonzima", "M", "IM", "Internal medicine", "RMDC/MD/2012/0311", 10000, True),
    ("dr.mukeshimana", "Alice", "Mukeshimana", "F", "PED", "Paediatrician", "RMDC/MD/2015/0682", 10000, True),
    ("dr.hakizimana", "Olivier", "Hakizimana", "M", "PED", "Paediatrician", "RMDC/MD/2017/0915", 10000, True),
    ("dr.umutoni", "Grace", "Umutoni", "F", "PED", "General practitioner (paediatric OPD)", "RMDC/MD/2020/1544", 5000, True),
    ("dr.nyirahabimana", "Chantal", "Nyirahabimana", "F", "OBG", "Obstetrician-gynaecologist", "RMDC/MD/2011/0254", 15000, True),
    ("dr.nsengimana", "Emmanuel", "Nsengimana", "M", "OBG", "Obstetrician-gynaecologist", "RMDC/MD/2016/0778", 15000, True),
    ("dr.uwera", "Solange", "Uwera", "F", "OBG", "Midwifery-trained GP", "RMDC/MD/2019/1320", 5000, False),
    ("dr.habiyaremye", "Innocent", "Habiyaremye", "M", "SUR", "General surgeon", "RMDC/MD/2010/0198", 15000, True),
    ("dr.ntwari", "Didier", "Ntwari", "M", "SUR", "Orthopaedic surgeon", "RMDC/MD/2013/0406", 15000, True),
    ("dr.munyaneza", "Fabrice", "Munyaneza", "M", "EMR", "Emergency physician", "RMDC/MD/2016/0801", 10000, True),
    ("dr.iradukunda", "Divine", "Iradukunda", "F", "EMR", "Emergency physician", "RMDC/MD/2021/1702", 10000, True),
    ("dr.gasana", "Thierry", "Gasana", "M", "DEN", "Dental surgeon", "RMDC/DS/2015/0123", 8000, True),
    ("dr.kayitesi", "Vestine", "Kayitesi", "F", "DEN", "Dental surgeon", "RMDC/DS/2018/0207", 8000, True),
]

# username, first, last, role, superuser?
STAFF = [
    ("admin", "Jean Paul", "Kamanzi", "ADMIN", True),
    ("receptionist", "Aline", "Uwase", "RECEPTIONIST", False),
    ("pharmacist", "Josiane", "Ingabire", "PHARMACIST", False),
    ("accountant", "Patrick", "Habimana", "ACCOUNTANT", False),
    ("rec.niyonsaba", "Clarisse", "Niyonsaba", "RECEPTIONIST", False),
    ("rec.tuyishime", "Samuel", "Tuyishime", "RECEPTIONIST", False),
    ("pharm.bizimana", "Gilbert", "Bizimana", "PHARMACIST", False),
    ("acc.mutoni", "Sandrine", "Mutoni", "ACCOUNTANT", False),
]

DEMO_PASSWORD = "Ubuzima@2026"

# --- Medicines (Rwanda essential medicines list style), prices in RWF per unit ---------------

# name, generic name, category, unit price, reorder level, stock
MEDICINES = [
    ("Coartem 20/120 mg tablet", "Artemether + lumefantrine", "ANTIMALARIAL", 250, 300, 2400),
    ("Artesunate 60 mg injection", "Artesunate", "ANTIMALARIAL", 2500, 40, 28),
    ("Amoxicillin 500 mg capsule", "Amoxicillin", "ANTIBIOTIC", 80, 300, 3100),
    ("Amoxicillin 250 mg/5 ml suspension (100 ml)", "Amoxicillin", "ANTIBIOTIC", 1800, 40, 35),
    ("Amoxicillin-clavulanate 625 mg tablet", "Co-amoxiclav", "ANTIBIOTIC", 450, 100, 640),
    ("Ciprofloxacin 500 mg tablet", "Ciprofloxacin", "ANTIBIOTIC", 120, 200, 1500),
    ("Cotrimoxazole 480 mg tablet", "Sulfamethoxazole + trimethoprim", "ANTIBIOTIC", 30, 200, 1200),
    ("Metronidazole 250 mg tablet", "Metronidazole", "ANTIBIOTIC", 30, 300, 2500),
    ("Doxycycline 100 mg capsule", "Doxycycline", "ANTIBIOTIC", 70, 150, 900),
    ("Ceftriaxone 1 g injection", "Ceftriaxone", "ANTIBIOTIC", 1500, 60, 48),
    ("Azithromycin 500 mg tablet", "Azithromycin", "ANTIBIOTIC", 400, 60, 300),
    ("Cloxacillin 500 mg capsule", "Cloxacillin", "ANTIBIOTIC", 120, 150, 820),
    ("Paracetamol 500 mg tablet", "Paracetamol", "ANALGESIC", 20, 500, 6200),
    ("Paracetamol syrup 120 mg/5 ml (100 ml)", "Paracetamol", "ANALGESIC", 1200, 50, 340),
    ("Ibuprofen 400 mg tablet", "Ibuprofen", "ANALGESIC", 30, 300, 2500),
    ("Diclofenac 50 mg tablet", "Diclofenac sodium", "ANALGESIC", 40, 200, 1000),
    ("Tramadol 50 mg capsule", "Tramadol", "ANALGESIC", 150, 100, 480),
    ("Amlodipine 5 mg tablet", "Amlodipine", "ANTIHYPERTENSIVE", 60, 300, 2100),
    ("Nifedipine 20 mg retard tablet", "Nifedipine", "ANTIHYPERTENSIVE", 50, 200, 1000),
    ("Hydrochlorothiazide 25 mg tablet", "Hydrochlorothiazide", "ANTIHYPERTENSIVE", 30, 200, 900),
    ("Captopril 25 mg tablet", "Captopril", "ANTIHYPERTENSIVE", 40, 150, 700),
    ("Atenolol 50 mg tablet", "Atenolol", "ANTIHYPERTENSIVE", 50, 150, 600),
    ("Metformin 500 mg tablet", "Metformin", "ANTIDIABETIC", 40, 400, 3000),
    ("Glibenclamide 5 mg tablet", "Glibenclamide", "ANTIDIABETIC", 30, 150, 800),
    ("Insulin Mixtard 30/70 (10 ml vial)", "Human insulin, biphasic", "ANTIDIABETIC", 8500, 20, 15),
    ("Omeprazole 20 mg capsule", "Omeprazole", "GASTRO", 60, 300, 2000),
    ("Oral rehydration salts (ORS) sachet", "ORS, low osmolarity", "GASTRO", 200, 200, 1200),
    ("Zinc sulphate 20 mg dispersible tablet", "Zinc sulphate", "SUPPLEMENT", 50, 200, 1000),
    ("Albendazole 400 mg tablet", "Albendazole", "ANTHELMINTIC", 150, 150, 900),
    ("Mebendazole 100 mg tablet", "Mebendazole", "ANTHELMINTIC", 50, 100, 600),
    ("Ferrous sulphate + folic acid tablet", "Iron + folic acid", "SUPPLEMENT", 30, 400, 3200),
    ("Folic acid 5 mg tablet", "Folic acid", "SUPPLEMENT", 20, 200, 1000),
    ("Multivitamin syrup (100 ml)", "Multivitamins", "SUPPLEMENT", 1500, 30, 150),
    ("Chlorpheniramine 4 mg tablet", "Chlorphenamine", "ANTIHISTAMINE", 20, 150, 900),
    ("Cetirizine 10 mg tablet", "Cetirizine", "ANTIHISTAMINE", 50, 100, 500),
    ("Salbutamol inhaler 100 mcg", "Salbutamol", "RESPIRATORY", 4500, 20, 12),
    ("Prednisolone 5 mg tablet", "Prednisolone", "RESPIRATORY", 30, 200, 1000),
    ("Fluconazole 150 mg capsule", "Fluconazole", "OTHER", 300, 50, 300),
    ("Chlorhexidine 0.2% mouthwash (250 ml)", "Chlorhexidine gluconate", "OTHER", 2500, 15, 60),
    ("Silver sulfadiazine 1% cream (50 g)", "Silver sulfadiazine", "OTHER", 3000, 15, 9),
]

# --- Clinical cases per department ---------------------------------------------------------------
# (reason, symptoms, diagnosis, treatment plan, [(medicine, dosage, frequency, days, quantity)])

CASES = {
    "IM": [
        ("Fever and headache for 3 days", "Fever 38.9 C, headache, joint pains and chills. Malaria RDT positive.",
         "Uncomplicated malaria (B54)", "Artemether-lumefantrine for 3 days, paracetamol for fever, oral fluids. Return if vomiting or confused.",
         [("Coartem 20/120 mg tablet", "4 tablets", "twice a day", 3, 24), ("Paracetamol 500 mg tablet", "2 tablets", "3 times a day", 3, 18)]),
        ("Routine blood pressure review", "BP 162/98 mmHg, occasional headaches, no chest pain.",
         "Essential hypertension (I10)", "Amlodipine 5 mg daily, reduce salt, walk 30 minutes a day. Review in 4 weeks.",
         [("Amlodipine 5 mg tablet", "1 tablet", "once a day", 30, 30)]),
        ("Hypertension follow-up", "BP 148/94 mmHg on amlodipine, ankle swelling mild.",
         "Essential hypertension, not controlled (I10)", "Add hydrochlorothiazide 25 mg daily. Check kidney function next visit.",
         [("Amlodipine 5 mg tablet", "1 tablet", "once a day", 30, 30), ("Hydrochlorothiazide 25 mg tablet", "1 tablet", "once a day", 30, 30)]),
        ("Diabetes follow-up", "Fasting glucose 9.8 mmol/L, polyuria, fatigue.",
         "Type 2 diabetes mellitus (E11)", "Metformin 500 mg twice daily, diet counselling, HbA1c in 3 months.",
         [("Metformin 500 mg tablet", "1 tablet", "twice a day", 30, 60)]),
        ("Epigastric pain after meals", "Burning epigastric pain, worse at night, no black stools.",
         "Gastritis / peptic ulcer disease (K29)", "Omeprazole 20 mg daily for 4 weeks. Avoid NSAIDs and alcohol (urwagwa, beer).",
         [("Omeprazole 20 mg capsule", "1 capsule", "once a day", 28, 28)]),
        ("Fever and abdominal pain for a week", "Step-ladder fever, abdominal pain, coated tongue.",
         "Typhoid fever (A01.0)", "Ciprofloxacin 500 mg twice daily for 10 days, boiled water and hand hygiene.",
         [("Ciprofloxacin 500 mg tablet", "1 tablet", "twice a day", 10, 20), ("Paracetamol 500 mg tablet", "2 tablets", "3 times a day", 3, 18)]),
        ("Burning urination", "Dysuria and frequency, suprapubic pain. Urine dipstick nitrite positive.",
         "Urinary tract infection (N39.0)", "Ciprofloxacin for 5 days, drink plenty of water.",
         [("Ciprofloxacin 500 mg tablet", "1 tablet", "twice a day", 5, 10)]),
        ("Cough and fever", "Productive cough for 5 days, fever, crackles at the right lung base.",
         "Community-acquired pneumonia (J18.9)", "Amoxicillin 500 mg 3 times daily for 7 days. Return if short of breath.",
         [("Amoxicillin 500 mg capsule", "1 capsule", "3 times a day", 7, 21), ("Paracetamol 500 mg tablet", "2 tablets", "3 times a day", 3, 18)]),
        ("Tiredness and dizziness", "Pale conjunctivae, Hb 9.1 g/dL.",
         "Iron-deficiency anaemia (D50)", "Iron and folic acid daily for 3 months; deworm.",
         [("Ferrous sulphate + folic acid tablet", "1 tablet", "once a day", 30, 30), ("Albendazole 400 mg tablet", "1 tablet", "single dose", 1, 1)]),
    ],
    "PED": [
        ("Child with high fever", "Fever 39.2 C, irritable, poor feeding. Malaria RDT positive.",
         "Uncomplicated malaria in a child (B54)", "Weight-based artemether-lumefantrine for 3 days, paracetamol syrup, keep breastfeeding.",
         [("Coartem 20/120 mg tablet", "2 tablets", "twice a day", 3, 12), ("Paracetamol syrup 120 mg/5 ml (100 ml)", "5 ml", "3 times a day", 3, 1)]),
        ("Cough and runny nose", "Cough, runny nose and mild fever. Chest clear, no fast breathing.",
         "Upper respiratory tract infection (J06.9)", "Supportive care, paracetamol, fluids. Return if breathing becomes fast.",
         [("Paracetamol syrup 120 mg/5 ml (100 ml)", "5 ml", "3 times a day", 3, 1)]),
        ("Diarrhoea for 2 days", "Watery stools 5 times a day, some dehydration (sunken eyes, drinks eagerly).",
         "Acute gastroenteritis with some dehydration (A09)", "ORS after each loose stool, zinc for 10 days, continue feeding.",
         [("Oral rehydration salts (ORS) sachet", "1 sachet", "after each loose stool", 3, 6), ("Zinc sulphate 20 mg dispersible tablet", "1 tablet", "once a day", 10, 10)]),
        ("Abdominal pain and poor appetite", "Distended abdomen, last deworming more than 6 months ago.",
         "Intestinal helminthiasis (B82.0)", "Albendazole single dose; hand washing and wearing shoes.",
         [("Albendazole 400 mg tablet", "1 tablet", "single dose", 1, 1)]),
        ("Fast breathing and fever", "Respiratory rate 52/min, no chest indrawing, crackles on auscultation.",
         "Pneumonia in a child (J18.9)", "Amoxicillin suspension for 5 days. Review in 2 days.",
         [("Amoxicillin 250 mg/5 ml suspension (100 ml)", "5 ml", "3 times a day", 5, 1)]),
        ("Growth monitoring visit", "Weight-for-age below -2 SD, no oedema.",
         "Moderate acute malnutrition (E44.0)", "Nutrition counselling, multivitamin, review at the health centre in 2 weeks.",
         [("Multivitamin syrup (100 ml)", "5 ml", "once a day", 20, 1)]),
        ("Itchy skin rash", "Papular itchy rash on arms and legs for 4 days.",
         "Allergic dermatitis (L23)", "Antihistamine for 5 days, avoid the suspected soap.",
         [("Chlorpheniramine 4 mg tablet", "half tablet", "twice a day", 5, 5)]),
    ],
    "OBG": [
        ("Antenatal care visit", "28 weeks pregnant, BP 112/70, fundal height matches dates, foetal heart 142.",
         "Normal pregnancy, routine antenatal care (Z34)", "Iron and folic acid daily, next ANC in 4 weeks, birth preparedness plan.",
         [("Ferrous sulphate + folic acid tablet", "1 tablet", "once a day", 30, 30)]),
        ("Lower abdominal pain and discharge", "Lower abdominal tenderness, abnormal discharge, fever 38.1 C.",
         "Pelvic inflammatory disease (N73.9)", "Doxycycline and metronidazole for 14 days; partner treatment advised.",
         [("Doxycycline 100 mg capsule", "1 capsule", "twice a day", 14, 28), ("Metronidazole 250 mg tablet", "2 tablets", "twice a day", 14, 56)]),
        ("Burning urination in pregnancy", "22 weeks pregnant, dysuria and frequency, dipstick positive.",
         "Urinary tract infection in pregnancy (O23.4)", "Amoxicillin for 7 days, plenty of fluids.",
         [("Amoxicillin 500 mg capsule", "1 capsule", "3 times a day", 7, 21)]),
        ("Postnatal check-up", "6 weeks after delivery, healing well, exclusive breastfeeding.",
         "Routine postnatal care (Z39.2)", "Family planning counselling, iron for one more month, baby vaccination card checked.",
         [("Ferrous sulphate + folic acid tablet", "1 tablet", "once a day", 30, 30)]),
        ("Dizziness in pregnancy", "24 weeks pregnant, Hb 8.9 g/dL, tired.",
         "Anaemia in pregnancy (O99.0)", "Iron and folic acid, deworming after first trimester, repeat Hb in 4 weeks.",
         [("Ferrous sulphate + folic acid tablet", "1 tablet", "twice a day", 30, 60), ("Folic acid 5 mg tablet", "1 tablet", "once a day", 30, 30)]),
        ("Vaginal itching", "Thick white discharge and itching for a week.",
         "Vulvovaginal candidiasis (B37.3)", "Fluconazole 150 mg single dose.",
         [("Fluconazole 150 mg capsule", "1 capsule", "single dose", 1, 1)]),
    ],
    "SUR": [
        ("Swelling in the groin", "Reducible right inguinal swelling, worse on coughing.",
         "Right inguinal hernia (K40.9)", "Booked for elective herniorrhaphy. Analgesia meanwhile.",
         [("Ibuprofen 400 mg tablet", "1 tablet", "3 times a day", 5, 15)]),
        ("Painful swelling on the thigh", "Fluctuant tender swelling of 4 cm, fever.",
         "Soft tissue abscess (L02.4)", "Incision and drainage done, daily dressing, cloxacillin for 7 days.",
         [("Cloxacillin 500 mg capsule", "1 capsule", "4 times a day", 7, 28), ("Ibuprofen 400 mg tablet", "1 tablet", "3 times a day", 5, 15)]),
        ("Post-operative review", "Day 10 after appendicectomy, wound clean and dry.",
         "Post-operative follow-up (Z48.8)", "Stitches removed. Paracetamol if needed.",
         [("Paracetamol 500 mg tablet", "2 tablets", "3 times a day", 3, 18)]),
        ("Right lower abdominal pain", "Tenderness and rebound in the right iliac fossa, fever 38.4 C.",
         "Acute appendicitis (K35.8)", "Admitted for appendicectomy; ceftriaxone and metronidazole.",
         [("Ceftriaxone 1 g injection", "1 g", "once a day", 3, 3), ("Metronidazole 250 mg tablet", "2 tablets", "3 times a day", 5, 30)]),
        ("Knee pain after a fall", "Swollen right knee, X-ray shows no fracture.",
         "Sprain of the knee (S83.6)", "Rest, ice, compression, elevation; ibuprofen; physiotherapy referral.",
         [("Ibuprofen 400 mg tablet", "1 tablet", "3 times a day", 5, 15)]),
    ],
    "EMR": [
        ("Moto accident injury", "Abrasions and a 5 cm laceration on the left leg after a moto crash. Conscious, GCS 15.",
         "Road traffic injury, leg laceration (V29)", "Wound cleaned and sutured, tetanus toxoid given, analgesia and antibiotics.",
         [("Tramadol 50 mg capsule", "1 capsule", "3 times a day", 3, 9), ("Amoxicillin-clavulanate 625 mg tablet", "1 tablet", "twice a day", 5, 10)]),
        ("High fever and vomiting", "Fever 40 C, repeated vomiting, very weak. Malaria RDT positive.",
         "Severe malaria (B50.9)", "IV artesunate at 0, 12 and 24 hours, then oral ACT. Admitted for observation.",
         [("Artesunate 60 mg injection", "2.4 mg/kg", "at 0, 12 and 24 h", 1, 3), ("Coartem 20/120 mg tablet", "4 tablets", "twice a day", 3, 24)]),
        ("Difficulty breathing", "Wheezing, SpO2 92%, known asthmatic.",
         "Acute asthma attack (J45.901)", "Salbutamol nebulisation, prednisolone for 5 days, inhaler technique taught.",
         [("Salbutamol inhaler 100 mcg", "2 puffs", "when needed", 30, 1), ("Prednisolone 5 mg tablet", "8 tablets", "once a day", 5, 40)]),
        ("Hand cut at work", "Clean 3 cm laceration on the palm, tendons intact.",
         "Laceration of the hand (S61.4)", "Sutured, dressing, review in 7 days for removal.",
         [("Paracetamol 500 mg tablet", "2 tablets", "3 times a day", 3, 18)]),
        ("Burn from boiling water", "Superficial partial-thickness scald on the forearm, about 4% of body surface.",
         "Scald burn of the forearm (T22.2)", "Cooled, cleaned, silver sulfadiazine dressing; analgesia; review in 2 days.",
         [("Silver sulfadiazine 1% cream (50 g)", "thin layer", "once a day", 7, 1), ("Paracetamol 500 mg tablet", "2 tablets", "3 times a day", 3, 18)]),
    ],
    "DEN": [
        ("Toothache", "Deep caries on the lower left molar, pain when chewing.",
         "Dental caries (K02.9)", "Filling done. Ibuprofen for pain. Brush twice daily.",
         [("Ibuprofen 400 mg tablet", "1 tablet", "3 times a day", 3, 9)]),
        ("Swollen gum and pain", "Periapical abscess on the upper right premolar.",
         "Dental abscess (K04.7)", "Drainage, antibiotics for 5 days, extraction booked.",
         [("Amoxicillin 500 mg capsule", "1 capsule", "3 times a day", 5, 15), ("Metronidazole 250 mg tablet", "2 tablets", "3 times a day", 5, 30)]),
        ("Bleeding gums", "Plaque and gum bleeding on probing.",
         "Gingivitis (K05.1)", "Scaling and polishing, chlorhexidine mouthwash for 1 week.",
         [("Chlorhexidine 0.2% mouthwash (250 ml)", "10 ml", "twice a day", 7, 1)]),
        ("Review after tooth extraction", "Socket healing well, no dry socket.",
         "Follow-up after extraction (Z48.8)", "No further treatment needed.", []),
    ],
}

# Insurers: share of patients, and the share of each bill the insurer pays.
# Mutuelle de Santé members pay a 10% ticket modérateur; RSSB/MMI members 15%.
INSURANCE_MIX = [("MUTUELLE", 64), ("RSSB", 18), ("MMI", 5), ("PRIVATE", 5), ("NONE", 8)]
INSURER_SHARE = {"MUTUELLE": 0.90, "RSSB": 0.85, "MMI": 0.85, "PRIVATE": 0.90, "NONE": 0.0}
PRIVATE_INSURERS = ["RADIANT", "SANLAM", "BRITAM", "PRIME", "OLDMUTUAL"]

RELATIONS = ["spouse", "mother", "father", "brother", "sister", "son", "daughter", "neighbour"]
