"""CampusCare AI - Campus Wayfinding & Navigation Engine.

Provides exact topological location resolution, shortest path calculation (Dijkstra),
and turn-by-turn walking directions for campus landmarks, laboratories, classrooms,
administrative offices, hostels, and amenities.
"""

import math
from typing import Dict, Any, List, Optional, Tuple


class CampusLocation:
    def __init__(
        self,
        node_id: str,
        name: str,
        aliases: List[str],
        building: str,
        floor: str,
        room: str,
        category: str,
        coordinates: Tuple[int, int],  # (x, y) on campus 100x100 grid
        description: str,
        operating_hours: str = "8:00 AM - 8:00 PM",
        nearest_landmark: str = "",
    ):
        self.node_id = node_id
        self.name = name
        self.aliases = [a.lower() for a in aliases]
        self.building = building
        self.floor = floor
        self.room = room
        self.category = category
        self.coordinates = coordinates
        self.description = description
        self.operating_hours = operating_hours
        self.nearest_landmark = nearest_landmark

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "name": self.name,
            "building": self.building,
            "floor": self.floor,
            "room": self.room,
            "category": self.category,
            "coordinates": {"x": self.coordinates[0], "y": self.coordinates[1]},
            "description": self.description,
            "operating_hours": self.operating_hours,
            "nearest_landmark": self.nearest_landmark,
        }


