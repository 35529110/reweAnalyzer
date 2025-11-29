import re

class Item:
    def __init__(self, name: str, price_per_unit: float= 0.0, quantity: float = 1.0, total: float=0.0):
        """
        Initialize a receipt item.
        
        Args:
            name: Product name
            price_per_unit: Price per single unit
            quantity: Number of units (default: 1)
            discount: Discount amount in EUR (default: 0.0)
        """
        self.name = name
        self.price_per_unit = price_per_unit
        self.quantity = quantity
        self.total = total
        
    def add_updating_second_line(self, line: str):
        (count_string,price_string) = line.strip().split("Stk x")
        count_string=count_string.strip()
        quantity = float(count_string)
        price_string=price_string.strip().replace(',','.')
        self.price_per_unit=float(price_string)
        
        # verify 
        if quantity * self.price_per_unit != self.total:
            print("Inconsistency with item {name}")
            print('quantity {quantity} and price per unit {price_per_unit} dont equal total {total}')
    
    def get_calculated_total(self) -> float:
        """Calculate total based on quantity and price per unit."""
        return self.quantity * self.price_per_unit
    
    def __repr__(self) -> str:
        return f"Item('{self.name}', {self.quantity}x {self.price_per_unit:.2f}€ = {self.total:.2f}€)"
    
