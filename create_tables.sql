CREATE TABLE IF NOT EXISTS shops (
    shop_id INTEGER PRIMARY KEY ,
    shop_name VARCHAR(30) NOT NULL
);

CREATE TABLE IF NOT EXISTS cashes (
    cash_id INTEGER NOT NULL,
    shop_id INTEGER NOT NULL,
    PRIMARY KEY (shop_id, cash_id),
    FOREIGN KEY (shop_id) REFERENCES shops(shop_id)
);

CREATE TABLE IF NOT EXISTS receipts (
    doc_id UUID PRIMARY KEY,
    shop_id INTEGER NOT NULL ,
    cash_id INTEGER NOT NULL ,
    receipt_date TIMESTAMP NOT NULL,
    FOREIGN KEY (shop_id, cash_id) REFERENCES cashes(shop_id, cash_id),
    payment_type VARCHAR(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS receipts_items (
    --id SERIAL PRIMARY KEY,
    doc_id UUID NOT NULL ,
    category VARCHAR(50) NOT NULL,
    item VARCHAR(100) NOT NULL,
    amount INTEGER NOT NULL CHECK (amount > 0),
    price DECIMAL(10, 2) NOT NULL,
    discount DECIMAL(10, 2) DEFAULT 0,
    total DECIMAL(10, 2),
    FOREIGN KEY (doc_id) REFERENCES receipts(doc_id)
);

CREATE TABLE IF NOT EXISTS sales (
    doc_id UUID NOT NULL,
    item VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    amount INTEGER NOT NULL CHECK (amount > 0),
    price DECIMAL(10, 2) NOT NULL,
    discount DECIMAL(10, 2) DEFAULT 0
    --CONSTRAINT  sales_unique
    --UNIQUE(doc_id, item)
);

CREATE INDEX idx_receipts_date ON receipts(receipt_date);
CREATE INDEX idx_receipts_shop ON receipts(shop_id);
CREATE INDEX idx_receipts_items_doc_id ON receipts_items(doc_id);

