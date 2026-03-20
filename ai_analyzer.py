import base64
import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)

from openai import OpenAI

SYSTEM_PROMPT = """You are a senior certified property defect inspector in India with 20+ years of experience
inspecting residential flats, apartments, and independent houses before purchase or rental.

You have deep knowledge of common Indian construction defects including:
- RCC (Reinforced Cement Concrete) issues
- Plastering and paint failures
- Indian-climate-specific water seepage and dampness
- Indian plumbing and electrical standards
- Tile and flooring issues common in Indian properties
- Structural settlement cracks vs cosmetic cracks

Your inspection must be thorough, professional, and actionable. Even subtle or minor defects
must be reported — a buyer deserves to know everything before spending lakhs/crores on a property."""

ANALYSIS_PROMPT = """TASK: Perform a comprehensive flat/property inspection analysis on this image.

You are inspecting this property on behalf of a potential buyer. Look for ALL of the following:

STRUCTURAL DEFECTS:
- Wall cracks (hairline, minor, major, diagonal, horizontal, vertical)
- Ceiling cracks or sagging
- Floor cracks or settlement
- Column or beam cracks
- Signs of foundation issues

WATER & MOISTURE DEFECTS:
- Water seepage or dampness patches
- Water stains (brown/yellow marks on walls/ceiling)
- Efflorescence (white salt deposits on walls)
- Peeling plaster due to moisture
- Signs of previous flooding or waterlogging

PAINT & PLASTERING DEFECTS:
- Peeling, bubbling, or flaking paint
- Uneven or lumpy plastering
- Discoloration or patchy paint
- Paint blistering

MOLD & BIOLOGICAL GROWTH:
- Black mold spots
- Green algae or fungal growth
- Musty/damp patches indicating hidden mold

TILE & FLOORING DEFECTS:
- Cracked, chipped, or broken tiles
- Loose or hollow tiles (tile lippage)
- Missing grout or deteriorated grout joints
- Scratched, warped, or damaged flooring
- Uneven floor surface

DOOR & WINDOW DEFECTS:
- Misaligned or sticking doors/windows
- Damaged door/window frames
- Broken or rusted grills/handles
- Gaps in door/window frames (sealing issues)
- Broken glass panes

PLUMBING VISIBLE ISSUES:
- Exposed or damaged pipes
- Water stains near pipe junctions
- Rusted or corroded fixtures
- Signs of past leakage near plumbing

ELECTRICAL VISIBLE ISSUES:
- Exposed or damaged wiring
- Damaged switchboards or sockets
- Burn marks near electrical points
- Missing switch covers or socket covers

CEILING DEFECTS:
- Sagging or bulging ceiling
- Water stains or seepage marks on ceiling
- Flaking or peeling ceiling paint
- Cracks along ceiling-wall junction

VENTILATION & SAFETY:
- Blocked or missing ventilation
- Damaged balcony railings or grills
- Any general wear indicating neglect or age

---

Return ONLY a valid JSON object (no markdown, no code block, no explanation):

{
  "defects": [
    {
      "category": "<category from allowed list>",
      "description": "<precise, specific description of the defect>",
      "location": "<exact location in image, e.g. bottom-left wall near floor>",
      "severity": "<minor|moderate|major>",
      "buyer_impact": "<what this means for a buyer — cost implication or safety risk>",
      "action_required": "<specific remediation steps and urgency>"
    }
  ],
  "overall_condition": "<good|fair|poor>",
  "buyer_recommendation": "<buy|negotiate|avoid>",
  "summary": "<2-3 sentence professional assessment for a potential buyer>"
}

ALLOWED CATEGORIES: Cracks, Water Damage / Seepage, Paint Defects, Mold / Mildew,
Tile Defects, Door & Window Defects, Flooring Defects, Ceiling Defects,
Plumbing Issues, Electrical Issues, Structural Concerns, General Wear & Tear,
Ventilation Issues, Safety Hazards.

SEVERITY GUIDE:
- minor:    Cosmetic only, no structural risk, fix cost < Rs.5,000
- moderate: Functional issue or will worsen, fix cost Rs.5,000-Rs.50,000
- major:    Structural/safety risk or active damage, fix cost > Rs.50,000

IMPORTANT: Be SENSITIVE to subtle defects. Even hairline cracks, slight discoloration,
minor tile chips, small damp patches, or barely visible stains MUST be reported as minor defects.
A buyer pays crores — report everything you see, no matter how small.

If absolutely no defects visible, return empty defects array with overall_condition "good"
and buyer_recommendation "buy".

Return ONLY valid JSON — nothing else."""


def analyze_image(image_path: str) -> dict:
    """Analyze a property image using OpenAI GPT-4o Vision."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set in .env file.")

    ext = Path(image_path).suffix.lower()
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    media_type = media_types.get(ext, "image/jpeg")

    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=2048,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{image_data}",
                            "detail": "high",
                        },
                    },
                    {"type": "text", "text": ANALYSIS_PROMPT},
                ],
            },
        ],
    )

    text = response.choices[0].message.content.strip()
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group())
            except json.JSONDecodeError:
                result = {"defects": [], "overall_condition": "unknown",
                          "buyer_recommendation": "negotiate",
                          "summary": "Analysis could not be parsed."}
        else:
            result = {"defects": [], "overall_condition": "unknown",
                      "buyer_recommendation": "negotiate",
                      "summary": "Analysis could not be completed."}

    for d in result.get("defects", []):
        if "buyer_impact" not in d:
            d["buyer_impact"] = "Requires further evaluation"

    return result
