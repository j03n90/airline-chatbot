from backend.api.schemas import AIRLINE_NAMES, AirlineCode

# Curated chunks transcribed from the supplied Passenger_Policies PDFs.
# Tables are kept whole so retrieval cannot split fee rows.

STA_VERSION = "1.4"
STA_EFFECTIVE_AT = "2026-03-01T00:00:00+00:00"
NSA_VERSION = "2.0"
NSA_EFFECTIVE_AT = "2026-01-01T00:00:00+00:00"
BHA_VERSION = "3.0"
BHA_EFFECTIVE_AT = "2026-07-01T00:00:00+00:00"

POLICY_DOCUMENTS = [
    {"airline": AirlineCode.STA.value, "version": STA_VERSION, "effective_at": STA_EFFECTIVE_AT},
    {"airline": AirlineCode.NSA.value, "version": NSA_VERSION, "effective_at": NSA_EFFECTIVE_AT},
    {"airline": AirlineCode.BHA.value, "version": BHA_VERSION, "effective_at": BHA_EFFECTIVE_AT},
]


def _make_chunk(airline: AirlineCode, version: str, effective_at: str):
    name = AIRLINE_NAMES[airline]
    effective_date = effective_at[:10]

    def chunk(section: str, title: str, page: int, kind: str, text: str) -> dict:
        prefix = (
            f"{name} ({airline.value}) v{version} effective {effective_date} - Section {section} {title}\n\n"
        )
        return {
            "airline_code": airline.value,
            "airline_name": name,
            "version": version,
            "effective_at": effective_at,
            "section": section,
            "title": title,
            "page": page,
            "kind": kind,
            "text": prefix + text.strip(),
        }

    return chunk


_sta = _make_chunk(AirlineCode.STA, STA_VERSION, STA_EFFECTIVE_AT)
_nsa = _make_chunk(AirlineCode.NSA, NSA_VERSION, NSA_EFFECTIVE_AT)
_bha = _make_chunk(AirlineCode.BHA, BHA_VERSION, BHA_EFFECTIVE_AT)

