#!/usr/bin/env python3
"""Generate the raw CSVs for one brief into data/<brief>/.

    python3 generate_data.py bigbasket | swiggy | myntra | razorpay

Deterministic (seeded), Python standard library only, no network. Each brief's data is shaped
for its own story — the raw files are the case, and the tickets are about what is in them.
Reading this file to find out what was planted is a way of skipping the project; the
warehouse is the place to look.
"""
import csv
import os
import random
import sys
from datetime import date, datetime, timedelta

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

CITIES = ["Bengaluru", "Mumbai", "Delhi", "Hyderabad", "Chennai", "Pune", "Kolkata",
          "Ahmedabad", "Jaipur", "Lucknow", "Kochi", "Chandigarh"]
FIRST = ["Aarav", "Ananya", "Arjun", "Diya", "Ishaan", "Kavya", "Rohan", "Sneha", "Vikram",
         "Priya", "Rahul", "Meera", "Karan", "Neha", "Aditya", "Pooja", "Siddharth", "Riya",
         "Nikhil", "Tanvi", "Manish", "Shreya", "Varun", "Isha"]
LAST = ["Sharma", "Verma", "Iyer", "Reddy", "Nair", "Patel", "Singh", "Gupta", "Kulkarni",
        "Das", "Mehta", "Rao", "Joshi", "Bose", "Chopra", "Pillai", "Menon", "Saxena"]


def out_dir(brief):
    d = os.path.join(OUT, brief)
    os.makedirs(d, exist_ok=True)
    return d


def write_csv(path, header, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"  wrote {os.path.relpath(path)}  ({len(rows):,} rows)")


def ts(d, rng, start_h=7, end_h=23):
    h = rng.randint(start_h, end_h - 1)
    return datetime(d.year, d.month, d.day, h, rng.randint(0, 59), rng.randint(0, 59))


# ── BigBasket: grocery order lines ──────────────────────────────────────────────────────
BB_CATALOGUE = {
    "Staples": ["Aashirvaad Atta 5kg", "India Gate Basmati 5kg", "Tata Salt 1kg", "Fortune Sunflower Oil 1L",
                "Toor Dal 1kg", "Moong Dal 1kg", "Sugar 1kg", "Poha 500g", "Rava 1kg", "Besan 1kg"],
    "Dairy": ["Amul Ghee 1L", "Nandini Milk 1L", "Amul Butter 500g", "Curd 400g", "Paneer 200g",
              "Cheese Slices 200g", "Amul Milk 500ml"],
    "Fruits & Veg": ["Onion 1kg", "Tomato 1kg", "Potato 1kg", "Banana 1 dozen", "Apple 1kg", "Coriander 100g",
                     "Green Chilli 100g", "Lemon 250g", "Carrot 500g", "Spinach 250g"],
    "Snacks": ["Lay's Magic Masala 52g", "Haldiram Bhujia 400g", "Parle-G 800g", "Britannia Good Day 600g",
               "Kurkure Masala Munch 90g", "Bingo Mad Angles 130g"],
    "Beverages": ["Tata Tea Gold 500g", "Nescafe Classic 100g", "Coca-Cola 2L", "Real Mixed Fruit 1L",
                  "Bru Instant 200g", "Paper Boat Aamras 200ml"],
    "Household": ["Surf Excel Matic 2kg", "Vim Bar 3x200g", "Harpic 1L", "Lizol Floor Cleaner 975ml",
                  "Good Knight Refill", "Scotch-Brite Scrub Pad"],
    "Personal Care": ["Dove Soap 3x100g", "Colgate MaxFresh 300g", "Head & Shoulders 340ml", "Nivea Body Lotion 400ml",
                      "Gillette Mach3 Cartridge", "Dettol Handwash 750ml"],
    "Baby Care": ["Pampers Pants L 42", "Cerelac Wheat 300g", "Johnson's Baby Powder 200g", "Himalaya Baby Wash 200ml"],
    "Bakery": ["Wheat Bread 400g", "Multigrain Bread 400g", "Eggs 12 pack", "Croissant 2 pack"],
    "Frozen": ["McCain French Fries 750g", "Sumeru Green Peas 500g", "Amul Ice Cream 1L", "ITC Chicken Nuggets 500g"],
}
# What gets bought together. The category team's whole question, so it is genuinely in the data.
BB_AFFINITY = {"Aashirvaad Atta 5kg": ("Amul Ghee 1L", 0.55), "Tata Tea Gold 500g": ("Sugar 1kg", 0.45),
               "Wheat Bread 400g": ("Amul Butter 500g", 0.5), "Eggs 12 pack": ("Wheat Bread 400g", 0.4),
               "Pampers Pants L 42": ("Johnson's Baby Powder 200g", 0.5), "Toor Dal 1kg": ("Tata Salt 1kg", 0.3)}