# Comprehensive Pilot Campus Map Catalog (Apex Institute of Technology)
CAMPUS_LOCATIONS: Dict[str, CampusLocation] = {
    "MAIN_GATE": CampusLocation(
        node_id="MAIN_GATE",
        name="Campus Main Entrance & Security Gate 1",
        aliases=["main gate", "entrance", "gate 1", "security gate", "campus gate", "front gate"],
        building="Main Gate Checkpost",
        floor="Ground Level",
        room="Security Post 1",
        category="GATEWAY",
        coordinates=(50, 10),
        description="Primary vehicular and pedestrian entrance with RFID access control and visitor verification.",
        operating_hours="24/7 Accessible",
        nearest_landmark="Transit Bay & Bus Terminal",
    ),
    "BUS_TERMINAL": CampusLocation(
        node_id="BUS_TERMINAL",
        name="College Transit Bay & Bus Terminal",
        aliases=["bus terminal", "bus stop", "transit bay", "bus station", "transport bay", "bus depot", "route 14"],
        building="Transit Plaza",
        floor="Ground Level",
        room="Bay 1-18",
        category="TRANSPORT",
        coordinates=(35, 15),
        description="Departure and arrival terminal for all 18 institutional bus routes and shuttle vans.",
        operating_hours="6:30 AM - 7:30 PM",
        nearest_landmark="Main Entrance Gate 1 (80m west)",
    ),
    "ATM_KIOSK": CampusLocation(
        node_id="ATM_KIOSK",
        name="SBI & HDFC 24/7 ATM & Banking Kiosk",
        aliases=["atm", "bank", "sbi atm", "hdfc atm", "cash machine", "banking kiosk"],
        building="Main Gate Plaza",
        floor="Ground Level",
        room="Kiosk 1 & 2",
        category="AMENITY",
        coordinates=(55, 12),
        description="Dual ATM facility providing cash withdrawal, passbook printing, and instant deposit.",
        operating_hours="24/7 Accessible",
        nearest_landmark="Beside Main Gate 1",
    ),
    "ADMIN_BLOCK": CampusLocation(
        node_id="ADMIN_BLOCK",
        name="Central Administrative Complex (Dr. Sarvepalli Radhakrishnan Bhavan)",
        aliases=["admin block", "administrative block", "bhavan", "main office", "admin"],
        building="Administrative Block",
        floor="Ground Floor Foyer",
        room="Central Foyer",
        category="ADMINISTRATIVE",
        coordinates=(50, 24),
        description="Central hub housing the Director's Office, Registrar, Bursar Accounts, and Exam Cell.",
        operating_hours="9:00 AM - 5:30 PM",
        nearest_landmark="Central Quadrangle (South Entrance)",
    ),
    "ACCOUNTS_BURSAR": CampusLocation(
        node_id="ACCOUNTS_BURSAR",
        name="Bursar & Finance Accounts Division (Fee Payment Desk)",
        aliases=["accounts", "accounts office", "fee counter", "bursar", "fee payment", "finance office", "tuition desk", "challan"],
        building="Administrative Block",
        floor="Ground Floor",
        room="Counters 3 to 6 (Room AD-004)",
        category="FEE_ACCOUNTS",
        coordinates=(52, 25),
        description="Official student counter for semester tuition fee payments, challans, receipt issuance, and scholarship endorsements.",
        operating_hours="9:30 AM - 4:30 PM (Mon-Sat)",
        nearest_landmark="Administrative Block Ground Floor, directly right of Main Reception",
    ),
    "DIRECTOR_OFFICE": CampusLocation(
        node_id="DIRECTOR_OFFICE",
        name="Director & Board of Governors Executive Suite",
        aliases=["director", "director office", "principal office", "principal", "executive suite"],
        building="Administrative Block",
        floor="2nd Floor",
        room="Room AD-201",
        category="ADMINISTRATIVE",
        coordinates=(48, 22),
        description="Office of the Institute Director (Dr. S. K. Raman). Prior appointment required for student meetings.",
        operating_hours="10:00 AM - 5:00 PM (Appointments 3-4 PM)",
        nearest_landmark="Take Admin Block Elevator to 2nd Floor, turn left",
    ),
    "REGISTRAR_OFFICE": CampusLocation(
        node_id="REGISTRAR_OFFICE",
        name="Office of the Registrar & Academic Affairs",
        aliases=["registrar", "registrar office", "academic affairs", "bonafide certificate", "transcripts"],
        building="Administrative Block",
        floor="1st Floor",
        room="Room AD-105",
        category="ADMINISTRATIVE",
        coordinates=(50, 26),
        description="Handles bonafide certificates, official mark transcripts, degree verification, and government compliance.",
        operating_hours="9:30 AM - 5:00 PM",
        nearest_landmark="Admin Block 1st Floor, opposite COE Exam Cell",
    ),
    "EXAM_CELL": CampusLocation(
        node_id="EXAM_CELL",
        name="Controller of Examinations (COE) Cell",
        aliases=["exam cell", "coe", "examination office", "hall ticket", "exam counter", "revaluation"],
        building="Administrative Block",
        floor="1st Floor",
        room="Room AD-112",
        category="ACADEMIC",
        coordinates=(46, 24),
        description="Conducts semester end exams, issues hall tickets, manages IA grade books, and processes revaluation requests.",
        operating_hours="9:30 AM - 5:00 PM",
        nearest_landmark="Admin Block 1st Floor West Wing",
    ),
    "TRANSPORT_DESK": CampusLocation(
        node_id="TRANSPORT_DESK",
        name="Office of Transportation & Transit Fleet Helpdesk",
        aliases=["transport office", "transport desk", "bus pass", "bus desk", "transit office"],
        building="Administrative Block",
        floor="Ground Floor",
        room="Bay 2 Transport Counter",
        category="TRANSPORT",
        coordinates=(54, 26),
        description="Handles semester bus pass passes, route reallocations, and transit fleet grievances.",
        operating_hours="9:00 AM - 4:30 PM",
        nearest_landmark="Adjacent to Accounts Division Counter 6",
    ),
    "HEALTH_CENTER": CampusLocation(
        node_id="HEALTH_CENTER",
        name="Campus Health Center & 24/7 Medical Dispensary",
        aliases=["health center", "medical", "clinic", "dispensary", "doctor", "ambulance", "first aid", "hospital"],
        building="Health & Wellness Pavilion",
        floor="Ground Floor",
        room="Rooms H-01 to H-04",
        category="HEALTH",
        coordinates=(30, 30),
        description="Resident medical officer, first-aid trauma unit, emergency beds, and 24/7 campus ambulance dispatch.",
        operating_hours="24/7 Medical Care",
        nearest_landmark="110m west of Administrative Complex across Rose Garden",
    ),
    "CENTRAL_LIBRARY": CampusLocation(
        node_id="CENTRAL_LIBRARY",
        name="Dr. A. P. J. Abdul Kalam Central Library",
        aliases=["library", "central library", "books", "reading room", "digital library", "ieee"],
        building="Central Library Building",
        floor="Ground to 3rd Floor",
        room="Stack Sections & Digital Stack (2nd Floor)",
        category="LIBRARY",
        coordinates=(50, 52),
        description="Modern 3-tier library with 45,000+ volumes, IEEE/ACM digital repository, and 24/7 quiet air-conditioned reading lounges.",
        operating_hours="7:30 AM - 11:00 PM",
        nearest_landmark="Central Quadrangle (facing Academic Block A)",
    ),
    "COMPUTING_BLOCK_A": CampusLocation(
        node_id="COMPUTING_BLOCK_A",
        name="Computing & AI Academic Block A (Alan Turing Block)",
        aliases=["block a", "computing block", "cse block", "turing block", "cs department"],
        building="Computing Block A",
        floor="Ground to 4th Floor",
        room="Main Entrance Portico",
        category="ACADEMIC",
        coordinates=(38, 42),
        description="Houses the Department of Computer Science & Engineering, AI & Data Science labs, and faculty suites.",
        operating_hours="7:30 AM - 9:00 PM",
        nearest_landmark="110m north-west of Central Library across Academic Walkway",
    ),
    "COMPUTING_LAB_3": CampusLocation(
        node_id="COMPUTING_LAB_3",
        name="High-Performance AI & GPU Computing Lab 3",
        aliases=["lab 3", "computing lab 3", "ai lab", "gpu lab", "nvidia lab", "hpc lab", "cs lab 3", "room a-104"],
        building="Computing Block A",
        floor="1st Floor",
        room="Room A-104",
        category="LABORATORY",
        coordinates=(38, 42),
        description="Equipped with 40x NVIDIA RTX A6000 workstations, high-speed InfiniBand network, and PyTorch/TensorFlow environments.",
        operating_hours="8:00 AM - 8:00 PM",
        nearest_landmark="Computing Block A, 1st Floor Wing B, opposite Server Room & HOD CSE Suite",
    ),
    "COMPUTING_LAB_1": CampusLocation(
        node_id="COMPUTING_LAB_1",
        name="Core Programming & Data Structures Lab 1",
        aliases=["lab 1", "computing lab 1", "programming lab", "ds lab", "cs lab 1", "room a-002"],
        building="Computing Block A",
        floor="Ground Floor",
        room="Room A-002",
        category="LABORATORY",
        coordinates=(36, 40),
        description="60 modern Linux workstations for C++, Java, Python programming and algorithms coursework.",
        operating_hours="8:00 AM - 6:00 PM",
        nearest_landmark="Computing Block A Ground Floor, immediately left of entrance foyer",
    ),
    "COMPUTING_LAB_2": CampusLocation(
        node_id="COMPUTING_LAB_2",
        name="Database Systems & Cloud Engineering Lab 2",
        aliases=["lab 2", "computing lab 2", "database lab", "dbms lab", "cloud lab", "room a-005"],
        building="Computing Block A",
        floor="Ground Floor",
        room="Room A-005",
        category="LABORATORY",
        coordinates=(40, 40),
        description="Workstations configured with PostgreSQL 18, Docker, Kubernetes, and AWS CLI tools.",
        operating_hours="8:00 AM - 6:00 PM",
        nearest_landmark="Computing Block A Ground Floor East Wing",
    ),
    "COMPUTING_LAB_4": CampusLocation(
        node_id="COMPUTING_LAB_4",
        name="Embedded Systems & Edge AI Lab 4",
        aliases=["lab 4", "computing lab 4", "iot lab", "embedded lab", "edge lab", "room a-203"],
        building="Computing Block A",
        floor="2nd Floor",
        room="Room A-203",
        category="LABORATORY",
        coordinates=(38, 44),
        description="Hardware lab with Raspberry Pi 5, Jetson Orin Nano, FPGA kits, and logic analyzers.",
        operating_hours="8:30 AM - 6:30 PM",
        nearest_landmark="Computing Block A 2nd Floor, take North elevator",
    ),
    "HOD_CSE": CampusLocation(
        node_id="HOD_CSE",
        name="Head of Department (CSE) - Prof. Sunita Reddy Suite",
        aliases=["hod cse", "hod cs", "cse hod", "hod office", "sunita reddy"],
        building="Computing Block A",
        floor="1st Floor",
        room="Room A-110",
        category="ADMINISTRATIVE",
        coordinates=(42, 42),
        description="Office of the Computer Science & Engineering Department Head. Student grievance hours: 2:30 PM - 4:00 PM.",
        operating_hours="9:00 AM - 5:30 PM",
        nearest_landmark="Computing Block A 1st Floor, next to Faculty Lounge",
    ),
    "LH_101": CampusLocation(
        node_id="LH_101",
        name="Smart Lecture Hall LH-101",
        aliases=["lh 101", "lh101", "lecture hall 101", "room 101", "classroom 101"],
        building="Computing Block A",
        floor="1st Floor",
        room="Room A-101",
        category="CLASSROOM",
        coordinates=(34, 42),
        description="120-seat tiered acoustic lecture theater with 4K laser projection and digital audio recording.",
        operating_hours="8:00 AM - 6:00 PM",
        nearest_landmark="Computing Block A 1st Floor West Wing",
    ),
    "SEMINAR_HALL_1": CampusLocation(
        node_id="SEMINAR_HALL_1",
        name="Turing International Seminar Hall",
        aliases=["seminar hall", "seminar hall 1", "turing hall", "conference hall"],
        building="Computing Block A",
        floor="3rd Floor",
        room="Room A-301",
        category="ACADEMIC",
        coordinates=(38, 46),
        description="Air-conditioned conference auditorium for research colloquiums, guest lectures, and paper presentations.",
        operating_hours="8:30 AM - 7:00 PM",
        nearest_landmark="Computing Block A 3rd Floor Central Atrium",
    ),
    "ECE_BLOCK": CampusLocation(
        node_id="ECE_BLOCK",
        name="Electronics & Communication Academic Block B (J. C. Bose Block)",
        aliases=["block b", "ece block", "electronics block", "bose block"],
        building="Block B",
        floor="Ground to 4th Floor",
        room="Main Portico",
        category="ACADEMIC",
        coordinates=(62, 42),
        description="Houses the Department of ECE, VLSI Design Lab, DSP Lab, and Microwave Antenna Chambers.",
        operating_hours="7:30 AM - 9:00 PM",
        nearest_landmark="125m east of Central Library across Quadrangle Lawn",
    ),
    "CAFETERIA": CampusLocation(
        node_id="CAFETERIA",
        name="Campus Central Cafeteria & Student Food Court",
        aliases=["cafeteria", "canteen", "food court", "cafe", "bistro", "coffee", "snacks"],
        building="Student Activity Center",
        floor="Ground Floor",
        room="Food Court Pavilion",
        category="AMENITY",
        coordinates=(68, 60),
        description="Multi-cuisine dining area offering healthy breakfast, lunch meals, barista coffee, and snacks.",
        operating_hours="7:30 AM - 9:30 PM",
        nearest_landmark="Between Academic Quadrangle and Residential Hostels",
    ),
    "AUDITORIUM": CampusLocation(
        node_id="AUDITORIUM",
        name="Apex Convocation & Cultural Auditorium",
        aliases=["auditorium", "audi", "convocation hall", "cultural hall", "main stage"],
        building="Auditorium Complex",
        floor="Ground Level",
        room="Main Hall",
        category="AMENITY",
        coordinates=(25, 65),
        description="1,500-seat grand auditorium for annual fests, convocation ceremonies, and national conferences.",
        operating_hours="Event Dependent",
        nearest_landmark="Western campus grounds, opposite Sports Pavilion",
    ),
    "SPORTS_COMPLEX": CampusLocation(
        node_id="SPORTS_COMPLEX",
        name="Indoor Sports Arena & Fitness Pavilion",
        aliases=["sports complex", "gym", "badminton", "sports arena", "fitness center", "basketball", "ground"],
        building="Sports Pavilion",
        floor="Ground Floor",
        room="Indoor Court 1-3 & Gym",
        category="SPORTS",
        coordinates=(20, 80),
        description="Features 4 wooden badminton courts, table tennis, modern gymnasium, and Olympic running track.",
        operating_hours="6:00 AM - 9:00 PM",
        nearest_landmark="Adjacent to College Cricket Ground",
    ),
    "HOSTEL_A": CampusLocation(
        node_id="HOSTEL_A",
        name="Hostel Block A (Senior Men's Residence - Aryabhata Bhavan)",
        aliases=["hostel a", "boys hostel a", "aryabhata hostel", "senior hostel"],
        building="Hostel Block A",
        floor="Floors 1 to 4",
        room="Rooms 101 to 420",
        category="RESIDENTIAL",
        coordinates=(80, 75),
        description="Residential quarters for 3rd and 4th-year male undergraduate and postgraduate engineering scholars.",
        operating_hours="Curfew: 9:30 PM (Weekdays), 10:00 PM (Weekends)",
        nearest_landmark="East Residential Quadrangle, next to Central Dining Mess",
    ),
    "HOSTEL_B": CampusLocation(
        node_id="HOSTEL_B",
        name="Hostel Block B (Junior Men's Residence - Ramanujan Bhavan)",
        aliases=["hostel b", "boys hostel b", "ramanujan hostel", "junior hostel", "hostel"],
        building="Hostel Block B",
        floor="Floors 1 to 4",
        room="Rooms 101 to 415",
        category="RESIDENTIAL",
        coordinates=(85, 80),
        description="Residential quarters for 1st and 2nd-year male engineering students with dedicated study halls.",
        operating_hours="Curfew: 9:30 PM (Weekdays), 10:00 PM (Weekends)",
        nearest_landmark="70m east of Central Dining Mess",
    ),
    "HOSTEL_C": CampusLocation(
        node_id="HOSTEL_C",
        name="Hostel Block C (Women's Residence - Gargi Bhavan)",
        aliases=["hostel c", "girls hostel", "womens hostel", "gargi hostel"],
        building="Hostel Block C",
        floor="Floors 1 to 4",
        room="Rooms 101 to 430",
        category="RESIDENTIAL",
        coordinates=(75, 85),
        description="Gated residential complex for female undergraduate scholars with 24/7 biometric security.",
        operating_hours="Curfew: 9:30 PM (Weekdays), 10:00 PM (Weekends)",
        nearest_landmark="Northern sector of residential zone, beside Chief Warden Office",
    ),
    "HOSTEL_MESS": CampusLocation(
        node_id="HOSTEL_MESS",
        name="Central Dining Hall & Student Mess (Annapurna Bhawan)",
        aliases=["mess", "hostel mess", "dining hall", "food hall", "annapurna"],
        building="Residential Dining Complex",
        floor="Ground & 1st Floor",
        room="Dining Halls 1 & 2",
        category="RESIDENTIAL",
        coordinates=(82, 70),
        description="Serves breakfast (7:30-9:00 AM), lunch (12:30-2:00 PM), evening snacks (5:00-6:00 PM), and dinner (7:30-9:30 PM).",
        operating_hours="Meal Timings Daily",
        nearest_landmark="Central hub connecting Hostel Blocks A, B, and C",
    ),
    "CHIEF_WARDEN": CampusLocation(
        node_id="CHIEF_WARDEN",
        name="Chief Warden Office & Residential Grievance Desk",
        aliases=["warden", "chief warden", "warden office", "hostel office"],
        building="Residential Central Office",
        floor="Ground Floor",
        room="Room W-01",
        category="RESIDENTIAL",
        coordinates=(80, 80),
        description="Handles hostel room allocations, late pass permissions, night leaves, and maintenance complaints.",
        operating_hours="9:00 AM - 7:00 PM (Emergency 24/7)",
        nearest_landmark="Directly between Hostel Block B and Hostel Block C",
    ),
}

