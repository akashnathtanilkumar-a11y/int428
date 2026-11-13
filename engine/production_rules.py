import json

class ProductionRuleEngine:
    """Explicit Unit II IF-THEN Production Rules over structured JSON Knowledge Base."""
    def __init__(self, kb_path: str):
        with open(kb_path, "r", encoding="utf-8") as f:
            self.kb = json.load(f)

    def evaluate(self, intent: str, ctx: dict) -> tuple[str, bool, str]:
        """Returns (response_text, is_answered, fired_rule_trace)."""
        prog = ctx.get("programme")
        marks = ctx.get("marks")
        cat = ctx.get("category") or "General"
        hostel_type = ctx.get("hostel_type")

        # RULE 1: Greeting
        if intent == "greeting":
            return (
                f"Namaste! Welcome to {self.kb['college_info']['name']} Admission Helpdesk. "
                "Ask me about programmes, eligibility, fees, hostel facilities, scholarships, documents, or deadlines.",
                True,
                "RULE_1_GREETING (IF intent == 'greeting' THEN return welcome_prompt)"
            )

        # RULE 2: Programmes Offered
        if intent == "programmes":
            if prog and prog in self.kb["programmes"]:
                p = self.kb["programmes"][prog]
                return (
                    f"**{p['full_name']} ({prog})**\n"
                    f"- Duration: {p['duration']}\n"
                    f"- Total Intake: {p['seats']} seats\n"
                    f"- Annual Tuition Fee: ₹{p['annual_fee']:,}\n"
                    f"- Eligibility: {p['eligibility_details']}",
                    True,
                    f"RULE_2A_PROGRAMME_DETAIL (IF intent == 'programmes' AND programme == '{prog}' THEN lookup_programme_kb)"
                )
            lines = ["We offer the following programmes for the 2026-27 academic session:"]
            for code, info in self.kb["programmes"].items():
                lines.append(f"- **{code}**: {info['full_name']} ({info['duration']}) — ₹{info['annual_fee']:,}/year")
            return (
                "\n".join(lines),
                True,
                "RULE_2B_PROGRAMME_LIST (IF intent == 'programmes' AND programme IS NULL THEN list_all_programmes)"
            )

        # RULE 3: Eligibility Criteria
        if intent == "eligibility":
            p = self.kb["programmes"][prog]
            req_marks = p["min_marks"].get(cat, p["min_marks"]["General"])
            if marks is not None:
                if marks >= req_marks:
                    return (
                        f"Yes! With **{marks}%** ({cat} category), you meet the minimum requirement of **{req_marks}%** for **{prog}**.\n"
                        f"Additional requirement: {p['eligibility_details']}",
                        True,
                        f"RULE_3A_ELIGIBILITY_PASS (IF intent == 'eligibility' AND marks[{marks}] >= min_marks[{prog}][{cat}][{req_marks}] THEN eligible)"
                    )
                else:
                    return (
                        f"Unfortunately, **{marks}%** falls short of the **{req_marks}%** minimum cut-off required for **{prog}** under the **{cat}** category.",
                        True,
                        f"RULE_3B_ELIGIBILITY_FAIL (IF intent == 'eligibility' AND marks[{marks}] < min_marks[{prog}][{cat}][{req_marks}] THEN ineligible)"
                    )
            return (
                f"**Eligibility for {prog} ({cat} Category):**\n"
                f"- Minimum Marks Required: **{req_marks}%**\n"
                f"- Criteria: {p['eligibility_details']}\n"
                f"*(Share your 10+2/Graduation percentage if you want me to check your exact eligibility.)*",
                True,
                f"RULE_3C_ELIGIBILITY_CRITERIA (IF intent == 'eligibility' AND programme == '{prog}' AND marks IS NULL THEN show_cutoff)"
            )

        # RULE 4: Fee Structure
        if intent == "fees":
            p = self.kb["programmes"][prog]
            return (
                f"**Fee Structure for {p['full_name']} ({prog}):**\n"
                f"- Annual Tuition Fee: **₹{p['annual_fee']:,}**\n"
                f"- Payable in two semester instalments of **₹{p['annual_fee']//2:,}** each.",
                True,
                f"RULE_4_FEES (IF intent == 'fees' AND programme == '{prog}' THEN lookup_annual_fee)"
            )

        # RULE 5: Hostel Facilities
        if intent == "hostel":
            if hostel_type and hostel_type in self.kb["hostel"]:
                h = self.kb["hostel"][hostel_type]
                total = h["annual_fee"] + h["mess_fee"]
                return (
                    f"**Hostel Details ({h['type']}):**\n"
                    f"- Room Rent: ₹{h['annual_fee']:,}/year\n"
                    f"- Mess Charges: ₹{h['mess_fee']:,}/year\n"
                    f"- **Total Annual Hostel + Mess Fee:** ₹{total:,}\n"
                    f"- Amenities: {h['amenities']}",
                    True,
                    f"RULE_5A_HOSTEL_SPECIFIC (IF intent == 'hostel' AND hostel_type == '{hostel_type}' THEN lookup_hostel_kb)"
                )
            lines = ["We provide separate on-campus hostels for boys and girls:"]
            for h_key, h in self.kb["hostel"].items():
                lines.append(f"- **{h_key} ({h['type']})**: ₹{h['annual_fee']:,}/yr room + ₹{h['mess_fee']:,}/yr mess")
            return (
                "\n".join(lines),
                True,
                "RULE_5B_HOSTEL_OVERVIEW (IF intent == 'hostel' AND hostel_type IS NULL THEN list_hostel_options)"
            )

        # RULE 6: Scholarships
        if intent == "scholarships":
            lines = ["**Available Scholarships & Financial Aid:**"]
            for s in self.kb["scholarships"]:
                lines.append(f"- **{s['name']}**: {s['benefit']} *(Criteria: {s['criteria']})*")
            return (
                "\n".join(lines),
                True,
                "RULE_6_SCHOLARSHIPS (IF intent == 'scholarships' THEN list_scholarships_kb)"
            )

        # RULE 7: Required Documents
        if intent == "documents":
            docs = "\n".join([f"- {d}" for d in self.kb["documents"]])
            return (
                f"**Mandatory Documents for Admission Verification:**\n{docs}",
                True,
                "RULE_7_DOCUMENTS (IF intent == 'documents' THEN list_documents_kb)"
            )

        # RULE 8: Admission Deadlines
        if intent == "deadlines":
            d = self.kb["deadlines"]
            return (
                "**2026 Admission Schedule:**\n"
                f"- Online Applications Open: **{d['application_start']}**\n"
                f"- Last Date to Apply: **{d['application_end']}**\n"
                f"- Counselling & Seat Allotment: **{d['entrance_counselling']}**\n"
                f"- Classes Commence: **{d['session_commencement']}**",
                True,
                "RULE_8_DEADLINES (IF intent == 'deadlines' THEN lookup_deadlines_kb)"
            )

        # RULE 9: Fallback
        return (
            "I couldn't match that to our admission rules. Please ask about **programmes, eligibility, fee structure, hostel facilities, scholarships, documents, or admission deadlines**.",
            False,
            "RULE_9_FALLBACK (IF no_intent_matched THEN trigger_graceful_fallback)"
        )