STA = [
    _sta(
        "1",
        "Scope and definitions",
        1,
        "prose",
        """This document applies only to tickets issued by Suntrail Air for flights operated by Suntrail Air.
Domestic means both endpoints of a segment are in the fictional Republic of Aster; all other segments are international.
Route type is assessed per segment for changes and baggage. For voluntary cancellation, an itinerary is international if any segment is international.
Travel has started once any segment on that ticket has been flown. A wholly unused ticket has no flown segments.
All timestamps use UTC. The early window is 24 hours or more before departure, including exactly 24 hours. The late window is less than 24 hours but more than 0 hours. At exactly departure time or later, Section 5 no-show rules apply.
Money is USD.""",
    ),
    _sta(
        "2.1",
        "Change fee schedule",
        2,
        "table",
        """Voluntary change fees apply per passenger, per changed flight segment, per completed change request.
Suntrail Air distinguishes domestic and international segments.

| Fare | Early (at least 24 hours) | Late (more than 0, less than 24 hours) |
| Economy Basic | Domestic USD 40; international not permitted | Not permitted |
| Economy Standard | Domestic USD 20; international USD 65 | Domestic USD 50; international USD 100 |
| Economy Flex | USD 0 on either route type | Domestic USD 0; international USD 25 |

Example: one Economy Standard traveler changes one domestic and one international segment, both 30 hours before departure. Fees are USD 20 + USD 65 = USD 85. Positive fare differences are additional.
A lower replacement fare creates no refund and cannot offset a change fee.
You may retain or upgrade the fare type, but not downgrade it. Airline, passenger and route endpoint substitutions are not voluntary changes.""",
    ),
    _sta(
        "3",
        "Voluntary cancellation and refunds",
        3,
        "table",
        """Cancellation fees are per passenger, per wholly unused itinerary, not per segment.

| Fare | Early | Late |
| Economy Basic | No fare refund or credit | No fare refund or credit |
| Economy Standard | Domestic credit less USD 25; international no fare refund or credit | No fare refund or credit |
| Economy Flex | Domestic original payment, USD 0 fee; international original payment less USD 50 | Domestic original payment less USD 20; international credit less USD 75 |

Unused government taxes are returned to the original payment method on request for every fare, including non-refundable fares and no-shows.
Purchased baggage and seat extras are non-refundable for a voluntary cancellation.
A travel credit expires 365 elapsed days after issue and cannot be transferred or exchanged for cash.""",
    ),
    _sta(
        "5",
        "No-shows",
        3,
        "prose",
        """A traveler is a no-show if no complete authorized change/cancellation request was received before departure and the traveler does not take that flight.
At exactly departure time, a new voluntary request is too late.
All remaining segments are suspended pending service-desk contact; there is no automatic reinstatement.
The remaining fare has no standard refund or credit, including Flex. Unused government taxes remain refundable.""",
    ),
    _sta(
        "6",
        "Airline-initiated disruptions",
        4,
        "prose",
        """A cancellation by Suntrail Air qualifies for all fare types.
A schedule change qualifies when the absolute difference between the original and revised scheduled departure time is 120 minutes or more, including exactly 120 minutes.
Replacement travel: one rebooking on this airline to the same destination in the same fare type, within 7 calendar days, no change fee or fare difference.
Refund before travel starts: full fare, unused taxes and unused extras to original payment. No cancellation fee, including Economy Basic.
Submit the choice within 30 elapsed days after the disruption notice.""",
    ),
    _sta(
        "7",
        "Cabin and checked baggage",
        5,
        "table",
        """Each passenger has one free personal item up to 40 x 30 x 15 cm and 3 kg. Cabin bags max 55 x 35 x 25 cm. Checked bags max 158 cm linear.
Allowances are per passenger on each segment and cannot be pooled.

| Fare | Cabin bag | Checked |
| Economy Basic | 1 cabin bag, 7 kg | Domestic: none; international: 1 bag, 20 kg |
| Economy Standard | 1 cabin bag, 10 kg | Domestic: 1 bag, 20 kg; international: 1 bag, 23 kg |
| Economy Flex | 1 cabin bag, 12 kg | Domestic: 2 bags, 20 kg each; international: 2 bags, 23 kg each |

A second cabin bag cannot be purchased. One additional checked bag may be purchased for USD 50 per passenger per segment (23 kg, 158 cm).
Example: Economy Basic includes no checked bag on an Aster domestic segment and one 20 kg checked bag on an international segment.""",
    ),
    _sta(
        "8",
        "Booking ownership and requests",
        6,
        "prose",
        """The named adult traveler may request service for their own ticket after identity and booking details are verified.
A booking reference, shared surname, or possession of payment details alone is not authority.
A payer or lead booker may not change, cancel or view another adult traveler's private ticket information without that traveler's explicit authorization.
A quote alone does not alter a booking. Confirm the quoted change or cancellation before execution.
Contact: https://service.suntrail-air.example or care@suntrail-air.example (fictional).""",
    ),
    _sta(
        "9",
        "Exceptions requiring manual review",
        6,
        "prose",
        """Manual review is required for: serious medical events; partly used itinerary refunds; selected-segment cancellations; mixed-fare tickets; disputed ownership; guardianship for a minor.
Lounge access, pet transport, loyalty benefits and unaccompanied-minor travel are not documented here. Contact the service desk; absence of a rule is neither permission nor a prohibition.""",
    ),
]