# Campus Pathway Graph (Undirected weighted graph: distance in meters)
# Walking speed is calibrated at 1.2 meters per second (~72 meters per minute).
CAMPUS_GRAPH_EDGES: List[Tuple[str, str, int, str]] = [
    # (NodeA, NodeB, DistanceMeters, PathwayDescription)
    ("MAIN_GATE", "ATM_KIOSK", 25, "Walk 25m along Main Gate Portico right-hand pavement."),
    ("MAIN_GATE", "BUS_TERMINAL", 80, "Head West 80m along the tree-lined pedestrian transit promenade."),
    ("MAIN_GATE", "ADMIN_BLOCK", 95, "Walk straight North 95m along Central Palm Avenue toward the Administrative Complex."),
    ("ATM_KIOSK", "ADMIN_BLOCK", 90, "Head North 90m through the front garden walkway."),
    ("BUS_TERMINAL", "HEALTH_CENTER", 110, "Head North 110m along West Avenue toward Health & Wellness Pavilion."),
    ("ADMIN_BLOCK", "ACCOUNTS_BURSAR", 15, "Enter Admin Block Ground Floor; turn right 15m to Counters 3-6."),
    ("ADMIN_BLOCK", "DIRECTOR_OFFICE", 30, "Take Admin Block central staircase or elevator to 2nd Floor, turn left 30m."),
    ("ADMIN_BLOCK", "REGISTRAR_OFFICE", 25, "Take Admin Block staircase to 1st Floor, walk 25m along central gallery."),
    ("ADMIN_BLOCK", "EXAM_CELL", 25, "Take Admin Block staircase to 1st Floor West Wing 25m."),
    ("ADMIN_BLOCK", "TRANSPORT_DESK", 20, "Admin Block Ground Floor, walk 20m past Reception to Bay 2 Counter."),
    ("ADMIN_BLOCK", "HEALTH_CENTER", 110, "Walk West 110m across the Rose Garden path toward Health Center."),
    ("ADMIN_BLOCK", "CENTRAL_LIBRARY", 140, "Walk North 140m along the paved Central Boulevard through the Quadrangle."),
    ("CENTRAL_LIBRARY", "COMPUTING_BLOCK_A", 110, "Head North-West 110m along Academic Walkway toward Alan Turing Block A."),
    ("CENTRAL_LIBRARY", "ECE_BLOCK", 125, "Head East 125m across the Quadrangle lawn toward J.C. Bose Block B."),
    ("CENTRAL_LIBRARY", "CAFETERIA", 90, "Head North-East 90m along student corridor toward Cafeteria food court."),
    ("COMPUTING_BLOCK_A", "COMPUTING_LAB_3", 35, "Enter Block A, take central stairs/elevator to 1st Floor, turn right 35m into Corridor A-1 (Room A-104)."),
    ("COMPUTING_BLOCK_A", "COMPUTING_LAB_1", 20, "Enter Block A Ground Floor, turn left 20m into Programming Lab (Room A-002)."),
    ("COMPUTING_BLOCK_A", "COMPUTING_LAB_2", 20, "Enter Block A Ground Floor, turn right 20m into Database Lab (Room A-005)."),
    ("COMPUTING_BLOCK_A", "COMPUTING_LAB_4", 45, "Enter Block A, take elevator to 2nd Floor, walk 45m along Corridor A-2 to Room A-203."),
    ("COMPUTING_BLOCK_A", "HOD_CSE", 35, "Enter Block A, proceed to 1st Floor, walk 35m past Lab 3 to HOD Suite (Room A-110)."),
    ("COMPUTING_BLOCK_A", "LH_101", 25, "Enter Block A, take stairs to 1st Floor West Wing 25m to Lecture Hall LH-101."),
    ("COMPUTING_BLOCK_A", "SEMINAR_HALL_1", 55, "Enter Block A, take elevator to 3rd Floor Central Atrium 55m."),
    ("COMPUTING_BLOCK_A", "AUDITORIUM", 130, "Exit Block A West Porch, walk 130m South-West along Gulmohar Lane to Auditorium."),
    ("COMPUTING_BLOCK_A", "SPORTS_COMPLEX", 180, "Head West 180m past the cultural auditorium toward the Indoor Sports Pavilion."),
    ("AUDITORIUM", "SPORTS_COMPLEX", 90, "Head North 90m along the athletic pavilion pathway."),
    ("CAFETERIA", "HOSTEL_MESS", 120, "Head East 120m along Shaded Canopy Walkway into the Residential Zone."),
    ("HOSTEL_MESS", "HOSTEL_A", 60, "Exit Mess, walk 60m East along Brick Paved Walkway to Hostel Block A entrance."),
    ("HOSTEL_MESS", "HOSTEL_B", 70, "Exit Mess, head North-East 70m past Green Lawns to Hostel Block B entrance."),
    ("HOSTEL_MESS", "HOSTEL_C", 85, "Exit Mess, head North 85m past security checkpost to Hostel Block C entrance."),
    ("HOSTEL_B", "CHIEF_WARDEN", 40, "Walk 40m South-West from Hostel Block B foyer to Chief Warden Office (Room W-01)."),
    ("HOSTEL_A", "CHIEF_WARDEN", 50, "Walk 50m North-West from Hostel Block A foyer to Chief Warden Office."),
    ("HOSTEL_C", "CHIEF_WARDEN", 45, "Walk 45m South from Hostel Block C gate to Chief Warden Office."),
]