def gen_bigbasket(rng):
    d = out_dir("bigbasket")
    skus, price, cat_of = {}, {}, {}
    n = 1000
    for cat, names in BB_CATALOGUE.items():
        for name in names:
            n += 1
            skus[name] = f"SKU{n}"
            cat_of[name] = cat
            price[name] = rng.choice([1900, 2500, 3500, 4900, 6500, 8900, 12900, 19900, 29900, 45000, 62000])
    names = list(skus)
    customers = []
    for i in range(6000):
        customers.append((f"C{100000 + i}", f"{rng.choice(FIRST)} {rng.choice(LAST)}", rng.choice(CITIES)))
    rows = []
    day0 = date(2025, 3, 1)
    order_no = 500000
    for _ in range(30000):
        order_no += 1
        oid = f"BB{order_no}"
        od = day0 + timedelta(days=rng.randint(0, 183))
        t = ts(od, rng)
        cust = rng.choice(customers)
        cid, cname, city = cust
        if rng.random() < 0.03:  # guest checkout: no customer id, name typed at checkout
            cid, cname = "", f"{rng.choice(FIRST)} {rng.choice(LAST)}"
        basket = set()
        for _ in range(max(1, int(rng.gauss(4, 2)))):
            item = rng.choice(names)
            basket.add(item)
            if item in BB_AFFINITY and rng.random() < BB_AFFINITY[item][1]:
                basket.add(BB_AFFINITY[item][0])
        basket = sorted(basket)
        # Some baskets carry the same product on two lines (added twice at checkout) — a real
        # export does this, and it is why the line grain is not (order, product).
        if len(basket) > 1 and rng.random() < 0.02:
            basket.append(basket[0])
        fee = 0 if len(basket) >= 4 else rng.choice([2500, 3500, 4900])
        for line_no, item in enumerate(basket, start=1):
            pname = item
            if rng.random() < 0.08:  # the catalogue export is not consistent about casing
                pname = item.upper() if rng.random() < 0.5 else item.lower()
            rows.append([oid, line_no, t.isoformat(sep=" "), cid, cname, city, skus[item], pname, cat_of[item],
                         rng.randint(1, 6), price[item], fee])
    write_csv(os.path.join(d, "order_lines.csv"),
              ["order_id", "line_no", "order_ts", "customer_id", "customer_name", "city", "sku", "product_name",
               "category", "qty", "unit_price_paise", "delivery_fee_paise"], rows)


# ── Swiggy: one file per day, a month of them ───────────────────────────────────────────
def gen_swiggy(rng):
    d = out_dir("swiggy")
    restaurants = [f"R{2000 + i}" for i in range(600)]
    rest_city = {r: rng.choice(CITIES) for r in restaurants}
    order_no = 8_000_000
    month = [date(2025, 8, 1) + timedelta(days=i) for i in range(31)]
    header = ["order_id", "customer_id", "restaurant_id", "city", "order_ts", "order_date", "status",
              "amount_paise", "delivery_fee_paise"]
    spill = []  # orders placed near midnight land in the next day's file — as they do upstream
    for day in month:
        base = 3600 + (900 if day.weekday() >= 5 else 0)
        rows = list(spill)
        spill = []
        for _ in range(int(rng.gauss(base, 150))):
            order_no += 1
            r = rng.choice(restaurants)
            t = ts(day, rng, 8, 24)
            status = "delivered" if rng.random() < 0.94 else "cancelled"
            row = [f"SW{order_no}", f"U{rng.randint(10000, 99999)}", r, rest_city[r], t.isoformat(sep=" "),
                   day.isoformat(), status, rng.choice([14900, 19900, 24900, 32900, 41900, 55900, 78900]),
                   rng.choice([0, 1900, 2900, 3900])]
            if t.hour == 23 and t.minute >= 45 and rng.random() < 0.7:
                spill.append(row)
            else:
                rows.append(row)
        write_csv(os.path.join(d, f"orders_{day.isoformat()}.csv"), header, rows)


# ── Myntra: two seller snapshots and the orders in between ──────────────────────────────
MY_CATEGORIES = ["Ethnic Wear", "Fusion Wear", "Western Wear", "Footwear", "Accessories", "Kids", "Sportswear",
                 "Beauty", "Home"]