NSA = [
    _nsa(
        "1",
        "Scope and definitions",
        1,
        "prose",
        """This document applies only to tickets issued by Northstar Air for flights operated by Northstar Air.
Domestic means both endpoints are in the Republic of Aster. Early window: 24 hours or more. Late window: less than 24 hours but more than 0. At departure or later: no-show.
Northstar Air is a full-service airline. Change fees do not vary by domestic vs international route except where cancellation itinerary type is defined.""",
    ),
    _nsa(
        "2.1",
        "Change fee schedule",
        2,
        "table",
        """Fees apply per passenger, per changed flight segment.

| Fare | Early (at least 24 hours) | Late (more than 0, less than 24 hours) |
| Economy Basic | USD 70 | Not permitted |
| Economy Standard | USD 25 | USD 60 |
| Economy Flex | USD 0 | USD 0 |

Example: two Economy Standard travelers change two segments each in the early window. Fees are 2 x 2 x USD 25 = USD 100.
Every permitted change also requires payment of any positive fare difference. A lower fare creates no refund.
Northstar Economy Flex changes are free in both the early and late windows, still subject to fare difference.""",
    ),
    _nsa(
        "3",
        "Voluntary cancellation and refunds",
        3,
        "table",
        """| Fare | Early | Late |
| Economy Basic | No fare refund or credit | No fare refund or credit |
| Economy Standard | Travel credit less USD 40 | Travel credit less USD 80 |
| Economy Flex | Original payment; USD 0 fee | Original payment; USD 0 fee |

Northstar Economy Flex voluntary cancellation returns the fare to the original payment method with no fee in both windows.
Unused government taxes are refundable for every fare. Purchased extras are not refundable on a voluntary cancellation.
Credits expire in 365 days, named to the passenger, not transferable, this airline only.""",
    ),
    _nsa(
        "5",
        "No-shows",
        3,
        "prose",
        """At exactly departure time a new voluntary request is too late and receives no-show treatment.
Remaining segments are suspended. Remaining fare has no standard refund or credit, including Flex. Unused taxes remain refundable.""",
    ),
    _nsa(
        "6",
        "Airline-initiated disruptions",
        4,
        "prose",
        """Northstar Air cancellation qualifies for all fares. A schedule change qualifies at 120 minutes or more, including exactly 120 minutes.
Replacement travel within 7 calendar days, same fare type, no change fee or fare difference.
Wholly unused affected itinerary: refund full fare, unused taxes and unused extras, no cancellation fee including Economy Basic.""",
    ),
    _nsa(
        "7",
        "Cabin and checked baggage",
        5,
        "table",
        """Personal item 40 x 30 x 15 cm, 3 kg. Cabin 55 x 35 x 25 cm. Checked 158 cm linear.

| Fare | Cabin bag | Checked |
| Economy Basic | 1 cabin bag, 8 kg | 1 bag, 23 kg |
| Economy Standard | 1 cabin bag, 8 kg | 1 bag, 23 kg |
| Economy Flex | 1 cabin bag, 12 kg | 2 bags, 23 kg each |

One additional checked bag USD 45 per passenger per segment, 23 kg. A second cabin bag cannot be purchased.
A Flex traveler may carry two separate 23 kg bags; a single 30 kg bag exceeds the per-bag limit even if combined allowance is 46 kg.""",
    ),
    _nsa(
        "8",
        "Booking ownership and requests",
        6,
        "prose",
        """Named adult traveler only, after identity and booking details are verified.
A booking reference, shared surname, or payment details alone is not authority.
Quote must be confirmed before execution. Contact: https://service.northstar-air.example or care@northstar-air.example.""",
    ),
    _nsa(
        "9",
        "Exceptions requiring manual review",
        6,
        "prose",
        """Medical events, partly used refunds, selected-segment cancellations, mixed-fare tickets, disputed ownership and guardianship require review.
Lounge, pets, loyalty and unaccompanied minors are not covered in this publication.""",
    ),
]