class CampusWayfinder:
    @staticmethod
    def find_location(query: str) -> Optional[CampusLocation]:
        """Resolves natural language query or place name to exact campus location."""
        q = query.lower().strip()
        # Direct key match
        for key, loc in CAMPUS_LOCATIONS.items():
            if q == key.lower() or q == loc.name.lower():
                return loc

        # Alias match
        for key, loc in CAMPUS_LOCATIONS.items():
            for alias in loc.aliases:
                if alias in q or q in alias:
                    return loc

        # Keyword match
        keywords = {
            "fee": "ACCOUNTS_BURSAR",
            "tuition": "ACCOUNTS_BURSAR",
            "accounts": "ACCOUNTS_BURSAR",
            "bursar": "ACCOUNTS_BURSAR",
            "lab 3": "COMPUTING_LAB_3",
            "ai lab": "COMPUTING_LAB_3",
            "gpu": "COMPUTING_LAB_3",
            "lab 1": "COMPUTING_LAB_1",
            "lab 2": "COMPUTING_LAB_2",
            "lab 4": "COMPUTING_LAB_4",
            "library": "CENTRAL_LIBRARY",
            "books": "CENTRAL_LIBRARY",
            "director": "DIRECTOR_OFFICE",
            "principal": "DIRECTOR_OFFICE",
            "registrar": "REGISTRAR_OFFICE",
            "exam": "EXAM_CELL",
            "hall ticket": "EXAM_CELL",
            "curfew": "CHIEF_WARDEN",
            "warden": "CHIEF_WARDEN",
            "hostel b": "HOSTEL_B",
            "hostel a": "HOSTEL_A",
            "hostel c": "HOSTEL_C",
            "mess": "HOSTEL_MESS",
            "food": "CAFETERIA",
            "canteen": "CAFETERIA",
            "bus": "BUS_TERMINAL",
            "transit": "BUS_TERMINAL",
            "atm": "ATM_KIOSK",
            "doctor": "HEALTH_CENTER",
            "medical": "HEALTH_CENTER",
            "clinic": "HEALTH_CENTER",
            "sports": "SPORTS_COMPLEX",
            "gym": "SPORTS_COMPLEX",
            "auditorium": "AUDITORIUM",
            "cse": "COMPUTING_BLOCK_A",
            "ece": "ECE_BLOCK",
        }
        for kw, node_id in keywords.items():
            if kw in q:
                return CAMPUS_LOCATIONS.get(node_id)

        return None

    @staticmethod
    def detect_origin_and_destination(query: str, default_origin: str = "HOSTEL_B") -> Tuple[Optional[CampusLocation], Optional[CampusLocation]]:
        """Parses origin and destination from expressions like 'from [origin] to [destination]' or 'how to go to [dest]'."""
        q = query.lower()

        # Check for explicit 'from X to Y' pattern
        if "from" in q and "to" in q:
            parts_after_from = q.split("from", 1)[1]
            if "to" in parts_after_from:
                from_part, to_part = parts_after_from.split("to", 1)
                origin = CampusWayfinder.find_location(from_part)
                dest = CampusWayfinder.find_location(to_part)
                if origin and dest:
                    return origin, dest

        # Check for destination only
        dest = CampusWayfinder.find_location(query)
        origin = CAMPUS_LOCATIONS.get(default_origin) or CAMPUS_LOCATIONS.get("MAIN_GATE")
        return origin, dest

    @staticmethod
    def calculate_route(
        origin_node_id: str,
        dest_node_id: str,
    ) -> Dict[str, Any]:
        """Calculates the exact shortest walking path using Dijkstra's algorithm.

        Returns cumulative distance in meters, estimated walking time in minutes,
        and turn-by-turn walking steps.
        """
        origin = CAMPUS_LOCATIONS.get(origin_node_id)
        dest = CAMPUS_LOCATIONS.get(dest_node_id)

        if not origin or not dest:
            raise ValueError(f"Invalid origin ({origin_node_id}) or destination ({dest_node_id})")

        if origin_node_id == dest_node_id:
            return {
                "origin": origin.to_dict(),
                "destination": dest.to_dict(),
                "total_distance_m": 0,
                "walking_time_min": 0.0,
                "turn_by_turn_steps": [f"You are already at {dest.name} ({dest.building}, {dest.floor})."],
                "path_nodes": [dest.to_dict()],
            }

        # Build adjacency list
        adj: Dict[str, List[Tuple[str, int, str]]] = {node: [] for node in CAMPUS_LOCATIONS}
        for u, v, dist, desc in CAMPUS_GRAPH_EDGES:
            if u in adj and v in adj:
                adj[u].append((v, dist, desc))
                adj[v].append((u, dist, desc))

        # Dijkstra algorithm
        import heapq
        distances = {node: float("inf") for node in CAMPUS_LOCATIONS}
        distances[origin_node_id] = 0
        previous_nodes: Dict[str, Optional[Tuple[str, int, str]]] = {node: None for node in CAMPUS_LOCATIONS}
        pq = [(0, origin_node_id)]

        while pq:
            current_dist, current_node = heapq.heappop(pq)
            if current_dist > distances[current_node]:
                continue
            if current_node == dest_node_id:
                break

            for neighbor, weight, step_desc in adj[current_node]:
                distance = current_dist + weight
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous_nodes[neighbor] = (current_node, weight, step_desc)
                    heapq.heappush(pq, (distance, neighbor))

        # Reconstruct path
        path_nodes: List[CampusLocation] = []
        steps: List[str] = []
        curr = dest_node_id

        temp_steps = []
        while curr:
            loc = CAMPUS_LOCATIONS[curr]
            path_nodes.insert(0, loc)
            prev_info = previous_nodes[curr]
            if prev_info:
                prev_node, weight, step_desc = prev_info
                temp_steps.insert(0, f"{step_desc} ({weight}m)")
                curr = prev_node
            else:
                break

        total_distance = int(distances[dest_node_id])
        # Average walking speed 1.2 m/s -> 72 m/min
        walking_time = round(total_distance / 72.0, 1)

        # Build turn-by-turn formatted narrative
        numbered_steps = []
        for idx, s in enumerate(temp_steps, start=1):
            numbered_steps.append(f"Step {idx}: {s}")

        # Add arrival step
        numbered_steps.append(
            f"Step {len(numbered_steps) + 1}: Arrive at {dest.name}. Located in {dest.building}, {dest.floor}, {dest.room}. Landmark: {dest.nearest_landmark}."
        )

        return {
            "origin": origin.to_dict(),
            "destination": dest.to_dict(),
            "total_distance_m": total_distance,
            "walking_time_min": walking_time,
            "turn_by_turn_steps": numbered_steps,
            "path_nodes": [p.to_dict() for p in path_nodes],
        }