class Receipt:
    def __init__(self,
                 store_name: str = "",
                 address: str = "",
                 city: str = "",
                 uid_nr: str = "",
                 items: list[Item] = None,
                 total_amount: float = 0.0,
                 change: float = 0.0,
                 payment_methode: str = "",
                 taxes: float = 0.0,
                 date: str = "",
                 time: str = "",
                 bon_nr: str = "",
                 amount_given: float = 0.0
                 ):
        """
        Initialize a receipt.

        Args:
            store_name: Name of the REWE store
            address: Store address
            city: City name
            uid_nr: UID number of the store
            items: List of Item objects
            total_amount: Total amount on the receipt
            change: Change returned to customer
            payment_methode: Payment method (e.g., BAR, EC-KARTE)
            taxes: Total tax amount
            date: Receipt date (DD.MM.YYYY)
            time: Receipt time (HH:MM)
            bon_nr: Receipt/Bon number
            amount_given: Amount given by customer
        """
        self.store_name = store_name
        self.address = address
        self.city = city
        self.uid_nr = uid_nr
        self.items = items if items is not None else []
        self.total_amount = total_amount
        self.change = change
        self.payment_methode = payment_methode
        self.taxes = taxes
        self.date = date
        self.time = time
        self.bon_nr = bon_nr
        self.amount_given = amount_given

    def get_calculated_total(self) -> float:
        """Calculate the sum of all item totals."""
        return sum(item.total for item in self.items)

    def validate_total(self) -> tuple[bool, float]:
        """
        Validate that the total_amount matches the sum of all items.

        Returns:
            tuple: (is_valid, difference) where difference = total_amount - calculated_total
        """
        calculated = self.get_calculated_total()
        difference = round(self.total_amount - calculated, 2)
        is_valid = abs(difference) < 0.01  # Allow for small floating point errors
        return is_valid, difference

    def __repr__(self) -> str:
        is_valid, diff = self.validate_total()
        validation_status = "✓" if is_valid else f"✗ (diff: {diff:.2f}€)"

        lines = []
        lines.append("=" * 60)
        lines.append(f"RECEIPT - {self.store_name}")
        lines.append("=" * 60)
        lines.append(f"Address:        {self.address}")
        lines.append(f"City:           {self.city}")
        lines.append(f"UID Nr:         {self.uid_nr}")
        lines.append(f"Date:           {self.date} {self.time}")
        lines.append(f"Bon Nr:         {self.bon_nr}")
        lines.append("-" * 60)
        lines.append("ITEMS:")
        lines.append("-" * 60)

        for item in self.items:
            if item.quantity == 1.0:
                lines.append(f"  {item.name:40s} {item.total:>6.2f}€")
            else:
                lines.append(f"  {item.name:40s} {item.total:>6.2f}€")
                lines.append(f"    ({item.quantity:.0f} x {item.price_per_unit:.2f}€)")

        lines.append("-" * 60)
        lines.append(f"TOTAL:          {self.total_amount:>6.2f}€ {validation_status}")
        lines.append(f"Payment:        {self.payment_methode:>6s} {self.amount_given:>6.2f}€")
        if self.change > 0:
            lines.append(f"Change:         {self.change:>13.2f}€")
        lines.append(f"Taxes:          {self.taxes:>13.2f}€")
        lines.append("=" * 60)

        return "\n".join(lines)

    @classmethod
    def from_text(cls, text: str) -> 'Receipt':
        """
        Parse a REWE receipt from text and return a Receipt object.

        Args:
            text: The receipt text content

        Returns:
            Receipt object with parsed data
        """
        lines = text.split('\n')

        # Skip page markers and empty lines, get first non-empty lines
        non_empty_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('---'):
                non_empty_lines.append(stripped)

        # Parse header (first 3-4 lines)
        store_name = non_empty_lines[0] if len(non_empty_lines) > 0 else ""
        address_line1 = non_empty_lines[1] if len(non_empty_lines) > 1 else ""
        address_line2 = non_empty_lines[2] if len(non_empty_lines) > 2 else ""
        address = address_line1

        # Extract city from address line (format: "postal_code city")
        city_match = re.search(r'(\d{5})\s+(.+)', address_line2)
        city = city_match.group(2).strip() if city_match else ""

        # Parse UID
        uid_match = re.search(r'UID Nr\.: (DE\d+)', text)
        uid_nr = uid_match.group(1) if uid_match else ""

        # Parse items (lines with product name, price, and tax category)
        items = []
        item_pattern = r'^(.+?)\s+(\d+,\d{2})\s+[A-B](?:\s+\*)?$'
        quantity_pattern = r'^\s*(\d+)\s+Stk\s+x\s+(\d+,\d{2})$'

        i = 0
        while i < len(non_empty_lines):
            line = non_empty_lines[i]
            match = re.match(item_pattern, line)
            if match:
                name = match.group(1).strip()
                total = float(match.group(2).replace(',', '.'))

                # Check if next line has quantity info
                if i + 1 < len(non_empty_lines):
                    next_line = non_empty_lines[i + 1]
                    qty_match = re.match(quantity_pattern, next_line)
                    if qty_match:
                        quantity = float(qty_match.group(1))
                        price_per_unit = float(qty_match.group(2).replace(',', '.'))
                        items.append(Item(name=name, quantity=quantity, price_per_unit=price_per_unit, total=total))
                        i += 2  # Skip the next line since we processed it
                        continue

                # No quantity line, default to quantity=1
                items.append(Item(name=name, quantity=1.0, price_per_unit=total, total=total))
            i += 1

        # Parse total amount
        total_match = re.search(r'SUMME\s+EUR\s+(\d+,\d{2})', text)
        total_amount = float(total_match.group(1).replace(',', '.')) if total_match else 0.0

        # Parse payment method and amount given
        payment_match = re.search(r'Geg\. (BAR|EC-KARTE|KARTE)\s+EUR\s+(\d+,\d{2})', text)
        payment_methode = payment_match.group(1) if payment_match else ""
        amount_given = float(payment_match.group(2).replace(',', '.')) if payment_match else 0.0

        # Parse change
        change_match = re.search(r'Rückgeld (?:BAR|EC-KARTE|KARTE)?\s+EUR\s+(\d+,\d{2})', text)
        change = float(change_match.group(1).replace(',', '.')) if change_match else 0.0

        # Parse taxes
        tax_match = re.search(r'Gesamtbetrag\s+[\d,]+\s+([\d,]+)\s+[\d,]+', text)
        taxes = float(tax_match.group(1).replace(',', '.')) if tax_match else 0.0

        # Parse date, time, and bon number
        date_time_match = re.search(r'(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})\s+Bon-Nr\.:(\d+)', text)
        date = date_time_match.group(1) if date_time_match else ""
        time = date_time_match.group(2) if date_time_match else ""
        bon_nr = date_time_match.group(3) if date_time_match else ""

        return cls(
            store_name=store_name,
            address=address,
            city=city,
            uid_nr=uid_nr,
            items=items,
            total_amount=total_amount,
            change=change,
            payment_methode=payment_methode,
            taxes=taxes,
            date=date,
            time=time,
            bon_nr=bon_nr,
            amount_given=amount_given
        )