MY_STATE = {"Bengaluru": "Karnataka", "Mumbai": "Maharashtra", "Delhi": "Delhi", "Hyderabad": "Telangana",
            "Chennai": "Tamil Nadu", "Pune": "Maharashtra", "Kolkata": "West Bengal", "Ahmedabad": "Gujarat",
            "Jaipur": "Rajasthan", "Lucknow": "Uttar Pradesh", "Kochi": "Kerala", "Chandigarh": "Punjab",
            "Surat": "Gujarat", "Tirupur": "Tamil Nadu", "Ludhiana": "Punjab"}


def typo(name, rng):
    i = rng.randint(1, len(name) - 2)
    return name[:i] + name[i] + name[i:] if rng.random() < 0.5 else name[:i] + name[i + 1:]


def gen_myntra(rng):
    d = out_dir("myntra")
    header = ["seller_id", "seller_name", "category", "city", "state", "gstin", "contact_email", "snapshot_date"]
    words = ["Textiles", "Fashions", "Apparels", "Creations", "Collections", "Boutique", "Traders", "Exports",
             "Garments", "Designs", "Emporium", "Weaves"]
    june, sept = [], []
    seller_ids = []
    for i in range(2000):
        sid = f"S{40000 + i}"
        seller_ids.append(sid)
        city = rng.choice(list(MY_STATE))
        name = f"{rng.choice(LAST)} {rng.choice(words)}"
        row = [sid, name, rng.choice(MY_CATEGORIES), city, MY_STATE[city],
               f"{rng.randint(10, 36)}AAACS{rng.randint(1000, 9999)}A1Z{rng.randint(0, 9)}",
               f"{name.split()[0].lower()}{rng.randint(1, 99)}@example.com"]
        june.append(row + ["2025-06-01"])
        sept.append(list(row) + ["2025-09-01"])
    # What changed between June and September. Some of it is history, some of it is a fix.
    idx = list(range(2000))
    rng.shuffle(idx)
    cat_changed = idx[:60]
    for i in cat_changed:  # a real move — the seller now sells something else
        sept[i][2] = rng.choice([c for c in MY_CATEGORIES if c != sept[i][2]])
    for i in idx[60:85]:  # June had the name wrong; September is the correction
        june[i][1] = typo(june[i][1], rng)
    for i in idx[85:100]:  # moved warehouse city
        city = rng.choice(list(MY_STATE))
        sept[i][3], sept[i][4] = city, MY_STATE[city]
    for i in idx[100:140]:  # a new contact address
        sept[i][6] = f"ops.{sept[i][1].split()[0].lower()}@example.com"
    for i in idx[140:150]:  # June had the GSTIN wrong by a character
        june[i][5] = june[i][5][:-1] + "9"
    for i in range(2000, 2030):  # onboarded after June
        sid = f"S{40000 + i}"
        seller_ids.append(sid)
        city = rng.choice(list(MY_STATE))
        name = f"{rng.choice(LAST)} {rng.choice(words)}"
        sept.append([sid, name, rng.choice(MY_CATEGORIES), city, MY_STATE[city],
                     f"{rng.randint(10, 36)}AAACS{rng.randint(1000, 9999)}A1Z{rng.randint(0, 9)}",
                     f"{name.split()[0].lower()}{rng.randint(1, 99)}@example.com", "2025-09-01"])
    write_csv(os.path.join(d, "sellers_2025_06.csv"), header, june)
    write_csv(os.path.join(d, "sellers_2025_09.csv"), header, sept)

    rows = []
    day0 = date(2025, 1, 1)
    heavy = [seller_ids[i] for i in cat_changed[:10]]  # the movers ship plenty, so the effect is visible
    for n in range(100000):
        od = day0 + timedelta(days=rng.randint(0, 262))
        sid = rng.choice(heavy) if rng.random() < 0.08 else rng.choice(seller_ids)
        if sid >= "S42000" and od < date(2025, 9, 1):  # not onboarded yet
            sid = rng.choice(seller_ids[:2000])
        rows.append([f"MY{7000000 + n}", od.isoformat(), sid, f"U{rng.randint(100000, 999999)}",
                     f"SKU{rng.randint(10000, 99999)}", rng.choice([49900, 79900, 99900, 129900, 189900, 249900]),
                     "delivered" if rng.random() < 0.9 else "returned"])
    write_csv(os.path.join(d, "orders.csv"),
              ["order_id", "order_date", "seller_id", "customer_id", "sku", "amount_paise", "status"], rows)


