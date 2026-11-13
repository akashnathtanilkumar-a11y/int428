import json

class ProductionRuleEngine:
    """IF-THEN production rules over a JSON knowledge base."""
    def __init__(self, kb_path: str):
        with open(kb_path, "r", encoding="utf-8") as f:
            self.kb = json.load(f)

    def evaluate(self, intent: str, ctx: dict) -> tuple[str, bool]:
        """Returns (response_text, is_answered)."""
        prog = ctx.get("programme")
        marks = ctx.get("marks")
        cat = ctx.get("category") or "General"
        hostel_type = ctx.get("hostel_type")

        # Greeting
        if intent == "greeting":
            return (
                f"Namaste! Welcome to {self.kb['college_info']['name']} Admission Helpdesk. "
                "Ask me about programmes, eligibility, fees, hostel facilities, scholarships, documents, or deadlines.",
                True
            )

        # Programmes offered
        if intent == "programmes":
            if prog and prog in self.kb["programmes"]:
                p = self.kb["programmes"][prog]
                return (
                    f"**{p['full_name']} ({prog})**\n"
                    f"- Duration: {p['duration']}\n"
                    f"- Total Intake: {p['seats']} seats\n"
                    f"- Annual Tuition Fee: ₹{p['annual_fee']:,}\n"
                    f"- Eligibility: {p['eligibility_details']}",
                    True
                )
            lines = ["We offer the following programmes for the 2026-27 academic session:"]
            for code, info in self.kb["programmes"].items():
                lines.append(f"- **{code}**: {info['full_name']} ({info['duration']}) — ₹{info['annual_fee']:,}/year")
            return ("\n".join(lines), True)

        # Eligibility criteria
        if intent == "eligibility":
            p = self.kb["programmes"][prog]
            req_marks = p["min_marks"].get(cat, p["min_marks"]["General"])
            if marks is not None:
                if marks >= req_marks:
                    return (
                        f"Yes! With **{marks}%** ({cat} category), you meet the minimum requirement of **{req_marks}%** for **{prog}**.\n"
                        f"Additional requirement: {p['eligibility_details']}",
                        True
                    )
                else:
                    return (
                        f"Unfortunately, **{marks}%** falls short of the **{req_marks}%** minimum cut-off required for **{prog}** under the **{cat}** category.",
                        True
                    )
            return (
                f"**Eligibility for {prog} ({cat} Category):**\n"
                f"- Minimum Marks Required: **{req_marks}%**\n"
                f"- Criteria: {p['eligibility_details']}\n"
                f"*(Share your 10+2/Graduation percentage if you want me to check your exact eligibility.)*",
                True
            )

        # Fee structure
        if intent == "fees":
            p = self.kb["programmes"][prog]
            return (
                f"**Fee Structure for {p['full_name']} ({prog}):**\n"
                f"- Annual Tuition Fee: **₹{p['annual_fee']:,}**\n"
                f"- Payable in two semester instalments of **₹{p['annual_fee']//2:,}** each.",
                True
            )

        # Hostel facilities
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
                    True
                )
            lines = ["We provide separate on-campus hostels for boys and girls:"]
            for h_key, h in self.kb["hostel"].items():
                lines.append(f"- **{h_key} ({h['type']})**: ₹{h['annual_fee']:,}/yr room + ₹{h['mess_fee']:,}/yr mess")
            return ("\n".join(lines), True)

        # Scholarships
        if intent == "scholarships":
            lines = ["**Available Scholarships & Financial Aid:**"]
            for s in self.kb["scholarships"]:
                lines.append(f"- **{s['name']}**: {s['benefit']} *(Criteria: {s['criteria']})*")
            return ("\n".join(lines), True)

        # Required documents
        if intent == "documents":
            docs = "\n".join([f"- {d}" for d in self.kb["documents"]])
            return (f"**Mandatory Documents for Admission Verification:**\n{docs}", True)

        # Admission deadlines
        if intent == "deadlines":
            d = self.kb["deadlines"]
            return (
                "**2026 Admission Schedule:**\n"
                f"- Online Applications Open: **{d['application_start']}**\n"
                f"- Last Date to Apply: **{d['application_end']}**\n"
                f"- Counselling & Seat Allotment: **{d['entrance_counselling']}**\n"
                f"- Classes Commence: **{d['session_commencement']}**",
                True
            )

        # Fallback
        return (
            "I couldn't match that to our admission rules. Please ask about **programmes, eligibility, fee structure, hostel facilities, scholarships, documents, or admission deadlines**.",
            False
        )