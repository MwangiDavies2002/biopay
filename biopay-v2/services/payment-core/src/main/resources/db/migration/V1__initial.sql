CREATE TABLE app_user (
  id VARCHAR(64) PRIMARY KEY,
  display_name VARCHAR(120) NOT NULL,
  status VARCHAR(32) NOT NULL,
  created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
);

CREATE TABLE merchant (
  id VARCHAR(64) PRIMARY KEY,
  name VARCHAR(160) NOT NULL,
  status VARCHAR(32) NOT NULL,
  created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
);

CREATE TABLE wallet (
  id VARCHAR(64) PRIMARY KEY,
  owner_type VARCHAR(24) NOT NULL,
  owner_id VARCHAR(64) NOT NULL,
  currency CHAR(3) NOT NULL,
  balance DECIMAL(19,4) NOT NULL DEFAULT 0,
  version BIGINT NOT NULL DEFAULT 0,
  created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  UNIQUE KEY uk_wallet_owner_currency (owner_type, owner_id, currency)
);

CREATE TABLE registered_device (
  id VARCHAR(64) PRIMARY KEY,
  user_id VARCHAR(64) NOT NULL,
  credential_id VARCHAR(255),
  public_key_pem TEXT,
  status VARCHAR(32) NOT NULL,
  created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  CONSTRAINT fk_device_user FOREIGN KEY (user_id) REFERENCES app_user(id)
);

CREATE TABLE payment_request (
  id VARCHAR(64) PRIMARY KEY,
  payer_user_id VARCHAR(64) NOT NULL,
  merchant_id VARCHAR(64) NOT NULL,
  amount DECIMAL(19,4) NOT NULL,
  currency CHAR(3) NOT NULL,
  status VARCHAR(32) NOT NULL,
  nonce_hash VARCHAR(128) NOT NULL,
  expires_at TIMESTAMP(6) NOT NULL,
  approved_at TIMESTAMP(6) NULL,
  created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  CONSTRAINT fk_payment_user FOREIGN KEY (payer_user_id) REFERENCES app_user(id),
  CONSTRAINT fk_payment_merchant FOREIGN KEY (merchant_id) REFERENCES merchant(id)
);

CREATE TABLE payment_transaction (
  id VARCHAR(64) PRIMARY KEY,
  payment_request_id VARCHAR(64) NOT NULL UNIQUE,
  status VARCHAR(32) NOT NULL,
  risk_score DECIMAL(8,6) NOT NULL,
  created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  CONSTRAINT fk_tx_payment FOREIGN KEY (payment_request_id) REFERENCES payment_request(id)
);

CREATE TABLE ledger_entry (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  transaction_id VARCHAR(64) NOT NULL,
  wallet_id VARCHAR(64) NOT NULL,
  direction VARCHAR(8) NOT NULL,
  amount DECIMAL(19,4) NOT NULL,
  currency CHAR(3) NOT NULL,
  created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  CONSTRAINT fk_ledger_tx FOREIGN KEY (transaction_id) REFERENCES payment_transaction(id),
  CONSTRAINT fk_ledger_wallet FOREIGN KEY (wallet_id) REFERENCES wallet(id),
  INDEX idx_ledger_tx (transaction_id),
  INDEX idx_ledger_wallet (wallet_id)
);

INSERT INTO app_user(id, display_name, status) VALUES ('USER-DEMO-001', 'Demo Customer', 'ACTIVE');
INSERT INTO merchant(id, name, status) VALUES ('MERCHANT-DEMO-001', 'Demo Merchant', 'ACTIVE');
INSERT INTO wallet(id, owner_type, owner_id, currency, balance) VALUES
('WALLET-USER-DEMO-001', 'USER', 'USER-DEMO-001', 'KES', 100000.0000),
('WALLET-MERCHANT-DEMO-001', 'MERCHANT', 'MERCHANT-DEMO-001', 'KES', 0.0000);
INSERT INTO registered_device(id, user_id, credential_id, status) VALUES
('DEVICE-DEMO-001', 'USER-DEMO-001', 'demo-passkey-credential', 'ACTIVE');
