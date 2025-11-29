-- SQLite Schema for REWE Receipt Analyzer
-- Adapted from PostgreSQL schema for SQLite compatibility

-- Main receipts table
CREATE TABLE IF NOT EXISTS receipts (
    receipt_id INTEGER PRIMARY KEY AUTOINCREMENT,
    bon_nummer VARCHAR(20) NOT NULL,
    markt_nummer VARCHAR(10) NOT NULL,
    kasse_nummer VARCHAR(10),
    bediener VARCHAR(20),

    -- Zeitstempel
    kaufdatum DATE NOT NULL,
    kaufzeit TIME NOT NULL,
    tse_start TIMESTAMP,
    tse_stop TIMESTAMP,

    -- Standort
    markt_name VARCHAR(200),
    markt_adresse VARCHAR(200),
    markt_plz VARCHAR(10),
    markt_ort VARCHAR(100),
    uid_nummer VARCHAR(50),

    -- Summen
    summe_brutto DECIMAL(10,2) NOT NULL,
    summe_netto DECIMAL(10,2),
    summe_steuer DECIMAL(10,2),

    -- Zahlungsdetails
    zahlungsart VARCHAR(50), -- z.B. 'VISA', 'BAR', 'Bonus-Guthaben'
    gezahlt_betrag DECIMAL(10,2),
    rueckgeld DECIMAL(10,2),

    -- REWE Bonus
    bonus_eingesetzt DECIMAL(10,2),
    bonus_gesammelt DECIMAL(10,2),
    bonus_guthaben_aktuell DECIMAL(10,2),

    -- Metadaten
    tse_signatur TEXT,
    tse_signaturzaehler BIGINT,
    tse_transaktion BIGINT,
    seriennummer_kasse VARCHAR(50),

    -- Verarbeitung
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    email_id INTEGER,
    pdf_dateiname VARCHAR(255),

    UNIQUE(markt_nummer, kasse_nummer, bon_nummer, kaufdatum)
);

-- Receipt items table
CREATE TABLE IF NOT EXISTS receipt_items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_id INTEGER NOT NULL,

    -- Produktinformationen
    artikel_name VARCHAR(200) NOT NULL,
    artikel_typ VARCHAR(50), -- 'PRODUKT', 'PFAND', 'LEERGUT', 'KORREKTUR'

    -- Preisinformationen
    einzelpreis DECIMAL(10,2),
    menge INTEGER DEFAULT 1,
    einheit VARCHAR(20), -- 'Stk', 'kg', etc.
    gewicht DECIMAL(10,3), -- für Frischetheke
    preis_pro_einheit DECIMAL(10,2), -- EUR/kg
    gesamt_preis DECIMAL(10,2) NOT NULL,

    -- Steuer
    steuersatz VARCHAR(10), -- 'A' (19%), 'B' (7%), etc.
    steuersatz_prozent DECIMAL(5,2),

    -- Flags
    ist_pfand BOOLEAN DEFAULT 0,
    ist_leergut BOOLEAN DEFAULT 0,
    ist_rabatt BOOLEAN DEFAULT 0,
    ist_bedienungstheke BOOLEAN DEFAULT 0,
    kein_bonus BOOLEAN DEFAULT 0, -- Items mit *

    -- Bonus-Details
    bonus_aktion VARCHAR(200),
    bonus_betrag DECIMAL(10,2),

    -- Position auf Beleg
    position_nr INTEGER,

    -- Metadaten
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (receipt_id) REFERENCES receipts(receipt_id) ON DELETE CASCADE
);

-- Tax summary table
CREATE TABLE IF NOT EXISTS tax_summary (
    tax_id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_id INTEGER NOT NULL,

    steuersatz_key VARCHAR(10), -- 'A', 'B', etc.
    steuersatz_prozent DECIMAL(5,2),
    netto_betrag DECIMAL(10,2),
    steuer_betrag DECIMAL(10,2),
    brutto_betrag DECIMAL(10,2),

    FOREIGN KEY (receipt_id) REFERENCES receipts(receipt_id) ON DELETE CASCADE,
    UNIQUE(receipt_id, steuersatz_key)
);

-- Markets table
CREATE TABLE IF NOT EXISTS markets (
    market_id INTEGER PRIMARY KEY AUTOINCREMENT,
    markt_nummer VARCHAR(10) UNIQUE NOT NULL,
    markt_name VARCHAR(200),
    strasse VARCHAR(200),
    plz VARCHAR(10),
    ort VARCHAR(100),
    telefon VARCHAR(50),
    uid_nummer VARCHAR(50),

    -- Koordinaten für spätere Analysen
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),

    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    aktualisiert_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products catalog table
CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    artikel_name VARCHAR(200) UNIQUE NOT NULL,
    kategorie VARCHAR(100),
    unterkategorie VARCHAR(100),
    marke VARCHAR(100),
    ist_bio BOOLEAN DEFAULT 0,
    standard_steuersatz VARCHAR(10),

    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better query performance

-- Zeitbasierte Abfragen
CREATE INDEX IF NOT EXISTS idx_receipts_kaufdatum ON receipts(kaufdatum);
CREATE INDEX IF NOT EXISTS idx_receipts_markt ON receipts(markt_nummer);
CREATE INDEX IF NOT EXISTS idx_receipts_datetime ON receipts(kaufdatum, kaufzeit);

-- Artikelsuche
CREATE INDEX IF NOT EXISTS idx_items_artikel ON receipt_items(artikel_name);
CREATE INDEX IF NOT EXISTS idx_items_receipt ON receipt_items(receipt_id);
CREATE INDEX IF NOT EXISTS idx_items_typ ON receipt_items(artikel_typ);

-- Markt-Lookup
CREATE INDEX IF NOT EXISTS idx_markets_nummer ON markets(markt_nummer);

-- Produkt-Suche
CREATE INDEX IF NOT EXISTS idx_products_name ON products(artikel_name);
