"""
VaakSetu — Demo Scenarios
30 realistic 1092 helpline call scenarios for hackathon demonstration.
Covers all major issue categories, languages, dialects, and sentiment types.
"""

DEMO_SCENARIOS = [
    # ── Ration Card Issues ──────────────────────────────────────────────────
    {
        "id": "RC001",
        "title": "Ration card Aadhaar linking (Kannada, confusion)",
        "language": "kn",
        "dialect": "bengaluru",
        "sentiment": "confusion",
        "transcript": "Namma ration card aadhar jothege link aagbekittu antha helitidare, aadare online portal le hogidre otp bandE illa. Yenu maaDabeku antha gottilla.",
        "expected_issue": "Citizen's ration card Aadhaar linking OTP is not being received on the portal",
        "expected_dept": "Food & Civil Supplies",
        "restatement": "Neevu heLidantu, nimage ration card Aadhaar link maduvaga OTP bandilla antha — ide sari tane?",
    },
    {
        "id": "RC002",
        "title": "Ration card name correction (Hindi)",
        "language": "hi",
        "dialect": "standard",
        "sentiment": "calm",
        "transcript": "Mera ration card mein naam galat hai, mere baap ka naam Ramesh hai lekin card mein Suresh likha hai. Isko theek karna hai.",
        "expected_issue": "Citizen's ration card has an incorrect father's name and needs correction",
        "expected_dept": "Food & Civil Supplies",
        "restatement": "Aapne kaha ki aapke ration card mein aapke pita ka naam galat hai — kya yeh sahi hai?",
    },
    {
        "id": "RC003",
        "title": "Ration not received (Dharwad Kannada, urgency)",
        "language": "kn",
        "dialect": "dharwad",
        "sentiment": "urgency",
        "transcript": "Haavudaa, nimdu ration shoppu bittre avru haanu kodalla, kaLeda yerdu tingaLinda ration bandE illa, mane le makkaLu iddare, bEga maaDri help.",
        "expected_issue": "Ration not distributed at the shop for two months — family with children is affected",
        "expected_dept": "Food & Civil Supplies",
        "restatement": "Neevu heLidantu, kaLeda 2 tingaLinda nimma ration shop le ration kodilla antha — ide sari tane?",
    },

    # ── Pension Issues ──────────────────────────────────────────────────────
    {
        "id": "PE001",
        "title": "Sandhya Suraksha pension not received (Mysuru Kannada, distress)",
        "language": "kn",
        "dialect": "mysuru",
        "sentiment": "distress",
        "transcript": "Nodi saar, nange sandhya suraksha pension ee tumhiN bandilla, 3 tingaLu aaytu. Nange bEre yaaro illa, ee haaNa ge aaDEnu. Daya maaDigore help maaDbeku.",
        "expected_issue": "Senior citizen has not received Sandhya Suraksha pension for 3 months — sole income source",
        "expected_dept": "Social Welfare Department",
        "restatement": "Neevu heLidantu, 3 tingaLinda nimage Sandhya Suraksha pension bandilla antha — ide sari tane?",
    },
    {
        "id": "PE002",
        "title": "Pension amount reduced (English)",
        "language": "en",
        "dialect": "standard",
        "sentiment": "confusion",
        "transcript": "My mother is getting Sandhya Suraksha pension but this month the amount came as half of what she usually gets. She is 76 years old and lives alone. Who do I contact about this?",
        "expected_issue": "Pension amount received is half the usual amount for a 76-year-old beneficiary",
        "expected_dept": "Social Welfare Department",
        "restatement": "You said your mother received only half her usual pension amount this month — is that correct?",
    },

    # ── BWSSB Water Supply ──────────────────────────────────────────────────
    {
        "id": "WA001",
        "title": "No water supply - Yelahanka (Kannada, anger)",
        "language": "kn",
        "dialect": "bengaluru",
        "sentiment": "anger",
        "transcript": "Yelahanka new town le 3 dinada inda neeru bandE illa. BWSSB ge phone maaDre yaaroo edee iLLa. Nimdu yaavdu upayogave illa, ivaga janaharu hengE irbekitu.",
        "expected_issue": "No water supply in Yelahanka New Town for 3 days, BWSSB helpline unreachable",
        "expected_dept": "BWSSB",
        "restatement": "Neevu heLidantu, Yelahanka New Town le 3 dinada inda neeru bandu illa antha — ide sari tane?",
    },
    {
        "id": "WA002",
        "title": "Water contamination complaint (Hindi)",
        "language": "hi",
        "dialect": "standard",
        "sentiment": "urgency",
        "transcript": "Hamare area mein jo paani aa raha hai woh bahut ganda hai, kaala rang ka hai aur smell bhi aa rahi hai. Bacche bimar pad rahe hain. Yeh emergency hai please turant action lo.",
        "expected_issue": "Contaminated black water supply causing children to fall ill — emergency situation",
        "expected_dept": "BWSSB",
        "restatement": "Aapne kaha ki aapke area mein kala aur badboodar paani aa raha hai aur bacche bimar hain — kya yeh sahi hai?",
    },

    # ── BBMP Civic Complaints ───────────────────────────────────────────────
    {
        "id": "BB001",
        "title": "Pothole causing accidents (Kannada, anger)",
        "language": "kn",
        "dialect": "bengaluru",
        "sentiment": "anger",
        "transcript": "BEL circle hatra road le tumba doDDa pothole ide, kaLeda vaara eraDu jana biidaru. BBMP ge complaint kodidivi aadre yaavdu action aagilla. Yaaraadru noDiri.",
        "expected_issue": "Large pothole near BEL Circle caused two accidents last week, no BBMP action on complaint",
        "expected_dept": "BBMP",
        "restatement": "Neevu heLidantu, BEL Circle hatra pothole ide, complaint kodidiru aadre action aagilla antha — ide sari tane?",
    },
    {
        "id": "BB002",
        "title": "Garbage collection stopped (English)",
        "language": "en",
        "dialect": "standard",
        "sentiment": "anger",
        "transcript": "The garbage collection in Koramangala 4th block has not happened for 5 days. The garbage is piling up on the road. It is a health hazard. When will BBMP come?",
        "expected_issue": "No garbage collection in Koramangala 4th Block for 5 days — health hazard",
        "expected_dept": "BBMP",
        "restatement": "You said garbage has not been collected in Koramangala 4th Block for 5 days — is that correct?",
    },

    # ── Land Records / Bhoomi ───────────────────────────────────────────────
    {
        "id": "LR001",
        "title": "Bhoomi mutation pending (Kannada, confusion)",
        "language": "kn",
        "dialect": "dharwad",
        "sentiment": "confusion",
        "transcript": "Namma appana hotte jaaga naavu khareedisu maaDdivi, aadare Bhoomi portal le mutation aagli tumba dina aaytu, yaaro heLalla enaaythu antaa. Revenue office ge hogidivi avru nimma file processing antha heltu idare.",
        "expected_issue": "Land mutation pending on Bhoomi portal after purchase — revenue office says processing but no update",
        "expected_dept": "Revenue / Bhoomi",
        "restatement": "Neevu heLidantu, Bhoomi portal le nimma land mutation tumba dina pending ide antha — ide sari tane?",
    },
    {
        "id": "LR002",
        "title": "Encumbrance certificate urgent (Hindi)",
        "language": "hi",
        "dialect": "standard",
        "sentiment": "urgency",
        "transcript": "Mujhe kal bank loan ke liye encumbrance certificate chahiye, Bhoomi portal pe apply kiya tha lekin download nahi ho raha. Kya aap help kar sakte hain? Kal deadline hai.",
        "expected_issue": "Encumbrance certificate for bank loan due tomorrow cannot be downloaded from Bhoomi",
        "expected_dept": "Revenue / Bhoomi",
        "restatement": "Aapne kaha ki kal loan ke liye Bhoomi se encumbrance certificate download nahi ho raha — kya yeh sahi hai?",
    },

    # ── Government Certificates ─────────────────────────────────────────────
    {
        "id": "CE001",
        "title": "Caste certificate delay (Kannada, frustration)",
        "language": "kn",
        "dialect": "mysuru",
        "sentiment": "anger",
        "transcript": "Nanu 2 thumbha dina munde Seva Sindhu le jathi pramanpatra ge apply maadde, innoo aagtailla. Nange college admission ge bEkittu, deadline mugitu haaguttide. Yaakadru maaDalla.",
        "expected_issue": "Caste certificate applied 2 months ago on Seva Sindhu, still pending — college admission deadline approaching",
        "expected_dept": "Revenue Department (Seva Sindhu)",
        "restatement": "Neevu heLidantu, 2 thumbha dina hinde apply maaDida jathi pramanpatra innoo bandilla antha — ide sari tane?",
    },
    {
        "id": "CE002",
        "title": "Income certificate for scholarship (English)",
        "language": "en",
        "dialect": "standard",
        "sentiment": "urgency",
        "transcript": "I applied for an income certificate on Seva Sindhu 3 weeks ago for my daughter's scholarship application. The status says officer approval pending. The scholarship deadline is this Friday. Can you please expedite?",
        "expected_issue": "Income certificate approval pending for 3 weeks, scholarship deadline is Friday",
        "expected_dept": "Revenue Department (Seva Sindhu)",
        "restatement": "You said your daughter's income certificate is stuck in officer approval with a scholarship deadline this Friday — is that correct?",
    },

    # ── High Distress / Emergency ───────────────────────────────────────────
    {
        "id": "EM001",
        "title": "Senior citizen medical emergency - pension not received",
        "language": "kn",
        "dialect": "mysuru",
        "sentiment": "distress",
        "transcript": "Naan 80 varsha hireya. Nange pension ee thumba dina bandilla. Nage mane le yaaro illa. Aushadha kharidkoBEku. Haana illada ee nanu hegE irbEku. DayaviTTu help maaDi.",
        "expected_issue": "80-year-old living alone has not received pension for months, cannot afford medicine — emergency",
        "expected_dept": "Social Welfare Department",
        "restatement": "Neevu heLidantu, nimage pension bandilla, aushadha konDkoBEkagide antha — ide sari tane?",
    },
    {
        "id": "EM002",
        "title": "Flood damage - seeking relief (Kannada, distress)",
        "language": "kn",
        "dialect": "dharwad",
        "sentiment": "distress",
        "transcript": "Namma mane ele neer toretu, ella hoitu, makkaLige uDu tikaLla, serkaara yaavadru help maaDalla, nimde ond saayi maaDli anta aagide, help maaDri.",
        "expected_issue": "House flooded, family has no food or shelter — seeking government relief immediately",
        "expected_dept": "Revenue / Disaster Management",
        "restatement": "Neevu heLidantu, nimma mane ge neeru horadu makkaLige uDubeeDu illa antha — ide sari tane?",
    },

    # ── Mixed Language / Code-switching ────────────────────────────────────
    {
        "id": "MX001",
        "title": "Code-switching Kannada-English (portal issue)",
        "language": "kn",
        "dialect": "bengaluru",
        "sentiment": "confusion",
        "transcript": "Seva Sindhu portal ge login maadidivi but OTP bandu illa. Password reset maadakke hogidivi adoo work aagilla. Yenu maaDodu antha gottilla, please help maaDi.",
        "expected_issue": "Cannot login to Seva Sindhu portal — OTP not received and password reset also not working",
        "expected_dept": "Seva Sindhu / IT Help",
        "restatement": "Neevu heLidantu, Seva Sindhu portal le login aagutilla, OTP bartu illa antha — ide sari tane?",
    },
    {
        "id": "MX002",
        "title": "Kannada-Hindi mix - ration shop closed",
        "language": "kn",
        "dialect": "dharwad",
        "sentiment": "anger",
        "transcript": "Namma area ration shop last 10 days inda band aagide. Shop wala koi baat kare nahi, phone uthate nahi. Makkalgu haaLu naDeda bidilla.",
        "expected_issue": "Ration shop closed for 10 days, shopkeeper not responding, children affected",
        "expected_dept": "Food & Civil Supplies",
        "restatement": "Neevu heLidantu, nimma ration shop 10 dinada inda band ide, yaaro phone eda irtilla antha — ide sari tane?",
    },
]

# Quick lookup
SCENARIOS_BY_ID = {s["id"]: s for s in DEMO_SCENARIOS}
SCENARIOS_BY_CATEGORY = {
    "ration": [s for s in DEMO_SCENARIOS if s["id"].startswith("RC")],
    "pension": [s for s in DEMO_SCENARIOS if s["id"].startswith("PE")],
    "water": [s for s in DEMO_SCENARIOS if s["id"].startswith("WA")],
    "bbmp": [s for s in DEMO_SCENARIOS if s["id"].startswith("BB")],
    "land": [s for s in DEMO_SCENARIOS if s["id"].startswith("LR")],
    "certificate": [s for s in DEMO_SCENARIOS if s["id"].startswith("CE")],
    "emergency": [s for s in DEMO_SCENARIOS if s["id"].startswith("EM")],
    "mixed": [s for s in DEMO_SCENARIOS if s["id"].startswith("MX")],
}
