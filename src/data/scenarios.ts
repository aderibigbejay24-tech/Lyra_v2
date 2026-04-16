export type Scenario = "clean" | "vague" | "hostile";

export interface LeadScenario {
  id: Scenario;
  label: string;
  customer: {
    name: string | null;
    email: string;
    phone: string | null;
    initials: string;
  };
  vehicle: {
    year: number | null;
    make: string | null;
    model: string | null;
    trim: string | null;
    vin: string | null;
    stock: string | null;
    price: number | null;
  };
  message: string;
  parseDegraded: boolean;
  escalate: boolean;
  escalationReason: string | null;
  draft: {
    subject: string;
    body: string;
    repName: string;
    repRole: string;
    confidence: number;
    financingAngle: string;
    toneCheck: string;
    costEstimate: string;
  } | null;
  inventoryMatch: {
    year: number;
    make: string;
    model: string;
    trim: string;
    mileage: string;
    color: string;
    price: string;
    stock: string;
    highlights: string[];
  } | null;
  bookingRep: {
    name: string;
    role: string;
    initials: string;
    date: string;
    time: string;
    vehicle: string;
    confirmationNumber: string;
  };
  auditOutcome: string;
}

export const SCENARIOS: Record<Scenario, LeadScenario> = {
  clean: {
    id: "clean",
    label: "Scenario A — Clean ADF",
    customer: {
      name: "Priya Singh",
      email: "priya.singh@example.com",
      phone: "403-555-0199",
      initials: "PS",
    },
    vehicle: {
      year: 2020,
      make: "Honda",
      model: "Accord",
      trim: "Sport 1.5T",
      vin: "1HGCV1F34LA012345",
      stock: "FN-24-0112",
      price: 26995,
    },
    message:
      "Hi, is this Accord still available? I'd like to know if there's any wiggle room on price and whether you offer financing. I can come by this Saturday if it works.",
    parseDegraded: false,
    escalate: false,
    escalationReason: null,
    draft: {
      subject: "Re: Your inquiry about the 2020 Honda Accord Sport 1.5T — FN-24-0112",
      body: `Hi Priya,

Thanks for reaching out about the 2020 Honda Accord Sport 1.5T (stock FN-24-0112). Great news — it's still available!

On pricing, we have a bit of flexibility depending on financing vs. cash. We do offer financing through several lenders, and we can often get you into a very competitive rate.

Saturday works great for us. Our lot is open 9 AM – 5 PM. Would you like to book a 1:00 PM test drive slot? I can have the car pulled and ready.

Looking forward to meeting you,
Foster Kielce | Fornest Automotive`,
      repName: "Foster Kielce",
      repRole: "Sales Lead",
      confidence: 0.87,
      financingAngle: "financing_highlight",
      toneCheck: "warm_professional",
      costEstimate: "$0.0012",
    },
    inventoryMatch: {
      year: 2020,
      make: "Honda",
      model: "Accord",
      trim: "Sport 1.5T",
      mileage: "54,200 km",
      color: "Sonic Gray Pearl",
      price: "$26,995",
      stock: "FN-24-0112",
      highlights: [
        "1.5L Turbocharged engine",
        "Apple CarPlay / Android Auto",
        "Heated front seats",
        "Honda Sensing suite",
        "One previous owner",
        "Clean CarFax — no accidents",
      ],
    },
    bookingRep: {
      name: "Ben Adeyemi",
      role: "Finance Manager",
      initials: "BA",
      date: "Saturday, April 18",
      time: "1:00 PM",
      vehicle: "2020 Honda Accord Sport 1.5T",
      confirmationNumber: "FN-BK-2024-4421",
    },
    auditOutcome: "booked",
  },
  vague: {
    id: "vague",
    label: "Scenario B — Vague Edge Case",
    customer: {
      name: null,
      email: "buyer99@example.com",
      phone: null,
      initials: "?",
    },
    vehicle: {
      year: null,
      make: null,
      model: null,
      trim: null,
      vin: null,
      stock: null,
      price: null,
    },
    message: "is this still for sale thx",
    parseDegraded: true,
    escalate: false,
    escalationReason: null,
    draft: {
      subject: "Re: Your vehicle inquiry — Fornest Automotive",
      body: `Hi there,

Thanks for reaching out to Fornest Automotive! We'd love to help you find the right vehicle.

Could you let us know which listing you're asking about? A stock number, year/make/model, or even the listing URL would be perfect.

Also, what's the best number to reach you? Our team is standing by and we can usually have a test drive booked within a few hours.

We look forward to hearing from you!
Foster Kielce | Fornest Automotive`,
      repName: "Foster Kielce",
      repRole: "Sales Lead",
      confidence: 0.41,
      financingAngle: "clarification_needed",
      toneCheck: "warm_neutral",
      costEstimate: "$0.0008",
    },
    inventoryMatch: null,
    bookingRep: {
      name: "Foster Kielce",
      role: "Sales Lead",
      initials: "FK",
      date: "Saturday, April 18",
      time: "2:00 PM",
      vehicle: "To be determined",
      confirmationNumber: "FN-BK-2024-4422",
    },
    auditOutcome: "clarification_requested",
  },
  hostile: {
    id: "hostile",
    label: "Scenario C — Hostile Escalation",
    customer: {
      name: "Jordan",
      email: "jordan.escalation@example.com",
      phone: "403-555-0888",
      initials: "JO",
    },
    vehicle: {
      year: 2019,
      make: "BMW",
      model: "330i",
      trim: "xDrive",
      vin: "WBA8E9G55KNU12345",
      stock: "FN-24-0155",
      price: 38990,
    },
    message:
      "3rd time I've emailed. If I don't hear back in 24h I am reporting you to AMVIC and filing a complaint with the BBB. My lawyer is aware.",
    parseDegraded: false,
    escalate: true,
    escalationReason:
      "Legal threat detected (AMVIC, BBB, lawyer). Prior contact count: 3. Requires immediate human intervention — do not auto-reply.",
    draft: null,
    inventoryMatch: {
      year: 2019,
      make: "BMW",
      model: "330i",
      trim: "xDrive",
      mileage: "72,100 km",
      color: "Alpine White",
      price: "$38,990",
      stock: "FN-24-0155",
      highlights: [
        "2.0L TwinPower Turbo",
        "M Sport package",
        "Panoramic sunroof",
        "Harman Kardon sound",
        "All-wheel drive",
        "Clean CarFax",
      ],
    },
    bookingRep: {
      name: "Sam Nakamura",
      role: "General Manager",
      initials: "SN",
      date: "Saturday, April 18",
      time: "10:00 AM",
      vehicle: "2019 BMW 330i xDrive",
      confirmationNumber: "FN-BK-2024-4423",
    },
    auditOutcome: "escalated",
  },
};