# ── Razorpay: the ledger and the bank's settlement file for one day ─────────────────────
def rupees(paise):
    return f"{paise // 100}.{paise % 100:02d}"


def gen_razorpay(rng):
    d = out_dir("razorpay")
    day = date(2025, 9, 15)
    prev = day - timedelta(days=1)
    merchants = [f"M{rng.randint(10**7, 10**8 - 1)}" for _ in range(400)]
    methods = ["upi", "upi", "upi", "card", "netbanking", "wallet"]
    ledger, settle = [], []
    entry_no, utr_no, pay_no = 1_000_000, 5_000_000, 9_000_000

    def pay_id():
        nonlocal pay_no
        pay_no += 1
        return f"pay_{pay_no:012d}"

    def ledger_row(pid, m, kind, paise, t):
        nonlocal entry_no
        entry_no += 1
        ledger.append([f"led_{entry_no}", pid, m, kind, paise, "INR", t.isoformat(sep=" "), rng.choice(methods)])

    def settle_row(pid, m, gross, captured_on, remark=""):
        nonlocal utr_no
        utr_no += 1
        fee = round(gross * 0.02)
        tax = round(fee * 0.18)
        settle.append([f"UTR{utr_no}", pid, m, rupees(gross), rupees(fee), rupees(tax), rupees(gross - fee - tax),
                       captured_on.isoformat(), day.isoformat(), remark])

    amounts = [9900, 19900, 24900, 49900, 99900, 149990, 199900, 349900, 599900, 1249900]
    # The ordinary day: captured before the 18:00 cut-off, settled the same day.
    for _ in range(18000):
        pid, m, a = pay_id(), rng.choice(merchants), rng.choice(amounts) + rng.randint(0, 99)
        t = ts(day, rng, 0, 18)
        ledger_row(pid, m, "capture", a, t)
        r = rng.random()
        if r < 0.0015:  # the bank's file and ours disagree by a paisa
            settle_row(pid, m, a + rng.choice([-1, 1]), day)
        elif r < 0.0017:  # captured, never settled — this is the kind that is a loss
            pass
        elif r < 0.0019:  # settled twice by the bank, two UTRs
            settle_row(pid, m, a, day)
            settle_row(pid, m, a, day, "RESUBMIT")
        elif r < 0.004:  # refunded in full or part before the cut-off; the bank nets it
            ref = a if rng.random() < 0.5 else a // 2
            ledger_row(pid, m, "refund", ref, ts(day, rng, 12, 18))
            settle_row(pid, m, a - ref, day)
        elif r < 0.0055:  # refunded AFTER the cut-off; the bank had already settled the full amount
            ref = a if rng.random() < 0.5 else a // 2
            ledger_row(pid, m, "refund", ref, ts(day, rng, 18, 24))
            settle_row(pid, m, a, day)
        else:
            settle_row(pid, m, a, day)
    # Captured after the cut-off: ours today, the bank's tomorrow.
    for _ in range(1200):
        pid, m, a = pay_id(), rng.choice(merchants), rng.choice(amounts) + rng.randint(0, 99)
        ledger_row(pid, m, "capture", a, ts(day, rng, 18, 24))
    # Yesterday's post-cut-off captures: the bank settles them today; our ledger for today has no row.
    for _ in range(900):
        pid, m, a = pay_id(), rng.choice(merchants), rng.choice(amounts) + rng.randint(0, 99)
        settle_row(pid, m, a, prev)
    rng.shuffle(ledger)
    rng.shuffle(settle)
    ledger.sort(key=lambda r: r[6])
    write_csv(os.path.join(d, "ledger_2025-09-15.csv"),
              ["entry_id", "payment_id", "merchant_id", "entry_type", "amount_paise", "currency", "entry_ts",
               "method"], ledger)
    write_csv(os.path.join(d, "settlement_2025-09-15.csv"),
              ["utr", "payment_id", "merchant_id", "gross_amount", "fee", "tax", "net_amount", "captured_on",
               "settled_on", "remarks"], settle)


GENERATORS = {"bigbasket": gen_bigbasket, "swiggy": gen_swiggy, "myntra": gen_myntra, "razorpay": gen_razorpay}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in GENERATORS:
        print(f"usage: python3 generate_data.py <{'|'.join(GENERATORS)}>")
        sys.exit(1)
    brief = sys.argv[1]
    print(f"Generating data for {brief} into data/{brief}/")
    GENERATORS[brief](random.Random(20250922))
    print("Done. Next: make build")