BHA = [
    _bha(
        "1",
        "Scope and definitions",
        1,
        "prose",
        """Bluehaven Airways is a low-cost airline. Except for the issuance-based fee in Appendix A, rules apply regardless of original ticket issuance date.
Early window 24 hours or more. Late window less than 24 hours but more than 0. Departure or later: no-show.
Domestic: both endpoints in the Republic of Aster.""",
    ),
    _bha(
        "2.1",
        "Change fee schedule",
        2,
        "table",
        """| Fare | Early (at least 24 hours) | Late |
| Economy Basic | Not permitted | Not permitted |
| Economy Standard | USD 55 current / USD 85 previous | Not permitted |
| Economy Flex | USD 15 | USD 45 |

Bluehaven Economy Basic cannot be changed in any window.
Economy Standard cannot be changed in the late window.
Standard issuance rule: tickets originally issued before 2026-07-01 00:00:00 UTC pay USD 85; those issued at or after that instant pay USD 55. Both apply only in the early window. The request date or reissue date does not select the fee.""",
    ),
    _bha(
        "Appendix A",
        "Economy Standard change-fee update",
        6,
        "table",
        """Appendix A. Economy Standard change-fee update for Bluehaven Airways.

| Original ticket issuance (UTC) | Early-window change fee |
| Previous rule: before 2026-07-01 00:00:00 | USD 85 per passenger per changed segment |
| Current rule: at or after 2026-07-01 00:00:00 | USD 55 per passenger per changed segment |

The late-window prohibition is unchanged. Positive fare differences still apply. The original issuance timestamp survives reissue.""",
    ),
    _bha(
        "3",
        "Voluntary cancellation and refunds",
        3,
        "table",
        """| Fare | Early | Late |
| Economy Basic | No fare refund or credit | No fare refund or credit |
| Economy Standard | No fare refund or credit | No fare refund or credit |
| Economy Flex | Travel credit less USD 30 | No fare refund or credit |

Bluehaven Economy Standard never receives a fare refund or credit on a voluntary cancellation. Unused taxes are still refundable.
Economy Flex only receives a travel credit (less USD 30) in the early window.""",
    ),
    _bha(
        "5",
        "No-shows",
        3,
        "prose",
        """No-show at departure or later. Remaining fare has no standard refund or credit, including Flex. Unused taxes remain refundable.""",
    ),
    _bha(
        "6",
        "Airline-initiated disruptions",
        4,
        "prose",
        """A cancellation by Bluehaven Airways qualifies for all fare types.
A schedule change qualifies when the absolute difference is 180 minutes or more, including exactly 180 minutes. A 120-minute change does not qualify on Bluehaven.
Replacement travel within 7 calendar days, no change fee or fare difference.
Refund before travel starts: full fare, unused taxes and unused extras, no cancellation fee including Economy Basic.""",
    ),
    _bha(
        "7",
        "Cabin and checked baggage",
        5,
        "table",
        """Personal item 40 x 30 x 15 cm, 3 kg.

| Fare | Cabin bag | Checked |
| Economy Basic | No cabin bag | No checked bag |
| Economy Standard | 1 cabin bag, 7 kg | No checked bag |
| Economy Flex | 1 cabin bag, 10 kg | 1 bag, 20 kg |

Bluehaven Economy Basic has no included cabin or checked bag. Economy Basic may purchase one cabin bag up to 7 kg for USD 25 per passenger per segment.
One additional checked bag USD 40 per passenger per segment, 20 kg. Standard and Flex cannot purchase a second cabin bag.
Example: a Standard traveler taking two segments with one 18 kg checked bag pays 2 x USD 40 = USD 80.""",
    ),
    _bha(
        "8",
        "Booking ownership and requests",
        6,
        "prose",
        """Named adult traveler after identity and booking details are verified. PNR plus surname alone is not authority.
Contact: https://service.bluehaven-airways.example or care@bluehaven-airways.example.""",
    ),
    _bha(
        "9",
        "Exceptions requiring manual review",
        6,
        "prose",
        """Medical events, partly used refunds, selected-segment cancellations, mixed-fare, ownership disputes and guardianship require review.
Pets, lounge, loyalty and unaccompanied minors are not covered.""",
    ),
]

CORPUS = {
    AirlineCode.STA.value: STA,
    AirlineCode.NSA.value: NSA,
    AirlineCode.BHA.value: BHA,
}
